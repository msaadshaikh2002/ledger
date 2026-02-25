import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os
import json

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_sheet():
    creds_json = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
    creds = Credentials.from_service_account_info(creds_json, scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open("Money Ledger").worksheet("Transactions")
    return sheet


def add_transaction(tx_type, person, amount, notes=""):
    sheet = get_sheet()

    now = datetime.now()

    date_str = now.strftime("%d %b %Y")     # 25 Feb 2026
    time_str = now.strftime("%I:%M %p")     # 11:46 AM (12-hour)

    row = [
        date_str,
        time_str,
        tx_type,
        person,
        amount,
        notes
    ]

    sheet.append_row(row)

def get_all_transactions():
    sheet = get_sheet()
    return sheet.get_all_records()


def calculate_balances():
    records = get_all_transactions()
    balances = {}

    for row in records:
        try:
            person = row.get("Person", "").strip()
            tx_type = row.get("Type", "").strip()
            amount = int(row.get("Amount", 0))

            if not person:
                continue

            if person not in balances:
                balances[person] = 0

            if tx_type == "GAVE":
                balances[person] += amount
            elif tx_type == "RETURNED":
                balances[person] -= amount
            elif tx_type == "BORROWED":
                balances[person] -= amount
            elif tx_type == "REPAID":
                balances[person] += amount

        except Exception as e:
            print("Balance calculation error:", e)
            continue

    return balances


