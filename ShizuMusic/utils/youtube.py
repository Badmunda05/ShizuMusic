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

import aiofiles
import aiohttp
from py_yt import Playlist, VideosSearch

from ShizuMusic.utils.formatters import sec_to_iso

logger = logging.getLogger(__name__)

# ── Shruti API config ─────────────────────────────────────────────────────────
SHRUTI_API_URL        = "https://shrutibots.site"
DOWNLOAD_DIR          = "downloads"
SHRUTI_TOKEN_TIMEOUT  = 10    # seconds — fetch download token
SHRUTI_STREAM_TIMEOUT = 900   # 15 min  — stream long songs

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
        logger.error(f"[shruti] stream_to_file: {e}")
        return False


async def _fetch_and_save(direct_url: str, file_path: str) -> bool:
    """Follow a redirect URL and save the audio file."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                direct_url,
                timeout=aiohttp.ClientTimeout(total=SHRUTI_STREAM_TIMEOUT),
            ) as resp:
                if resp.status not in (200, 206):
                    return False
                async with aiofiles.open(file_path, "wb") as f:
                    async for chunk in resp.content.iter_chunked(65536):
                        await f.write(chunk)
        return os.path.exists(file_path) and os.path.getsize(file_path) > 0
    except Exception as e:
        logger.error(f"[shruti] fetch_and_save: {e}")
        return False


async def _download_via_shruti(video_id: str, file_path: str) -> bool:
    """
    Two-step Shruti API download:
      Step 1 → GET /download?url=<id>&type=audio  →  download_token
      Step 2 → GET /stream/<id>?type=audio&token=  →  mp3 (direct or 302 redirect)
    """
    try:
        async with aiohttp.ClientSession() as session:

            # Step 1 — get token
            async with session.get(
                f"{SHRUTI_API_URL}/download",
                params={"url": video_id, "type": "audio"},
                timeout=aiohttp.ClientTimeout(total=SHRUTI_TOKEN_TIMEOUT),
            ) as resp:
                if resp.status != 200:
                    logger.warning(f"[shruti] Token fetch failed: HTTP {resp.status}")
                    return False
                data  = await resp.json()
                token = data.get("download_token")
                if not token:
                    logger.warning("[shruti] No download_token in response")
                    return False

            # Step 2 — stream audio
            stream_url = (
                f"{SHRUTI_API_URL}/stream/{video_id}"
                f"?type=audio&token={token}"
            )
            async with session.get(
                stream_url,
                timeout=aiohttp.ClientTimeout(total=SHRUTI_STREAM_TIMEOUT),
                allow_redirects=False,
            ) as file_resp:
                if file_resp.status == 302:
                    redirect = file_resp.headers.get("Location")
                    if not redirect:
                        return False
                    return await _fetch_and_save(redirect, file_path)
                elif file_resp.status == 200:
                    return await _stream_to_file(file_resp, file_path)
                else:
                    logger.warning(f"[shruti] Stream HTTP {file_resp.status}")
                    return False

    except asyncio.TimeoutError:
        logger.warning("[shruti] Request timed out")
        return False
    except Exception as e:
        logger.error(f"[shruti] Unexpected error: {e}")
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
        logger.info("[shruti] Cache hit")
        return _file_cache[url]

    video_id  = _extract_video_id(url)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp3")

    # Disk cache
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        _file_cache[url] = file_path
        return file_path

    logger.info(f"[shruti] Downloading: {video_id}")
    if await _download_via_shruti(video_id, file_path):
        _file_cache[url] = file_path
        logger.info(f"[shruti] Done — {os.path.getsize(file_path) // 1024} KB")
        return file_path

    _cleanup(file_path)
    raise Exception("Shruti API download failed. Please try again.")


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
