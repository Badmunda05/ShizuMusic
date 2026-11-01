"""
config.py — All environment variables in one place.
Copy sample.env → .env and fill in your values.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Required ──────────────────────────────────────────────────────────────────
API_ID          = int(os.environ["API_ID"])
API_HASH        = os.environ["API_HASH"]
BOT_TOKEN       = os.environ["BOT_TOKEN"]
STRING_SESSION  = os.environ["STRING_SESSION"]
MONGO_DB_URL    = os.environ["MONGO_DB_URL"]
OWNER_ID        = int(os.environ["OWNER_ID"])

# ── Optional ──────────────────────────────────────────────────────────────────
BOT_NAME         = os.getenv("BOT_NAME", "Shizu Music")
BOT_LINK         = os.getenv("BOT_LINK", "https://t.me/ShizuMusicBot")
UPDATES_CHANNEL  = os.getenv("UPDATES_CHANNEL", "https://t.me/PBX_UPDATE")
SUPPORT_GROUP    = os.getenv("SUPPORT_GROUP", "https://t.me/PBXCHATS")
LOGGER_ID        = int(os.getenv("LOGGER_ID", "0"))
PING_IMG_URL     = os.getenv("PING_IMG_URL", "https://files.catbox.moe/ddzvc0.jpg",)
SESSION_NAME     = os.getenv("SESSION_NAME", "ShizuMusic")
PORT             = int(os.getenv("PORT", 10000))

# ── Download config (cookies first, API as fallback) ─────────────────────────
# USE_COOKIES=True  : yt-dlp + cookies first, download API is the fallback
# USE_COOKIES=False : download API first, plain yt-dlp only if the API fails
# Default: False when API_URL + API_KEY are set, otherwise True.
# No API is hard-coded here — set your own via env (API_URL / API_KEY).
API_URL   = (os.getenv("API_URL") or os.getenv("YT_API_URL") or "").strip().rstrip("/")
API_KEY   = (os.getenv("API_KEY") or os.getenv("YT_API_KEY") or "").strip()


def _env_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None or val.strip() == "":
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


USE_COOKIES = _env_bool("USE_COOKIES", not (API_URL and API_KEY))
# batbin.me links to cookie files (space / comma / newline separated)
COOKIES_URL = [
    u for u in os.getenv("COOKIES_URL", "").replace(",", " ").split()
    if "batbin.me" in u
]
COOKIES_DIR       = "cookies"
DOWNLOAD_DIR      = "downloads"
YT_TOKEN_TIMEOUT  = 10    # seconds — fetch download token
YT_STREAM_TIMEOUT = 900   # 15 min  — download / stream long songs

# ── NSFW Moderation API ─────────────────────────────────────────────────────
#NSFW_API_URL = os.getenv("NSFW_API_URL", "https://ai-moderation-api-khyr.onrender.com")
#NSFW_API_KEY = os.getenv("NSFW_API_KEY", "nsfwBad")

# Custom detection thresholds — sent with every /detect/upload call.
#NSFW_THRESHOLDS = {
#    "porn": float(os.getenv("NSFW_THRESHOLD_PORN", "0.7")),
#    "sexy": float(os.getenv("NSFW_THRESHOLD_SEXY", "0.8")),
#}

#── Start ───────────────────────────────────────────────────────────────────────
START_PHOTOS = [
    "https://files.catbox.moe/jgt2vm.png",
]

# ── Limits ────────────────────────────────────────────────────────────────────
MAX_DURATION_SECONDS = 1800   # 30 minutes
QUEUE_LIMIT          = 20
COOLDOWN             = 10     # seconds between /play per chat

# ── Playlist limits ───────────────────────────────────────────────────────────
PLAYLIST_LIMIT       = 10     # playlists per user
PLAYLIST_SONG_LIMIT  = 50     # songs per playlist


#BLOCKED_EXTENSIONS = [
#    ".zip",
#    ".rar",
#    ".7z",
#    ".apk",
#    ".exe",
#    ".py",
#    ".js",
#    ".go",
#    ".php",
#]
