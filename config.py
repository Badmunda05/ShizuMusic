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

# ── NSFW Moderation API ─────────────────────────────────────────────────────
#NSFW_API_URL = os.getenv("NSFW_API_URL", "https://ai-moderation-api-khyr.onrender.com")
#NSFW_API_KEY = os.getenv("NSFW_API_KEY", "nsfwBad")

# Custom detection thresholds — sent with every /detect/upload call.
#NSFW_THRESHOLDS = {
#    "porn": float(os.getenv("NSFW_THRESHOLD_PORN", "0.7")),
#    "sexy": float(os.getenv("NSFW_THRESHOLD_SEXY", "0.8")),
}

#── Start ───────────────────────────────────────────────────────────────────────
START_ANIMATIONS = [
    "https://telegra.ph/file/1a3c152717eb9d2e94dc2.mp4",
    "https://graph.org/file/ba7699c28dab379b518ca.mp4",
    "https://graph.org/file/83ebf52e8bbf138620de7.mp4",
    "https://graph.org/file/82fd67aa56eb1b299e08d.mp4",
    "https://graph.org/file/318eac81e3d4667edcb77.mp4",
    "https://graph.org/file/7c1aa59649fbf3ab422da.mp4",
    "https://graph.org/file/2a7f857f31b32766ac6fc.mp4",
]

# ── Limits ────────────────────────────────────────────────────────────────────
MAX_DURATION_SECONDS = 1800   # 30 minutes
QUEUE_LIMIT          = 20
COOLDOWN             = 10     # seconds between /play per chat


BLOCKED_EXTENSIONS = [
    ".zip",
    ".rar",
    ".7z",
    ".apk",
    ".exe",
    ".py",
    ".js",
    ".go",
    ".php",
]
