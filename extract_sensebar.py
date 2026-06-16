"""
Step 1a: Extract Agent-related video URLs from @sensebar YouTube channel.
輸出 sensebar_ai_urls.txt 供 download_subs.py 使用。
"""
import yt_dlp
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

CHANNEL_URL = "https://www.youtube.com/@sensebar/videos"
KEYWORDS = ["claude", "codex", "antigravity", "opencode", "agent"]
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sensebar_ai_urls.txt")

print("Extracting videos from @sensebar...")
try:
    with yt_dlp.YoutubeDL({'extract_flat': True, 'skip_download': True, 'quiet': True}) as ydl:
        info = ydl.extract_info(CHANNEL_URL, download=False)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)

entries = info.get('entries', [])
print(f"Total videos on channel: {len(entries)}")

matches = []
for entry in entries:
    title = entry.get('title', '')
    vid_id = entry.get('id', '') or entry.get('url', '')
    if not vid_id.startswith('http'):
        vid_id = f"https://www.youtube.com/watch?v={vid_id}"
    if any(kw in title.lower() for kw in KEYWORDS):
        matches.append(vid_id)

print(f"Matched {len(matches)} Agent-related videos.")
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(matches) + "\n")
print(f"Saved to: {OUTPUT_FILE}")
