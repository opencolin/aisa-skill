#!/usr/bin/env python3
"""Check the aisa skill before publishing. Makes free calls only; no paid AIsa call runs.

  python3 check_skill.py [skill-dir]
Checks the Agent Skills frontmatter limits, relative files and anchors, external links, stray secrets, stale rules from the
old skill, and (when AISA_API_KEY is set) the MCP tool names in SKILL.md against the live tools/list. Exits 1 on failure.
"""
import json, os, re, sys, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent / "aisa")
MCP = "https://mcp.aisa.one/mcp"
TOOLS = ["search", "list_categories", "batch_get_schema", "batch_quote", "batch_use", "account"]
fails = []


def check(ok, msg):
    print(("ok   " if ok else "FAIL ") + msg)
    if not ok:
        fails.append(msg)


skill = (ROOT / "SKILL.md").read_text()
files = sorted(ROOT.rglob("*.md"))
m = re.match(r"---\n(.*?)\n---\n", skill, re.S)
check(bool(m), "SKILL.md has frontmatter")
front = m.group(1) if m else ""


def block(key):
    b = re.search(rf"^{key}: >-\n((?:  .*\n?)+)", front, re.M)
    return " ".join(x.strip() for x in b.group(1).splitlines()) if b else ""


name = re.search(r"^name: (.+)$", front, re.M)
check(bool(name) and name.group(1) == ROOT.name, "name matches the directory")
check(bool(name) and re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name.group(1)) is not None, "name format")
desc, compat = block("description"), block("compatibility")
check(0 < len(desc) <= 1024, f"description is {len(desc)} chars (limit 1024)")
check(0 < len(compat) <= 500, f"compatibility is {len(compat)} chars (limit 500)")

for f in files:
    text = f.read_text()
    rel = f.relative_to(ROOT)
    check(not re.search(r"sk-aisa-[A-Za-z0-9]{10,}", text), f"{rel}: no API key")
    check("AISA_SEARCH_TOOL" not in text, f"{rel}: no placeholder tool names")

for ref in sorted(set(re.findall(r"references/[a-z0-9-]+\.md", skill))):
    check((ROOT / ref).exists(), f"{ref} exists")
for ref in sorted(p.name for p in (ROOT / "references").glob("*.md")):
    check(f"references/{ref}" in skill, f"SKILL.md links {ref}")

heads = {re.sub(r"[^a-z0-9 -]", "", h.lower()).strip().replace(" ", "-") for h in re.findall(r"^#+ (.+)$", skill, re.M)}
for a in sorted(set(re.findall(r"\]\(#([a-z0-9-]+)\)", skill))):
    check(a in heads, f"anchor #{a}")

check("/v1/credits/balance" in skill, "verification uses /v1/credits/balance")
check(not re.search(r"\|\s*HTTP\s*\|\s*`GET https://api\.aisa\.one/v1/models", skill), "verification does not rely on /v1/models")

SKIP = ("api.aisa.one", "api.circle.com", "mcp.aisa.one/mcp", "console.aisa.one")   # API hosts, and a console that blocks bots
urls = sorted({u.rstrip(".,:)`'\"") for f in files for u in re.findall(r"https://[^\s)`'\"<>|]+", f.read_text())
               if "{" not in u and "<" not in u and not any(x in u for x in SKIP)})


def status(u):
    req = urllib.request.Request(u.split("#")[0], headers={"User-Agent": "aisa-skill-check"})
    try:
        return u, urllib.request.urlopen(req, timeout=25).status
    except urllib.error.HTTPError as ex:
        return u, ex.code
    except Exception as ex:
        return u, type(ex).__name__


with ThreadPoolExecutor(8) as ex:
    for u, s in ex.map(status, urls):
        check(s in (200, 301, 302, 307, 308), f"{s} {u}")

key = os.environ.get("AISA_API_KEY")
if not key:
    print("skip live tool names: AISA_API_KEY is not set")
else:
    def rpc(body, sid=None):
        h = {"Authorization": f"Bearer {key}", "Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        if sid:
            h["Mcp-Session-Id"] = sid
        r = urllib.request.urlopen(urllib.request.Request(MCP, data=json.dumps(body).encode(), headers=h, method="POST"), timeout=60)
        t = r.read().decode()
        d = [x[5:].strip() for x in t.splitlines() if x.startswith("data:")]
        return (json.loads(d[-1] if d else t) if t.strip() else {}), r.headers.get("Mcp-Session-Id") or sid

    _, sid = rpc({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "aisa-skill-check", "version": "1"}}})
    rpc({"jsonrpc": "2.0", "method": "notifications/initialized"}, sid)
    live = {t["name"] for t in rpc({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}, sid)[0]["result"]["tools"]}
    for t in TOOLS:
        check(t in live and f"`{t}`" in skill, f"MCP tool {t} is live and documented")

print(f"\n{len(fails)} failed" if fails else "\nall checks passed")
sys.exit(1 if fails else 0)
