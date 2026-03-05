import csv
import json
import os
import re
import imaplib
from datetime import datetime
from email import message_from_bytes
from email.header import decode_header
from pathlib import Path

BASE = Path(r"C:\Users\User\Documents\Openclaw")
DATA = BASE / "data"
MEM = BASE / "memory"
DATA.mkdir(exist_ok=True)
MEM.mkdir(exist_ok=True)

LATEST_PATH = MEM / "booking_intent_latest.json"
QUEUE_PATH = DATA / "booking_intent_queue.csv"
STATE_PATH = MEM / "booking_intent_state.json"

HOT_TOKENS = [
    "book", "booking", "availability", "available", "this week", "today", "tomorrow",
    "need mixing", "need mastering", "recording", "studio time", "session",
    "how much", "price", "quote", "ready to start", "call me", "phone"
]
WARM_TOKENS = [
    "interested", "maybe", "could", "thinking about", "next month", "question",
    "rates", "mix", "master", "vocal", "project", "ep", "single"
]

SERVICE_HINTS = {
    "recording": ["record", "recording", "vocals", "session"],
    "mixing": ["mix", "mixing", "stems"],
    "mastering": ["master", "mastering"],
    "date_night": ["date night", "experience", "birthday", "group", "things to do"],
}


def decode_text(value):
    if not value:
        return ""
    parts = decode_header(value)
    output = []
    for text, enc in parts:
        if isinstance(text, bytes):
            output.append(text.decode(enc or "utf-8", errors="ignore"))
        else:
            output.append(text)
    return " ".join(output).strip()


def extract_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            dispo = str(part.get("Content-Disposition") or "")
            if ctype == "text/plain" and "attachment" not in dispo.lower():
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode(part.get_content_charset() or "utf-8", errors="ignore")
        return ""
    payload = msg.get_payload(decode=True)
    if payload:
        return payload.decode(msg.get_content_charset() or "utf-8", errors="ignore")
    return ""


def classify(text):
    t = text.lower()
    hot_score = sum(1 for tok in HOT_TOKENS if tok in t)
    warm_score = sum(1 for tok in WARM_TOKENS if tok in t)

    if hot_score >= 2:
        intent = "hot"
        urgency = "high"
    elif hot_score == 1 or warm_score >= 2:
        intent = "warm"
        urgency = "medium"
    else:
        intent = "nurture"
        urgency = "low"

    service = "general"
    for k, tokens in SERVICE_HINTS.items():
        if any(tok in t for tok in tokens):
            service = k
            break

    return intent, urgency, hot_score, warm_score, service


def ensure_files():
    if not QUEUE_PATH.exists():
        with QUEUE_PATH.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([
                "date", "message_id", "from", "subject", "intent", "urgency", "service_fit", "recommended_next_action", "status"
            ])


def load_seen_ids():
    if not STATE_PATH.exists():
        return set()
    try:
        raw = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        return set(raw.get("seen_message_ids", []))
    except Exception:
        return set()


def save_seen_ids(ids):
    STATE_PATH.write_text(json.dumps({"seen_message_ids": sorted(list(ids))[-1000:]}, indent=2), encoding="utf-8")


def next_action(intent, service):
    if intent == "hot":
        return f"Reply within 15m with {service} availability + phone CTA"
    if intent == "warm":
        return f"Reply within 2h with short {service} option + one clear next step"
    return "Add to nurture and follow up in 48h"


def main():
    ensure_files()
    seen_ids = load_seen_ids()

    user = os.getenv("GMAIL_USER")
    pwd = os.getenv("GMAIL_PASS")
    if not user or not pwd:
        out = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "status": "blocked",
            "error": "missing_gmail_credentials",
            "checked": 0,
            "new": 0,
            "hot": 0,
            "warm": 0,
            "nurture": 0,
        }
        LATEST_PATH.write_text(json.dumps(out, indent=2), encoding="utf-8")
        print("[Booking Intent Watcher | status:blocked | reason:missing_gmail_credentials]")
        return

    checked = 0
    new_count = 0
    hot = 0
    warm = 0
    nurture = 0

    with imaplib.IMAP4_SSL("imap.gmail.com") as imap:
        imap.login(user, pwd)
        imap.select("INBOX")
        typ, data = imap.search(None, "UNSEEN")
        ids = data[0].split()[-40:]

        rows_to_add = []
        for mid in ids:
            msg_id = mid.decode()
            checked += 1
            if msg_id in seen_ids:
                continue

            typ, msg_data = imap.fetch(mid, "(RFC822)")
            if typ != "OK" or not msg_data or not msg_data[0]:
                continue

            raw_email = msg_data[0][1]
            msg = message_from_bytes(raw_email)

            sender = decode_text(msg.get("From", ""))
            subject = decode_text(msg.get("Subject", ""))
            body = extract_body(msg)
            text = f"{subject}\n{body[:2000]}"

            intent, urgency, hot_score, warm_score, service = classify(text)

            if intent == "hot":
                hot += 1
            elif intent == "warm":
                warm += 1
            else:
                nurture += 1

            rows_to_add.append([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                msg_id,
                re.sub(r"\s+", " ", sender)[:240],
                re.sub(r"\s+", " ", subject)[:240],
                intent,
                urgency,
                service,
                next_action(intent, service),
                "new",
            ])

            seen_ids.add(msg_id)
            new_count += 1

        if rows_to_add:
            with QUEUE_PATH.open("a", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerows(rows_to_add)

        imap.close()
        imap.logout()

    save_seen_ids(seen_ids)

    # collect top hot leads from this run for optional immediate alerts
    hot_leads = []
    if rows_to_add:
        for row in rows_to_add:
            if row[4] == "hot":
                hot_leads.append({
                    "message_id": row[1],
                    "from": row[2],
                    "subject": row[3],
                    "service_fit": row[6],
                    "next_action": row[7],
                })

    latest = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "status": "ok",
        "checked": checked,
        "new": new_count,
        "hot": hot,
        "warm": warm,
        "nurture": nurture,
        "hot_leads": hot_leads[:5],
        "queue_file": str(QUEUE_PATH),
    }
    LATEST_PATH.write_text(json.dumps(latest, indent=2), encoding="utf-8")
    print(f"[Booking Intent Watcher {latest['date']} | checked:{checked} | new:{new_count} | hot:{hot} warm:{warm} nurture:{nurture}]")


if __name__ == "__main__":
    main()
