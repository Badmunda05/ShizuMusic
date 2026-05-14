# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

import asyncio
import logging
import os
import yt_dlp

import aiofiles
import aiohttp
from py_yt import Playlist, VideosSearch

from ShizuMusic.utils.formatters import sec_to_iso

logger = logging.getLogger(__name__)

# ── Alpha Music Config ────────────────────────────────────────────────────────
DOWNLOAD_DIR          = "downloads"
STREAM_TIMEOUT        = 900   # 15 min — stream long songs

_file_cache: dict[str, str] = {}


# ═════════════════════════════════════════════════════════════════════════════
# INTERNAL HELPERS
# ═════════════════════════════════════════════════════════════════════════════

def _extract_video_id(url: str) -> str:
    """Extract raw video ID from any YouTube URL format."""
    if "v=" in url:
        return url.split("v=")[-1].split("&")[0]
    if "youtu.be/" in url:
        return url.split("youtu.be/")[-1].split("?")[0]
    return url


def _cleanup(path: str) -> None:
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


async def _stream_to_file(response: aiohttp.ClientResponse, file_path: str) -> bool:
    """Stream HTTP response body directly to a file."""
    try:
        async with aiofiles.open(file_path, "wb") as f:
            async for chunk in response.content.iter_chunked(65536):
                await f.write(chunk)
        return os.path.exists(file_path) and os.path.getsize(file_path) > 0
    except Exception as e:
        logger.error(f"[alpha] stream_to_file: {e}")
        return False


async def _fetch_and_save(direct_url: str, file_path: str) -> bool:
    """Follow a redirect URL and save the audio file."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                direct_url,
                timeout=aiohttp.ClientTimeout(total=STREAM_TIMEOUT),
            ) as resp:
                if resp.status not in (200, 206):
                    return False
                async with aiofiles.open(file_path, "wb") as f:
                    async for chunk in resp.content.iter_chunked(65536):
                        await f.write(chunk)
        return os.path.exists(file_path) and os.path.getsize(file_path) > 0
    except Exception as e:
        logger.error(f"[alpha] fetch_and_save: {e}")
        return False


async def _download_via_alpha(video_id: str, file_path: str) -> bool:
    """
    Direct YT-DLP Download - No Watermarks, No external APIs.
    """
    try:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": file_path,
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
        }
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            await loop.run_in_executor(
                None, 
                lambda: ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
            )
        return os.path.exists(file_path) and os.path.getsize(file_path) > 0

    except Exception as e:
        logger.error(f"[alpha-dlp] Error: {e}")
        return False


# ═════════════════════════════════════════════════════════════════════════════
# PUBLIC — STREAM RESOLVER
# ═════════════════════════════════════════════════════════════════════════════

async def resolve_stream(url: str) -> str:
    # Already a local file (e.g. Telegram audio download)
    if os.path.exists(url) and os.path.isfile(url):
        return url

    # In-memory cache
    if url in _file_cache and os.path.exists(_file_cache[url]):
        logger.info("[alpha] Cache hit")
        return _file_cache[url]

    video_id  = _extract_video_id(url)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp3")

    # Disk cache
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        _file_cache[url] = file_path
        return file_path

    logger.info(f"[alpha] Downloading: {video_id}")
    # Using the new Direct Alpha Download logic
    if await _download_via_alpha(video_id, file_path):
        _file_cache[url] = file_path
        logger.info(f"[alpha] Done — {os.path.getsize(file_path) // 1024} KB")
        return file_path

    _cleanup(file_path)
    raise Exception("Alpha Music download failed. Please try again.")


# ═════════════════════════════════════════════════════════════════════════════
# PUBLIC — YOUTUBE SEARCH / METADATA
# ═════════════════════════════════════════════════════════════════════════════

async def search_yt(query: str):

    # ── Playlist ──────────────────────────────────────────────────────────────
    if "playlist?list=" in query or "&list=" in query:
        pl   = await Playlist.get(query)
        vids = pl.get("videos") or []
        if not vids:
            raise Exception("ᴩʟᴀʏʟɪsᴛ ɪs ᴇᴍᴩᴛʏ")

        items = []
        for v in vids:
            raw = v.get("duration", {})
            if isinstance(raw, dict):
                try:
                    secs = int(raw.get("secondsText", 0))
                except Exception:
                    secs = 0
            else:
                try:
                    secs = int(raw)
                except Exception:
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

    # ── Single video search ───────────────────────────────────────────────────
    search  = VideosSearch(query, limit=1)
    results = await search.next()
    lst     = results.get("result", [])
    if not lst:
        raise Exception("ɴᴏ ʀᴇsᴜʟᴛs ғᴏᴜɴᴅ")

    r     = lst[0]
    url   = r.get("link") or f"https://www.youtube.com/watch?v={r['id']}"
    title = r.get("title", "Unknown")
    thumb = (r.get("thumbnails") or [{}])[0].get("url", "").split("?")[0]
    dur   = r.get("duration") or "0:00"

    # Convert "M:SS" / "H:MM:SS" → seconds
    parts = [int(x) for x in dur.split(":")]
    secs  = (
        parts[0] * 3600 + parts[1] * 60 + parts[2]
        if len(parts) == 3
        else parts[0] * 60 + parts[1]
    )
    return (url, title, sec_to_iso(secs), thumb)
    
