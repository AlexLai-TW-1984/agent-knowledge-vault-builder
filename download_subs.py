"""
Step 2: Download & clean subtitles for all URLs in a txt file.
Handles both individual videos and playlists.
輸出乾淨的 Markdown 檔案到 Clipping/ 資料夾。

Usage:
    python download_subs.py sensebar_ai_urls.txt
    python download_subs.py notion_ai_urls.txt
"""
import yt_dlp
import os
import re
import glob
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.abspath(__file__))
CLIPPING_DIR = os.path.join(BASE, "Clipping")
SUB_TMP = os.path.join(BASE, "_tmp_subs")
os.makedirs(CLIPPING_DIR, exist_ok=True)
os.makedirs(SUB_TMP, exist_ok=True)

urls_file = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE, "sensebar_ai_urls.txt")
with open(urls_file, "r", encoding="utf-8") as f:
    urls = [l.strip() for l in f if l.strip() and not l.startswith('#')]

def safe_name(title):
    return re.sub(r'[\\/*?:"<>|]', "_", title).strip().strip('.')

def parse_vtt(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    out, last = [], ""
    for line in lines:
        line = line.strip()
        if not line or line.startswith("WEBVTT") or line.startswith("Kind:") \
                or line.startswith("Language:") or "-->" in line:
            continue
        line = re.sub(r'<[^>]+>', '', line).strip()
        if not line or line == last:
            continue
        out.append(line)
        last = line
    return "\n".join(out)

def download_single(url, label=""):
    print(f"  [{label}] Fetching: {url}")
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'untitled')
    except Exception as e:
        print(f"    Error: {e}")
        return

    out_path = os.path.join(CLIPPING_DIR, f"{safe_name(title)}.md")
    if os.path.exists(out_path):
        print(f"    [Skip] Already exists: {safe_name(title)}.md")
        return

    for f in glob.glob(os.path.join(SUB_TMP, "tmp.*")):
        try: os.remove(f)
        except: pass

    ydl_opts = {
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsubtitles': True,
        'subtitleslangs': ['zh-Hant', 'zh-TW', 'zh', 'en'],
        'subtitlesformat': 'vtt',
        'outtmpl': os.path.join(SUB_TMP, 'tmp.%(ext)s'),
        'quiet': True, 'no_warnings': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)
        vtt_files = glob.glob(os.path.join(SUB_TMP, "tmp.*.vtt"))
        if vtt_files:
            text = parse_vtt(vtt_files[0])
            md = f"# {title}\n\n- 影片連結：{url}\n\n---\n\n{text}\n"
        else:
            md = f"# {title}\n\n- 影片連結：{url}\n\n*(No subtitles available)*\n"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"    [Done] {safe_name(title)}.md")
    except Exception as e:
        print(f"    Error: {e}")

    for f in glob.glob(os.path.join(SUB_TMP, "tmp.*")):
        try: os.remove(f)
        except: pass

def process(url, idx, total):
    if 'playlist' in url or ('list=' in url and 'watch' not in url):
        print(f"[{idx}/{total}] Expanding playlist: {url}")
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True, 'extract_flat': True}) as ydl:
                info = ydl.extract_info(url, download=False)
            entries = info.get('entries', [])
            print(f"  Playlist has {len(entries)} videos")
            for i, e in enumerate(entries, 1):
                vid_url = f"https://www.youtube.com/watch?v={e['id']}"
                download_single(vid_url, label=f"{idx}.{i}/{total}")
                time.sleep(1)
        except Exception as e:
            print(f"  Error expanding playlist: {e}")
    else:
        download_single(url, label=f"{idx}/{total}")

print(f"Processing {len(urls)} sources from {os.path.basename(urls_file)}")
for i, url in enumerate(urls, 1):
    process(url, i, len(urls))
    time.sleep(1)

print("\nDone! Subtitles saved to Clipping/")
