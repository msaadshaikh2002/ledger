import re

TYPE_KEYWORDS = {
    "gave": "GAVE",
    "diya": "GAVE",
    "de diya": "GAVE",

    "liya": "BORROWED",
    "took": "BORROWED",
    "se liya": "BORROWED",

    "wapas": "RETURNED",
    "returned": "RETURNED",
    "lota diya": "RETURNED",

    "repay": "REPAID",
    "chuka diya": "REPAID"
}

def normalize_name(name):
    return name.strip().title()

def detect_type(text):
    text_lower = text.lower()
    for keyword in sorted(TYPE_KEYWORDS, key=len, reverse=True):
        if keyword in text_lower:
            return TYPE_KEYWORDS[keyword]
    return "UNKNOWN"


def extract_amount(text):
    text = text.replace(",", "")
    match = re.search(r"(₹?\s?\d+)", text)
    if match:
        amount = re.sub(r"[^\d]", "", match.group())
        return int(amount)
    return 0


def extract_person(text):
    words = text.split()

    for i, word in enumerate(words):
        if word.lower() in ["ko", "ne", "se"]:
            if i > 0:
                return normalize_name(words[i - 1])

    # fallback: first capitalized word
    for word in words:
        if word[0].isupper() and not word.isdigit():
            return normalize_name(word)

    return "Unknown"


def parse_message(text):
    tx_type = detect_type(text)
    person = extract_person(text)
    amount = extract_amount(text)
    notes = extract_notes(text)

    if amount == 0:
        return {"error": "Amount not detected"}

    if tx_type == "UNKNOWN":
        return {"error": "Transaction type not detected"}

    # 🔎 NEW VALIDATION
    if person == "Unknown" or person.isdigit():
        return {"error": "Person not detected"}

    return {
        "type": tx_type,
        "person": person,
        "amount": amount,
        "notes": notes
    }

def extract_notes(text):
    text_lower = text.lower()

    # Find transaction keyword position
    for keyword in TYPE_KEYWORDS:
        if keyword in text_lower:
            start_index = text_lower.find(keyword)
            end_index = start_index + len(keyword)

            # Notes = everything after keyword
            notes = text[end_index:].strip()
            return notes

    return ""