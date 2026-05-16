# --------------------------------------------------------------------------------
#  Alpha Music © 2026
#  Direct YouTube Downloader (Stable Version)
# --------------------------------------------------------------------------------

import asyncio
import logging
import os
import yt_dlp
from py_yt import Playlist, VideosSearch
from ShizuMusic.utils.formatters import sec_to_iso

logger = logging.getLogger(__name__)

DOWNLOAD_DIR = "downloads"
COOKIE_FILE  = "cookies.txt"

_file_cache: dict[str, str] = {}

def _extract_video_id(url: str) -> str:
    if "v=" in url:
        return url.split("v=")[-1].split("&")[0]
    if "youtu.be/" in url:
        return url.split("youtu.be/")[-1].split("?")[0]
    return url

async def _download_via_ytdlp(url: str, file_path: str) -> bool:
    """Enhanced Direct Download logic"""
    try:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": file_path.replace(".mp3", ""), # yt-dlp automatically adds .mp3
            "cookiefile": COOKIE_FILE,
            "quiet": True,
            "no_warnings": True,
            "nocheckcertificate": True,
            "source_address": "0.0.0.0", # Helps with IPv6 issues on Render
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }

        def _do_download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        await asyncio.to_thread(_do_download)
        
        # Check for the file with multiple attempts
        actual_file = file_path if file_path.endswith(".mp3") else f"{file_path}.mp3"
        return os.path.exists(actual_file) and os.path.getsize(actual_file) > 0
    except Exception as e:
        logger.error(f"[Alpha] Download error: {str(e)}")
        return False

async def resolve_stream(url: str) -> str:
    if os.path.exists(url) and os.path.isfile(url):
        return url

    if url in _file_cache and os.path.exists(_file_cache[url]):
        return _file_cache[url]

    video_id  = _extract_video_id(url)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp3")

    if os.path.exists(file_path):
        return file_path

    logger.info(f"[Alpha] Downloading: {video_id}")
    
    if await _download_via_ytdlp(url, file_path):
        _file_cache[url] = file_path
        return file_path

    if os.path.exists(file_path):
        os.remove(file_path)
        
    # Final Error Message
    raise Exception("Download failed. Please check if cookies.txt is valid and uploaded.")

# search_yt function remains the same as previous version
async def search_yt(query: str):
    if "playlist?list=" in query or "&list=" in query:
        pl = await Playlist.get(query)
        vids = pl.get("videos") or []
        items = []
        for v in vids:
            try:
                raw = v.get("duration", {})
                secs = int(raw.get("secondsText", 0)) if isinstance(raw, dict) else int(raw or 0)
                thumb = (v.get("thumbnails") or [{}])[0].get("url", "").split("?")[0]
                items.append({"link": f"https://www.youtube.com/watch?v={v['id']}", "title": v.get("title", "Unknown"), "duration": sec_to_iso(secs), "thumbnail": thumb})
            except: continue
        return {"playlist": items}

    search = VideosSearch(query, limit=1)
    res = (await search.next()).get("result", [])[0]
    dur = res.get("duration") or "0:00"
    parts = [int(x) for x in dur.split(":")]
    secs = parts[0]*3600 + parts[1]*60 + parts[2] if len(parts)==3 else parts[0]*60 + parts[1] if len(parts)==2 else 0
    return (res.get("link"), res.get("title"), sec_to_iso(secs), res.get("thumbnails")[0]["url"].split("?")[0])
    
