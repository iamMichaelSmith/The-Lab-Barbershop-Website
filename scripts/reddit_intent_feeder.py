import csv
import json
from datetime import datetime
from pathlib import Path

BASE = Path(r"C:\Users\User\Documents\Openclaw")
DATA = BASE / "data"
MEM = BASE / "memory"

SRC = MEM / "reddit_daily5_latest.json"
QUEUE = DATA / "booking_intent_queue.csv"
STATE = MEM / "reddit_intent_feeder_state.json"
LATEST = MEM / "reddit_intent_feeder_latest.json"


def ensure_queue():
    if not QUEUE.exists():
        with QUEUE.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([
                "date", "message_id", "from", "subject", "intent", "urgency", "service_fit", "recommended_next_action", "status"
            ])


def load_state():
    if not STATE.exists():
        return {"seen_urls": []}
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        return {"seen_urls": []}


def save_state(state):
    STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def classify(score):
    if score >= 60:
        return "hot", "high"
    if score >= 50:
        return "warm", "medium"
    return "nurture", "low"


def service_fit(title):
    t = (title or "").lower()
    if "master" in t:
        return "mastering"
    if "mix" in t:
        return "mixing"
    if "record" in t or "studio" in t:
        return "recording"
    return "mixing"


def main():
    ensure_queue()
    state = load_state()
    seen = set(state.get("seen_urls", []))

    if not SRC.exists():
        out = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "status": "blocked",
            "reason": "missing_reddit_daily5_latest",
            "new": 0,
            "hot": 0,
            "warm": 0,
            "nurture": 0,
        }
        LATEST.write_text(json.dumps(out, indent=2), encoding="utf-8")
        print("[Reddit Intent Feeder | status:blocked | reason:missing_reddit_daily5_latest]")
        return

    src = json.loads(SRC.read_text(encoding="utf-8"))
    entries = src.get("entries", []) if isinstance(src, dict) else []

    rows = []
    hot = warm = nurture = 0

    for e in entries:
        url = (e.get("url") or "").strip()
        if not url or url in seen:
            continue

        score = int(e.get("score", 0) or 0)
        intent, urgency = classify(score)
        fit = service_fit(e.get("title", ""))

        if intent == "hot":
            hot += 1
        elif intent == "warm":
            warm += 1
        else:
            nurture += 1

        title = (e.get("title") or "")[:240]
        subreddit = (e.get("subreddit") or "reddit")

        rows.append([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            f"reddit:{abs(hash(url))}",
            f"reddit/{subreddit}",
            title,
            intent,
            urgency,
            fit,
            f"Open thread search, find live poster, send value-first {fit} offer",
            "new",
        ])

        seen.add(url)

    if rows:
        with QUEUE.open("a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerows(rows)

    state["seen_urls"] = list(seen)[-2000:]
    save_state(state)

    out = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "status": "ok",
        "new": len(rows),
        "hot": hot,
        "warm": warm,
        "nurture": nurture,
        "source": str(SRC),
    }
    LATEST.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"[Reddit Intent Feeder {out['date']} | new:{len(rows)} | hot:{hot} warm:{warm} nurture:{nurture}]")


if __name__ == "__main__":
    main()
