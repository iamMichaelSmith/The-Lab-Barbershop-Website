import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(r"C:\Users\User\Documents\Openclaw")
DATA = BASE / "data"
MEM = BASE / "memory"
DATA.mkdir(exist_ok=True)
MEM.mkdir(exist_ok=True)

today = datetime.now().strftime("%Y-%m-%d")
state_path = MEM / "bluesky_lead_hunter_state.json"

CORE_QUERIES = [
    "producer beats",
    "new song out",
    "EP out now",
    "album out now",
    "mix feedback",
]

ROTATING_QUERIES = [
    "new single out",
    "need mixing",
    "need mastering",
    "mix engineer",
    "mastering engineer",
    "recording vocals",
    "in the studio",
    "just recorded this",
    "dropping this week",
    "presave",
]

EXPANDED_QUERIES = [
    "independent artist",
    "unsigned artist",
    "debut single",
    "working on my ep",
    "austin musician",
    "atx artist",
]

agg_tokens = ["newswire", "news", "updates", "mag", "daily", "blog", "repost bot", "promo page"]
music_tokens = ["artist", "rapper", "singer", "producer", "song", "single", "ep", "album", "track", "mix", "master", "studio", "beat", "vocals", "recording"]
genre_tokens = ["hip hop", "hip-hop", "rap", "r&b", "afrobeats", "alt-pop", "alternative", "melodic", "trap", "pop"]
geo_tokens = ["austin", "atx", "texas", "tx", "round rock", "pflugerville", "cedar park", "leander", "kyle", "buda", "san marcos"]
release_tokens = ["new song", "new single", "ep out", "album out", "out now", "dropping", "presave", "release", "just dropped"]
contact_tokens = ["booking", "inquiries", "email", "dm", "management", "contact"]
studio_tokens = ["studio", "recorded", "recording", "mix", "master", "session", "vocals", "engineer"]
link_tokens = ["spotify", "soundcloud", "bandcamp", "youtu", "linktr.ee", "beacons.ai", "audiomack", "music.apple"]


def load_state():
    if not state_path.exists():
        return {"rot_index": 0, "search_mode": "strict"}
    try:
        raw = json.loads(state_path.read_text(encoding="utf-8"))
    except Exception:
        return {"rot_index": 0, "search_mode": "strict"}
    return {
        "rot_index": int(raw.get("rot_index", 0)),
        "search_mode": raw.get("search_mode", "strict") if raw.get("search_mode") in ("strict", "expanded") else "strict",
    }


def save_state(state):
    state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def run_query(q):
    cmds = [
        ["bsky", "search", "--json", "-n", "40", q],
        ["python", "skills/bluesky/scripts/bsky.py", "search", "--json", "-n", "40", q],
    ]
    last_err = "cli_unavailable"
    for cmd in cmds:
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, cwd=str(BASE), timeout=75)
            if p.returncode != 0:
                last_err = (p.stderr or p.stdout or "cmd_failed").strip()[:120]
                continue
            if not p.stdout.strip():
                last_err = "empty_stdout"
                continue
            try:
                parsed = json.loads(p.stdout)
            except Exception:
                last_err = f"json_parse_failed:{cmd[0]}"
                continue
            return parsed if isinstance(parsed, list) else [], None
        except Exception as e:
            last_err = str(e)[:120]

    # one simple fallback query if phrase was too strict
    simple = " ".join(q.split()[:2]) if len(q.split()) > 2 else q
    if simple != q:
        try:
            p = subprocess.run(["python", "skills/bluesky/scripts/bsky.py", "search", "--json", "-n", "25", simple], capture_output=True, text=True, cwd=str(BASE), timeout=60)
            if p.returncode == 0 and p.stdout.strip():
                parsed = json.loads(p.stdout)
                return parsed if isinstance(parsed, list) else [], None
        except Exception:
            pass

    return [], last_err


def score_post(post):
    text = (post.get("text") or "").lower()
    handle = (post.get("author", {}).get("handle") or "").lower()
    profile = ((post.get("author", {}).get("displayName") or "") + " " + (post.get("author", {}).get("description") or "")).lower()

    if any(tok in handle for tok in agg_tokens):
        return None

    # hard disqualify if no music signal in post+profile
    if not any(tok in text or tok in profile for tok in music_tokens):
        return None

    score = 0
    if any(tok in text or tok in profile for tok in geo_tokens):
        score += 25
    if any(tok in text for tok in genre_tokens):
        score += 20
    if any(tok in text for tok in link_tokens):
        score += 15

    created = post.get("createdAt")
    if created:
        try:
            dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            age = (datetime.now(timezone.utc) - dt).days
            if age <= 7:
                score += 15
            elif age <= 30:
                score += 10
            elif age <= 60:
                score += 5
            else:
                return None
        except Exception:
            pass

    if any(tok in text for tok in release_tokens):
        score += 10
    if any(tok in text or tok in profile for tok in contact_tokens):
        score += 10
    if any(tok in text for tok in studio_tokens):
        score += 5

    if score >= 78:
        tier = "A"
    elif score >= 62:
        tier = "B"
    elif score >= 48:
        tier = "C"
    else:
        return None

    return score, tier


def build_queries(state):
    rot_index = state.get("rot_index", 0)
    rotating = [ROTATING_QUERIES[(rot_index + i) % len(ROTATING_QUERIES)] for i in range(4)]
    state["rot_index"] = (rot_index + 4) % len(ROTATING_QUERIES)

    queries = list(CORE_QUERIES) + rotating
    if state.get("search_mode") == "expanded":
        queries += EXPANDED_QUERIES
    return queries


def is_logged_in():
    checks = [
        ["bsky", "whoami"],
        ["python", "skills/bluesky/scripts/bsky.py", "whoami"],
    ]
    for cmd in checks:
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, cwd=str(BASE), timeout=20)
            out = (p.stdout or "") + "\n" + (p.stderr or "")
            if p.returncode == 0 and "not logged in" not in out.lower():
                return True
        except Exception:
            continue
    return False


state = load_state()
if not is_logged_in():
    latest = {
        "date": today,
        "checked": 0,
        "kept": 0,
        "A": 0,
        "B": 0,
        "C": 0,
        "queued_AB": 0,
        "top_query": "none",
        "mode": state.get("search_mode", "strict"),
        "blockers": ["not_logged_in"],
    }
    (MEM / "bluesky_lead_hunter_latest.json").write_text(json.dumps(latest, indent=2), encoding="utf-8")
    save_state(state)
    print(f"[Bluesky Qualified Leads {today} | checked:0 | kept:0 | A:0 B:0 C:0 | queued_AB:0 | top_query:none | blockers:short-list]")
    raise SystemExit(0)

queries = build_queries(state)

all_kept = []
blockers = []
checked = 0
seen_urls = set()
seen_hash = set()

for q in queries:
    items, err = run_query(q)
    if err:
        blockers.append(f"{q}:{err}")
        continue
    for p in items:
        checked += 1
        url = p.get("url") or p.get("uri")
        text = (p.get("text") or "").strip().lower()
        handle = (p.get("author", {}).get("handle") or "").strip().lower()
        dedupe_key = f"{handle}|{text[:120]}"
        if (url and url in seen_urls) or dedupe_key in seen_hash:
            continue

        s = score_post(p)
        if not s:
            continue
        score, tier = s
        if url:
            seen_urls.add(url)
        seen_hash.add(dedupe_key)
        all_kept.append({
            "handle": p.get("author", {}).get("handle", ""),
            "displayName": p.get("author", {}).get("displayName", ""),
            "postUrl": url or "",
            "postText": (p.get("text") or "")[:240],
            "leadScore": score,
            "tier": tier,
            "sourceQuery": q,
            "createdAt": p.get("createdAt", ""),
        })

# adaptive mode toggle
if len(all_kept) < 8 and state.get("search_mode") == "strict":
    state["search_mode"] = "expanded"
elif len(all_kept) >= 12 and state.get("search_mode") == "expanded":
    state["search_mode"] = "strict"

# write leads json
out_json = DATA / f"bluesky_leads_{today}.json"
out_json.write_text(json.dumps({
    "date": today,
    "checked": checked,
    "kept": len(all_kept),
    "mode": state.get("search_mode", "strict"),
    "blockers": blockers,
    "leads": all_kept,
}, indent=2), encoding="utf-8")

# queue/archive
queue = DATA / "client_leads_queue.csv"
archive = DATA / "client_leads_archive.csv"
fields = ["date_found","source","type","title","url","score","tier","budget_signal","contact_path","next_action","first_touch","status","owner","notes"]
for f in [queue, archive]:
    if not f.exists():
        with f.open("w", newline="", encoding="utf-8") as fh:
            csv.DictWriter(fh, fieldnames=fields).writeheader()

existing_urls = set()
with queue.open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        existing_urls.add((r.get("url") or "").strip())
with archive.open(encoding="utf-8", newline="") as fh:
    for r in csv.DictReader(fh):
        existing_urls.add((r.get("url") or "").strip())

queued_ab = 0
with queue.open("a", newline="", encoding="utf-8") as fq, archive.open("a", newline="", encoding="utf-8") as fa:
    wq = csv.DictWriter(fq, fieldnames=fields)
    wa = csv.DictWriter(fa, fieldnames=fields)
    for l in all_kept:
        row = {
            "date_found": today,
            "source": "Bluesky",
            "type": "ARTIST",
            "title": f"{l['displayName'] or l['handle']} - {l['sourceQuery']}",
            "url": l["postUrl"],
            "score": l["leadScore"],
            "tier": l["tier"],
            "budget_signal": "release_intent",
            "contact_path": "bluesky_profile",
            "next_action": "qualify_contact_and_prepare_outreach",
            "first_touch": "value_comment_then_dm_if_open",
            "status": "new",
            "owner": "studio-assistant",
            "notes": l["postText"],
        }
        if not row["url"]:
            continue
        is_new = row["url"] not in existing_urls
        if is_new:
            wa.writerow(row)
            existing_urls.add(row["url"])
        if l["tier"] in ("A", "B") and is_new:
            wq.writerow(row)
            queued_ab += 1

latest = {
    "date": today,
    "checked": checked,
    "kept": len(all_kept),
    "A": sum(1 for x in all_kept if x["tier"] == "A"),
    "B": sum(1 for x in all_kept if x["tier"] == "B"),
    "C": sum(1 for x in all_kept if x["tier"] == "C"),
    "queued_AB": queued_ab,
    "top_query": (all_kept[0]["sourceQuery"] if all_kept else "none"),
    "mode": state.get("search_mode", "strict"),
    "blockers": blockers,
}
(MEM / "bluesky_lead_hunter_latest.json").write_text(json.dumps(latest, indent=2), encoding="utf-8")
save_state(state)

print(f"[Bluesky Qualified Leads {today} | checked:{checked} | kept:{len(all_kept)} | A:{latest['A']} B:{latest['B']} C:{latest['C']} | queued_AB:{queued_ab} | top_query:{latest['top_query']} | blockers:{'none' if not blockers else 'short-list'}]")
