# ═══════════════════════════════════════════════════════════════
#                     🎵 SHIZUMUSIC
#
#                   © 2026 BAD MUNDA
#
#                Developed with ❤️ by Bad Munda
#
#             Do not remove or alter the original credits.
#
#           Copyright © 2026 Bad Munda. All rights reserved.
#
#              
# ═══════════════════════════════════════════════════════════════

import asyncio
import logging
import os
import re
from typing import Union

import aiofiles
import aiohttp
import yt_dlp
from py_yt import Playlist, VideosSearch
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from config import *
from ShizuMusic.utils.formatters import sec_to_iso

logger = logging.getLogger(__name__)

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


# Public alias — used by the autoplay engine to pull the video id back out
extract_video_id = _extract_video_id


def _cleanup(path: str) -> None:
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def time_to_seconds(time) -> int:
    """Convert M:SS or H:MM:SS string to total seconds."""
    stringt = str(time)
    return sum(int(x) * 60 ** i for i, x in enumerate(reversed(stringt.split(":"))))


# ═════════════════════════════════════════════════════════════════════════════
# DOWNLOAD HELPERS (New API — single-step direct stream)
# ═════════════════════════════════════════════════════════════════════════════

async def download_song(link: str) -> str:
    """Download audio via Shruti API. Returns local file path or None on failure."""
    video_id = _extract_video_id(link)
    if not video_id or len(video_id) < 3:
        return None

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp3")

    # Disk cache
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return file_path

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{YT_API_URL}/download",
                params={"url": video_id, "type": "audio", "api_key": YT_API_KEY},
                timeout=aiohttp.ClientTimeout(total=YT_STREAM_TIMEOUT),
            ) as resp:
                if resp.status != 200:
                    logger.warning(f"[shruti] Audio download failed: HTTP {resp.status}")
                    return None
                async with aiofiles.open(file_path, "wb") as f:
                    async for chunk in resp.content.iter_chunked(131072):
                        await f.write(chunk)

        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            return file_path
        return None

    except Exception as e:
        logger.error(f"[shruti] download_song error: {e}")
        _cleanup(file_path)
        return None


async def download_video(link: str) -> str:
    """Download video via Shruti API. Returns local file path or None on failure."""
    video_id = _extract_video_id(link)
    if not video_id or len(video_id) < 3:
        return None

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp4")

    # Disk cache
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return file_path

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{YT_API_URL}/download",
                params={"url": video_id, "type": "video", "api_key": YT_API_KEY},
                timeout=aiohttp.ClientTimeout(total=YT_STREAM_TIMEOUT),
            ) as resp:
                if resp.status != 200:
                    logger.warning(f"[shruti] Video download failed: HTTP {resp.status}")
                    return None
                async with aiofiles.open(file_path, "wb") as f:
                    async for chunk in resp.content.iter_chunked(131072):
                        await f.write(chunk)

        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            return file_path
        return None

    except Exception as e:
        logger.error(f"[shruti] download_video error: {e}")
        _cleanup(file_path)
        return None


# ═════════════════════════════════════════════════════════════════════════════
# PUBLIC — STREAM RESOLVER (backward-compatible)
# ═════════════════════════════════════════════════════════════════════════════

async def resolve_stream(url: str) -> str:
    """Resolve a YouTube URL or video ID to a local audio file path."""
    # Already a local file (e.g. Telegram audio download)
    if os.path.exists(url) and os.path.isfile(url):
        return url

    # In-memory cache
    if url in _file_cache and os.path.exists(_file_cache[url]):
        logger.info("[shruti] Cache hit")
        return _file_cache[url]

    video_id  = _extract_video_id(url)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp3")

    # Disk cache
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        _file_cache[url] = file_path
        return file_path

    logger.info(f"[shruti] Downloading: {video_id}")
    downloaded = await download_song(url)
    if downloaded:
        _file_cache[url] = downloaded
        logger.info(f"[shruti] Done — {os.path.getsize(downloaded) // 1024} KB")
        return downloaded

    raise Exception("Shruti API download failed. Please try again.")


# ═════════════════════════════════════════════════════════════════════════════
# PUBLIC — YOUTUBE SEARCH / METADATA
# ═════════════════════════════════════════════════════════════════════════════

async def search_yt(query: str):
    """Search YouTube for a video or playlist. Returns metadata tuple or playlist dict."""

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

    parts = [int(x) for x in dur.split(":")]
    secs  = (
        parts[0] * 3600 + parts[1] * 60 + parts[2]
        if len(parts) == 3
        else parts[0] * 60 + parts[1]
    )
    return (url, title, sec_to_iso(secs), thumb)


# ═════════════════════════════════════════════════════════════════════════════
# "UP NEXT" / RELATED VIDEOS  (used by AutoPlay)
# ═════════════════════════════════════════════════════════════════════════════
_INNERTUBE_NEXT = (
    "https://www.youtube.com/youtubei/v1/next"
    "?prettyPrint=false&key=AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"
)
_INNERTUBE_CLIENT_VERSION = "2.20250101.00.00"
_DURATION_RE = re.compile(r"^\d{1,2}(?::\d{2}){1,2}$")


def _yt_text(node) -> str:
    """Plain text of a YouTube text object (simpleText / runs / content)."""
    if isinstance(node, str):
        return node
    if isinstance(node, dict):
        if "simpleText" in node:
            return str(node["simpleText"])
        if "runs" in node:
            return "".join(str(r.get("text", "")) for r in node["runs"] if isinstance(r, dict))
        if "content" in node:
            return str(node["content"])
    return ""


def _find_duration(node):
    """First 'm:ss' / 'h:mm:ss' string anywhere inside node."""
    if isinstance(node, str):
        return node if _DURATION_RE.match(node.strip()) else None
    if isinstance(node, dict):
        for v in node.values():
            found = _find_duration(v)
            if found:
                return found.strip()
    elif isinstance(node, list):
        for v in node:
            found = _find_duration(v)
            if found:
                return found.strip()
    return None


def _first_content(node):
    """First 'content' string inside node (used for the channel name)."""
    if isinstance(node, dict):
        if isinstance(node.get("content"), str) and node["content"].strip():
            return node["content"]
        for v in node.values():
            found = _first_content(v)
            if found:
                return found
    elif isinstance(node, list):
        for v in node:
            found = _first_content(v)
            if found:
                return found
    return None


def parse_related(data, exclude_id=None, limit: int = 30):
    """
    Pull the recommended videos out of a youtubei /next response.
    Works with both the old (compactVideoRenderer) and the new
    (lockupViewModel) layouts, so a small YouTube change won't break it.
    """
    out, seen = [], set()

    def add(vid, title, duration, channel):
        if not vid or not title or vid == exclude_id or vid in seen:
            return
        seen.add(vid)
        out.append({"id": vid, "title": title, "duration": duration or "", "channel": channel or ""})

    def walk(node):
        if isinstance(node, dict):
            cvr = node.get("compactVideoRenderer")
            if isinstance(cvr, dict):
                add(
                    cvr.get("videoId"),
                    _yt_text(cvr.get("title")),
                    _yt_text(cvr.get("lengthText")) or _find_duration(cvr.get("thumbnailOverlays")),
                    _yt_text(cvr.get("longBylineText") or cvr.get("shortBylineText")),
                )
            lvm = node.get("lockupViewModel")
            if isinstance(lvm, dict) and lvm.get("contentType") == "LOCKUP_CONTENT_TYPE_VIDEO":
                meta = (lvm.get("metadata") or {}).get("lockupMetadataViewModel") or {}
                add(
                    lvm.get("contentId"),
                    _yt_text(meta.get("title")),
                    _find_duration(lvm.get("contentImage")),
                    _first_content(meta.get("metadata")),
                )
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(data)
    return out[:limit]


async def related_videos(video_id: str, limit: int = 30) -> list:
    """Videos YouTube itself suggests after `video_id` (best source for autoplay)."""
    payload = {
        "context": {
            "client": {
                "clientName": "WEB",
                "clientVersion": _INNERTUBE_CLIENT_VERSION,
                "hl": "en",
                "gl": "US",
            }
        },
        "videoId": video_id,
    }
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        ),
        "Content-Type": "application/json",
        "Origin": "https://www.youtube.com",
        "X-YouTube-Client-Name": "1",
        "X-YouTube-Client-Version": _INNERTUBE_CLIENT_VERSION,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                _INNERTUBE_NEXT,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=8),
            ) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json(content_type=None)
        return parse_related(data, exclude_id=video_id, limit=limit)
    except Exception as e:
        logger.warning(f"[related_videos] {video_id}: {e}")
        return []


# ═════════════════════════════════════════════════════════════════════════════
# PUBLIC — YouTubeAPI CLASS (full-featured, from Youtube5 style)
# ═════════════════════════════════════════════════════════════════════════════

class YouTubeAPI:
    def __init__(self):
        self.base     = "https://www.youtube.com/watch?v="
        self.regex    = r"(?:youtube\.com|youtu\.be)"
        self.status   = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg      = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _build_link(self, link: str, videoid) -> str:
        return (self.base + link) if videoid else link

    def _strip_extra(self, link: str) -> str:
        return link.split("&")[0] if "&" in link else link

    # ── Public methods ────────────────────────────────────────────────────────

    async def exists(self, link: str, videoid: Union[bool, str] = None) -> bool:
        if videoid:
            link = self.base + link
        return bool(re.search(self.regex, link))

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        for message in messages:
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        return text[entity.offset: entity.offset + entity.length]
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        return None

    async def details(self, link: str, videoid: Union[bool, str] = None):
        link = self._strip_extra(self._build_link(link, videoid))
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title        = result["title"]
            duration_min = result["duration"]
            thumbnail    = result["thumbnails"][0]["url"].split("?")[0]
            vidid        = result["id"]
            duration_sec = int(time_to_seconds(duration_min)) if duration_min else 0
        return title, duration_min, duration_sec, thumbnail, vidid

    async def title(self, link: str, videoid: Union[bool, str] = None) -> str:
        link = self._strip_extra(self._build_link(link, videoid))
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["title"]

    async def duration(self, link: str, videoid: Union[bool, str] = None) -> str:
        link = self._strip_extra(self._build_link(link, videoid))
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["duration"]

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None) -> str:
        link = self._strip_extra(self._build_link(link, videoid))
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["thumbnails"][0]["url"].split("?")[0]

    async def video(self, link: str, videoid: Union[bool, str] = None):
        link = self._strip_extra(self._build_link(link, videoid))
        try:
            downloaded_file = await download_video(link)
            if downloaded_file:
                return 1, downloaded_file
            return 0, "Video download failed"
        except Exception as e:
            return 0, f"Video download error: {e}"

    async def playlist(
        self, link: str, limit: int, user_id, videoid: Union[bool, str] = None
    ) -> list:
        if videoid:
            link = self.listbase + link
        link = self._strip_extra(link)
        try:
            plist = await Playlist.get(link)
        except Exception:
            return []
        videos = plist.get("videos") or []
        ids = []
        for data in videos[:limit]:
            if not data:
                continue
            vid = data.get("id")
            if not vid:
                continue
            ids.append(vid)
        return ids

    async def track(self, link: str, videoid: Union[bool, str] = None):
        link = self._strip_extra(self._build_link(link, videoid))
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title        = result["title"]
            duration_min = result["duration"]
            vidid        = result["id"]
            yturl        = result["link"]
            thumbnail    = result["thumbnails"][0]["url"].split("?")[0]
        track_details = {
            "title":        title,
            "link":         yturl,
            "vidid":        vidid,
            "duration_min": duration_min,
            "thumb":        thumbnail,
        }
        return track_details, vidid

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        link = self._strip_extra(self._build_link(link, videoid))
        ytdl_opts = {"quiet": True}
        ydl = yt_dlp.YoutubeDL(ytdl_opts)
        with ydl:
            formats_available = []
            r = ydl.extract_info(link, download=False)
            for fmt in r["formats"]:
                try:
                    if "dash" not in str(fmt["format"]).lower():
                        formats_available.append(
                            {
                                "format":      fmt["format"],
                                "filesize":    fmt.get("filesize"),
                                "format_id":   fmt["format_id"],
                                "ext":         fmt["ext"],
                                "format_note": fmt["format_note"],
                                "yturl":       link,
                            }
                        )
                except Exception:
                    continue
        return formats_available, link

    async def slider(
        self, link: str, query_type: int, videoid: Union[bool, str] = None
    ):
        link = self._strip_extra(self._build_link(link, videoid))
        a      = VideosSearch(link, limit=10)
        result = (await a.next()).get("result")
        title        = result[query_type]["title"]
        duration_min = result[query_type]["duration"]
        vidid        = result[query_type]["id"]
        thumbnail    = result[query_type]["thumbnails"][0]["url"].split("?")[0]
        return title, duration_min, thumbnail, vidid

    async def download(
        self,
        link: str,
        mystic,
        video:     Union[bool, str] = None,
        videoid:   Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title:     Union[bool, str] = None,
    ):
        if videoid:
            link = self.base + link
        try:
            if video:
                downloaded_file = await download_video(link)
            else:
                downloaded_file = await download_song(link)
            if downloaded_file:
                return downloaded_file, True
            return None, False
        except Exception:
            return None, False
