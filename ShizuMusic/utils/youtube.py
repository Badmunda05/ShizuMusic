# --------------------------------------------------------------------------------
#  Alpha Music © 2026
#  Updated to bypass Shruti API & use personal cookies.txt
# --------------------------------------------------------------------------------

import asyncio
import logging
import os
import yt_dlp
import aiofiles
from py_yt import Playlist, VideosSearch
from ShizuMusic.utils.formatters import sec_to_iso

logger = logging.getLogger(__name__)

DOWNLOAD_DIR = "downloads"
COOKIE_FILE  = "cookies.txt" # Aapne jo main folder mein upload ki hai

_file_cache: dict[str, str] = {}

# ═════════════════════════════════════════════════════════════════════════════
# INTERNAL HELPERS (Direct YT-DLP Download)
# ═════════════════════════════════════════════════════════════════════════════

def _extract_video_id(url: str) -> str:
    if "v=" in url:
        return url.split("v=")[-1].split("&")[0]
    if "youtu.be/" in url:
        return url.split("youtu.be/")[-1].split("?")[0]
    return url

async def _download_via_ytdlp(url: str, file_path: str) -> bool:
    """Download direct from YouTube using yt-dlp and cookies.txt"""
    try:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": file_path.replace(".mp3", ".%(ext)s"), # Temporary template
            "cookiefile": COOKIE_FILE,
            "quiet": True,
            "no_warnings": True,
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
        
        # Check if the converted mp3 exists
        return os.path.exists(file_path) and os.path.getsize(file_path) > 0
    except Exception as e:
        logger.error(f"[yt-dlp] Download error: {e}")
        return False

# ═════════════════════════════════════════════════════════════════════════════
# PUBLIC — STREAM RESOLVER
# ═════════════════════════════════════════════════════════════════════════════

async def resolve_stream(url: str) -> str:
    if os.path.exists(url) and os.path.isfile(url):
        return url

    if url in _file_cache and os.path.exists(_file_cache[url]):
        return _file_cache[url]

    video_id  = _extract_video_id(url)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp3")

    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        _file_cache[url] = file_path
        return file_path

    logger.info(f"[Alpha] Downloading: {video_id} using yt-dlp")
    
    # Using our new direct download method instead of Shruti API
    if await _download_via_ytdlp(url, file_path):
        _file_cache[url] = file_path
        logger.info(f"[Alpha] Success — {os.path.getsize(file_path) // 1024} KB")
        return file_path

    if os.path.exists(file_path):
        os.remove(file_path)
        
    raise Exception("Download failed. YouTube might be blocking or cookies expired.")


# ═════════════════════════════════════════════════════════════════════════════
# PUBLIC — YOUTUBE SEARCH / METADATA
# ═════════════════════════════════════════════════════════════════════════════

async def search_yt(query: str):
    if "playlist?list=" in query or "&list=" in query:
        pl   = await Playlist.get(query)
        vids = pl.get("videos") or []
        if not vids:
            raise Exception("Playlist is empty")

        items = []
        for v in vids:
            try:
                raw = v.get("duration", {})
                secs = int(raw.get("secondsText", 0)) if isinstance(raw, dict) else int(raw or 0)
            except:
                secs = 0

            thumbs = v.get("thumbnails") or []
            thumb  = thumbs[0].get("url", "").split("?")[0] if thumbs else ""
            items.append({
                "link":      f"https://www.youtube.com/watch?v={v['id']}",
                "title":     v.get("title", "Unknown"),
                "duration":  sec_to_iso(secs),
                "thumbnail": thumb,
            })
        return {"playlist": items}

    search  = VideosSearch(query, limit=1)
    results = await search.next()
    lst     = results.get("result", [])
    if not lst:
        raise Exception("No results found")

    r     = lst[0]
    url   = r.get("link") or f"https://www.youtube.com/watch?v={r['id']}"
    title = r.get("title", "Unknown")
    thumb = (r.get("thumbnails") or [{}])[0].get("url", "").split("?")[0]
    dur   = r.get("duration") or "0:00"

    parts = [int(x) for x in dur.split(":")]
    secs  = (
        parts[0] * 3600 + parts[1] * 60 + parts[2]
        if len(parts) == 3
        else parts[0] * 60 + parts[1] if len(parts) == 2 else 0
    )
    return (url, title, sec_to_iso(secs), thumb)
