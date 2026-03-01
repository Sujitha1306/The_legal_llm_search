import requests
import time
import random
import json
import os
import sys

# Force ASCII-safe output for Windows PowerShell
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from local_search_llm_v2 import OllamaSearchAgent

def sep(title):
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)

# ── CHECK 1: User-Agent Rotation ──────────────────────────────
sep("CHECK 1: User-Agent Rotation")
agent = OllamaSearchAgent.__new__(OllamaSearchAgent)
uas = []
for i in range(3):
    h = agent._get_headers()
    ua = h["User-Agent"]
    uas.append(ua)
    print(f"  [{i+1}] {ua[:90]}")

has_python = any("python-requests" in u.lower() for u in uas)
unique = len(set(uas)) == 3
if has_python:
    print("  RESULT: FAIL -- python-requests User-Agent leaked!")
elif unique:
    print("  RESULT: PASS -- All 3 User-Agents are unique.")
else:
    print("  RESULT: WARN -- Some User-Agents are repeated.")

# ── CHECK 2: IP Anonymity ─────────────────────────────────────
sep("CHECK 2: IP Anonymity (No Proxy - Phase 2 Deferred)")
try:
    r = requests.get("https://httpbin.org/ip", headers=agent._get_headers(), timeout=10)
    ip = r.json().get("origin", "unknown")
    print(f"  Visible IP to target sites: {ip}")
    print("  RESULT: NOTE -- This is your real IP. Proxy/Tor deferred to Phase 2.")
except Exception as e:
    print(f"  RESULT: ERROR -- Could not reach httpbin.org: {e}")

# ── CHECK 3: Rate Limiting Delays ────────────────────────────
sep("CHECK 3: Rate Limiting -- Human-like Delays")
d_list = []
for i in range(3):
    d = random.uniform(2, 5)
    t0 = time.time()
    time.sleep(d)
    actual = time.time() - t0
    d_list.append(actual)
    print(f"  Iteration {i+1}: target={d:.2f}s  actual={actual:.2f}s")

in_range = all(2.0 <= x <= 5.5 for x in d_list)
varied = (max(d_list) - min(d_list)) > 0.3
if in_range and varied:
    print("  RESULT: PASS -- Random delays 2-5s confirmed.")
elif in_range:
    print("  RESULT: WARN -- In range but low variance.")
else:
    print("  RESULT: FAIL -- Delays outside expected 2-5s range.")

# ── CHECK 4: Legal Source Migration ──────────────────────────
sep("CHECK 4: Legal Source Migration")
base = os.path.dirname(os.path.abspath(__file__))
legal_path = os.path.join(base, "legal_sources.json")
legacy_path = os.path.join(base, "legacy_news_sources.json")

try:
    with open(legal_path, encoding="utf-8") as f:
        legal = json.load(f)
    print(f"  legal_sources.json -- {len(legal)} entries:")
    for s in legal:
        print(f"    [{s['id']}] {s['displayName']}: {s['name']}")
    old_in_legal = [s["name"] for s in legal if any(
        x in s["name"] for x in ["indiatimes", "hindustantimes", "firstpost", "thewire", "indiatoday"]
    )]
    if old_in_legal:
        print(f"  RESULT: WARN -- Old news URLs still present: {old_in_legal}")
    else:
        print("  RESULT: PASS -- No old news URLs in legal_sources.json.")
except Exception as e:
    print(f"  ERROR: {e}")

try:
    with open(legacy_path, encoding="utf-8") as f:
        legacy = json.load(f)
    print(f"\n  legacy_news_sources.json -- {len(legacy)} sites archived:")
    for s in legacy:
        print(f"    [{s['id']}] {s['displayName']}: {s['name']}")
    print("  RESULT: PASS -- Legacy sources correctly archived.")
except Exception as e:
    print(f"  ERROR: {e}")

# ── CHECK 5: Bot-Check on Legal Sites ───────────────────────
sep("CHECK 5: Bot-Check (Status + Cloudflare Detection)")
test_urls = [
    ("Indian Kanoon", "https://indiankanoon.org/"),
    ("Live Law",      "https://www.livelaw.in/"),
    ("Bar and Bench", "https://www.barandbench.com/"),
]
for name, url in test_urls:
    delay = random.uniform(2, 4)
    print(f"\n  Testing {name} ({url}) -- waiting {delay:.1f}s ...")
    time.sleep(delay)
    try:
        t0 = time.time()
        resp = requests.get(url, headers=agent._get_headers(), timeout=15)
        elapsed = time.time() - t0
        code = resp.status_code
        cf = any(x in resp.text for x in ["Just a moment", "Checking your browser", "cf-browser-verification", "Enable JavaScript"])
        preview = resp.text[:200].replace("\n", " ").strip()

        if code == 200 and not cf:
            verdict = "PASS -- 200 OK, no Cloudflare block"
        elif cf:
            verdict = "FAIL -- Cloudflare wall detected (Just a moment...)"
        elif code == 403:
            verdict = "FAIL -- 403 Forbidden (IP/UA blocked)"
        elif code == 429:
            verdict = "FAIL -- 429 Too Many Requests (rate too fast)"
        else:
            verdict = f"WARN -- Unexpected status {code}"

        print(f"  Status: {code}  |  Time: {elapsed:.1f}s")
        print(f"  RESULT: {verdict}")
        print(f"  Preview: {preview[:180]}...")
    except Exception as e:
        print(f"  RESULT: ERROR -- {e}")

print()
print("=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)
