"""
Step 1b: Scrape Agent-related course YouTube URLs from the Notion learning database.
輸出 notion_ai_urls.txt 供 download_subs.py 使用。

Requires: pip install firecrawl-py
Get a free API key at https://firecrawl.dev
"""
import re
import sys
import os
import json

sys.stdout.reconfigure(encoding='utf-8')

NOTION_URL = "https://rune-sea-d8b.notion.site/AI-2bcdb82eb7ff81afb178cca49446bfba"
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notion_ai_urls.txt")

AGENT_KEYWORDS = ["agent", "codex", "opencode", "antigravity", "claude", "cowork", "agentic", "workflow"]

# ── Firecrawl scrape ──────────────────────────────────────────────────────────
try:
    from firecrawl import FirecrawlApp
    FIRECRAWL_KEY = os.environ.get("FIRECRAWL_API_KEY", "")
    if not FIRECRAWL_KEY:
        raise EnvironmentError("Set FIRECRAWL_API_KEY environment variable first.")
    app = FirecrawlApp(api_key=FIRECRAWL_KEY)
    result = app.scrape_url(
        NOTION_URL,
        params={"formats": ["markdown"], "waitFor": 8000,
                "actions": [{"type": "scroll", "direction": "down"},
                             {"type": "wait", "milliseconds": 3000},
                             {"type": "scroll", "direction": "down"},
                             {"type": "wait", "milliseconds": 3000},
                             {"type": "scrape"}]}
    )
    md = result.get("markdown", "")
except Exception as e:
    print(f"Firecrawl error: {e}")
    print("Falling back to requests...")
    try:
        import requests
        r = requests.get(NOTION_URL, timeout=15)
        md = r.text
    except Exception as e2:
        print(f"Requests also failed: {e2}")
        sys.exit(1)

# ── Extract Notion course sub-page URLs ──────────────────────────────────────
notion_links = re.findall(
    r'\[([^\]]{5,100})\]\((https://rune-sea-d8b\.notion\.site/[A-Za-z0-9\-_一-鿿]+[^\)]*)\)',
    md
)
agent_notion_urls = []
seen = set()
for title, url in notion_links:
    clean = url.split('?')[0]
    if clean in seen or 'image' in url or 'attachment' in url or 'p/' in url:
        continue
    if any(kw in title.lower() or kw in clean.lower() for kw in AGENT_KEYWORDS):
        seen.add(clean)
        agent_notion_urls.append((title.strip(), clean))

print(f"Found {len(agent_notion_urls)} Agent-related Notion pages. Fetching YouTube URLs...")

# ── Visit each sub-page to extract YouTube URL ────────────────────────────────
youtube_urls = []
for title, notion_url in agent_notion_urls:
    print(f"  Checking: {title[:60]}")
    try:
        sub = app.scrape_url(notion_url, params={"formats": ["markdown"], "waitFor": 4000})
        sub_md = sub.get("markdown", "")
    except Exception:
        try:
            import requests
            sub_md = requests.get(notion_url, timeout=10).text
        except Exception:
            continue

    yt = re.findall(
        r'https?://(?:www\.)?(?:youtube\.com/watch\?[^\s\)\]\"\\\\]+|youtube\.com/playlist\?[^\s\)\]\"\\\\]+|youtu\.be/[\w\-]+)',
        sub_md
    )
    for u in yt:
        u = u.rstrip(')].\\\"')
        if u not in youtube_urls:
            youtube_urls.append(u)
            print(f"    -> {u}")

print(f"\nTotal YouTube URLs found: {len(youtube_urls)}")
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(youtube_urls) + "\n")
print(f"Saved to: {OUTPUT_FILE}")
