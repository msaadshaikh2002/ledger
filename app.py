import os
import requests
from fastapi import FastAPI, Request
from dotenv import load_dotenv
from parser import parse_message
from sheets import add_transaction

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = FastAPI()


@app.get("/")
def home():
    return {"status": "Bot is running 🚀"}


def send_message(chat_id, text):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }

    response = requests.post(url, json=payload)
    print("Telegram response:", response.status_code, response.text)


@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    print("Incoming data:", data)

    if "message" not in data or "text" not in data["message"]:
        return {"ok": True}

    chat_id = data["message"]["chat"]["id"]
    text = data["message"]["text"].strip()

    # =============================
    # 📊 SUMMARY COMMAND
    # =============================
    if text.startswith("/summary"):
        from sheets import calculate_balances
        balances = calculate_balances()

        if not balances:
            reply_text = "No transactions yet."
        else:
            reply_text = "📊 Ledger Summary:\n\n"
            for person, balance in balances.items():
                if balance > 0:
                    reply_text += f"{person} owes you ₹{balance}\n"
                elif balance < 0:
                    reply_text += f"You owe {person} ₹{abs(balance)}\n"
                else:
                    reply_text += f"{person}: Settled ✅\n"

        send_message(chat_id, reply_text)
        return {"ok": True}

    # =============================
    # 📜 LEDGER COMMAND
    # =============================
    if text.startswith("/ledger"):
        from sheets import get_all_transactions
        records = get_all_transactions()

        parts = text.split()
        if len(parts) < 2:
            send_message(chat_id, "Usage: /ledger Aadil")
            return {"ok": True}

        target = parts[1].title()
        reply_text = f"📜 Ledger for {target}:\n\n"

        found = False
        balance = 0

        for row in records:
            if row["Person"].lower() == target.lower():
                found = True

                tx_type = row["Type"]
                amount = int(row["Amount"])

                reply_text += (
                    f"{row['Date']} {row['Time']} | "
                    f"{tx_type} | "
                    f"₹{amount}\n"
                )

                # Balance logic
                if tx_type == "GAVE":
                    balance += amount
                elif tx_type == "RETURNED":
                    balance -= amount
                elif tx_type == "BORROWED":
                    balance -= amount
                elif tx_type == "REPAID":
                    balance += amount

        if not found:
            reply_text += "No transactions found."
        else:
            reply_text += "\n-----------------\n"

            if balance > 0:
                reply_text += f"Total: {target} owes you ₹{balance}"
            elif balance < 0:
                reply_text += f"Total: You owe {target} ₹{abs(balance)}"
            else:
                reply_text += "Total: Settled ✅"

        send_message(chat_id, reply_text)
        return {"ok": True}

    # =============================
    # 💰 NORMAL TRANSACTION
    # =============================
    parsed = parse_message(text)
    print("Parsed:", parsed)

    if "error" in parsed:
        send_message(chat_id, f"❌ {parsed['error']}")
        return {"ok": True}

    try:
        add_transaction(
            parsed["type"],
            parsed["person"],
            parsed["amount"],
            parsed.get("notes", "")
        )

        reply_text = (
            f"✅ Recorded\n"
            f"Type: {parsed['type']}\n"
            f"Person: {parsed['person']}\n"
            f"Amount: ₹{parsed['amount']}\n"
            f"Notes: {parsed.get('notes', 'None')}"
        )

    except Exception as e:
        print("Sheets Error:", e)
        reply_text = "❌ Failed to record transaction"

    send_message(chat_id, reply_text)
    return {"ok": True}