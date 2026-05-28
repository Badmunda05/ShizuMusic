# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

import logging
from typing import Optional

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

import config

logger = logging.getLogger(__name__)

# ── Client ─────────────────────────────────────────────────────────────────────
_client: Optional[MongoClient] = None
_db = None


def start_mongo() -> bool:
    global _client, _db

    if not config.MONGO_DB_URL:
        logger.warning("MONGO_DB_URL not set — database features disabled.")
        return False

    try:
        _client = MongoClient(config.MONGO_DB_URL, serverSelectionTimeoutMS=5000)
        _client.admin.command("ping")
        _db = _client["ShizuMusic"]
        logger.info("✅ MongoDB connected successfully.")
        return True

    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        _client = None
        _db = None
        return False

    except Exception as e:
        logger.error(f"❌ MongoDB unexpected error: {e}")
        _client = None
        _db = None
        return False


def get_db():
    return _db


def is_connected() -> bool:
    return _db is not None


def get_mongo_client() -> Optional[MongoClient]:
    """Return the raw MongoClient (used for dbstats in /stats command)."""
    return _client


# ── Collections ────────────────────────────────────────────────────────────────

def _col(name: str):
    if _db is None:
        return None
    return _db[name]


# ── Served Chats ───────────────────────────────────────────────────────────────
# FIX: All served chat/user data is stored in MongoDB only.
# There is NO in-memory set/list — so bot restarts never reset counts to 0.

def add_served_chat(chat_id: int) -> None:
    col = _col("served_chats")
    if col is None:
        return
    try:
        col.update_one({"_id": chat_id}, {"$set": {"_id": chat_id}}, upsert=True)
    except Exception as e:
        logger.error(f"[DB] add_served_chat: {e}")


def get_served_chats() -> list:
    col = _col("served_chats")
    if col is None:
        return []
    try:
        return [doc["_id"] for doc in col.find({}, {"_id": 1})]
    except Exception as e:
        logger.error(f"[DB] get_served_chats: {e}")
        return []


def get_served_chats_count() -> int:
    col = _col("served_chats")
    if col is None:
        return 0
    try:
        return col.count_documents({})
    except Exception as e:
        logger.error(f"[DB] get_served_chats_count: {e}")
        return 0


def remove_served_chat(chat_id: int) -> None:
    col = _col("served_chats")
    if col is None:
        return
    try:
        col.delete_one({"_id": chat_id})
    except Exception as e:
        logger.error(f"[DB] remove_served_chat: {e}")


# ── Served Users ───────────────────────────────────────────────────────────────

def add_served_user(user_id: int) -> None:
    col = _col("served_users")
    if col is None:
        return
    try:
        col.update_one({"_id": user_id}, {"$set": {"_id": user_id}}, upsert=True)
    except Exception as e:
        logger.error(f"[DB] add_served_user: {e}")


def get_served_users() -> list:
    col = _col("served_users")
    if col is None:
        return []
    try:
        return [doc["_id"] for doc in col.find({}, {"_id": 1})]
    except Exception as e:
        logger.error(f"[DB] get_served_users: {e}")
        return []


def get_served_users_count() -> int:
    col = _col("served_users")
    if col is None:
        return 0
    try:
        return col.count_documents({})
    except Exception as e:
        logger.error(f"[DB] get_served_users_count: {e}")
        return 0


# ── Blocked Chats (ban) ────────────────────────────────────────────────────────

def ban_chat(chat_id: int) -> None:
    col = _col("banned_chats")
    if col is None:
        return
    try:
        col.update_one({"_id": chat_id}, {"$set": {"_id": chat_id}}, upsert=True)
    except Exception as e:
        logger.error(f"[DB] ban_chat: {e}")


def unban_chat(chat_id: int) -> None:
    col = _col("banned_chats")
    if col is None:
        return
    try:
        col.delete_one({"_id": chat_id})
    except Exception as e:
        logger.error(f"[DB] unban_chat: {e}")


def is_chat_banned(chat_id: int) -> bool:
    col = _col("banned_chats")
    if col is None:
        return False
    try:
        return col.find_one({"_id": chat_id}) is not None
    except Exception:
        return False


def get_banned_chats() -> list:
    col = _col("banned_chats")
    if col is None:
        return []
    try:
        return [doc["_id"] for doc in col.find({}, {"_id": 1})]
    except Exception:
        return []


def get_banned_chats_count() -> int:
    col = _col("banned_chats")
    if col is None:
        return 0
    try:
        return col.count_documents({})
    except Exception:
        return 0


# ── Assistant Joined Chats ─────────────────────────────────────────────────────

def mark_assistant_joined(chat_id: int) -> None:
    col = _col("assistant_chats")
    if col is None:
        return
    try:
        col.update_one({"_id": chat_id}, {"$set": {"_id": chat_id}}, upsert=True)
    except Exception as e:
        logger.error(f"[DB] mark_assistant_joined: {e}")


def is_assistant_joined(chat_id: int) -> bool:
    col = _col("assistant_chats")
    if col is None:
        return False
    try:
        return col.find_one({"_id": chat_id}) is not None
    except Exception:
        return False


# ── Play Stats ─────────────────────────────────────────────────────────────────

def increment_play_count(chat_id: int) -> None:
    col = _col("play_stats")
    if col is None:
        return
    try:
        col.update_one(
            {"_id": chat_id},
            {"$inc": {"count": 1}},
            upsert=True,
        )
    except Exception as e:
        logger.error(f"[DB] increment_play_count: {e}")


def get_total_plays() -> int:
    col = _col("play_stats")
    if col is None:
        return 0
    try:
        result = col.aggregate([{"$group": {"_id": None, "total": {"$sum": "$count"}}}])
        for r in result:
            return r.get("total", 0)
        return 0
    except Exception:
        return 0


# ── Broadcast Chats ────────────────────────────────────────────────────────────

def add_broadcast_chat(chat_id: int, chat_type: str) -> None:
    col = _col("broadcast")
    if col is None:
        return
    try:
        col.update_one(
            {"_id": int(chat_id)},
            {
                "$set": {
                    "_id": int(chat_id),
                    "chat_id": int(chat_id),
                    "type": chat_type,
                }
            },
            upsert=True,
        )
    except Exception as e:
        logger.error(f"[DB] add_broadcast_chat: {e}")


def get_broadcast_chats() -> list:
    col = _col("broadcast")
    if col is None:
        return []
    try:
        return list(col.find({}, {"_id": 1, "chat_id": 1, "type": 1}))
    except Exception as e:
        logger.error(f"[DB] get_broadcast_chats: {e}")
        return []


def get_broadcast_count() -> dict:
    col = _col("broadcast")
    if col is None:
        return {"total": 0, "private": 0, "groups": 0}
    try:
        total   = col.count_documents({})
        private = col.count_documents({"type": "private"})
        groups  = col.count_documents({"type": "group"})
        return {"total": total, "private": private, "groups": groups}
    except Exception as e:
        logger.error(f"[DB] get_broadcast_count: {e}")
        return {"total": 0, "private": 0, "groups": 0}


def remove_broadcast_chat(chat_id: int) -> None:
    col = _col("broadcast")
    if col is None:
        return
    try:
        col.delete_one({"_id": int(chat_id)})
    except Exception as e:
        logger.error(f"[DB] remove_broadcast_chat: {e}")


# ── Chat Effects (speed / bass / effects_on) ───────────────────────────────────

def save_chat_effects(chat_id: int, speed: float, bass: int, enabled: bool) -> None:
    """Save current effect settings for a chat to MongoDB."""
    col = _col("chat_effects")
    if col is None:
        return
    try:
        col.update_one(
            {"_id": chat_id},
            {"$set": {
                "_id":     chat_id,
                "speed":   speed,
                "bass":    bass,
                "enabled": enabled,
            }},
            upsert=True,
        )
    except Exception as e:
        logger.error(f"[DB] save_chat_effects: {e}")


def load_chat_effects(chat_id: int) -> dict:
    """Load effect settings for a chat. Returns defaults if not found."""
    col = _col("chat_effects")
    if col is None:
        return {"speed": 1.0, "bass": 0, "enabled": False}
    try:
        doc = col.find_one({"_id": chat_id})
        if doc:
            return {
                "speed":   doc.get("speed",   1.0),
                "bass":    doc.get("bass",     0),
                "enabled": doc.get("enabled",  False),
            }
    except Exception as e:
        logger.error(f"[DB] load_chat_effects: {e}")
    return {"speed": 1.0, "bass": 0, "enabled": False}


def delete_chat_effects(chat_id: int) -> None:
    """Remove effect settings for a chat."""
    col = _col("chat_effects")
    if col is None:
        return
    try:
        col.delete_one({"_id": chat_id})
    except Exception as e:
        logger.error(f"[DB] delete_chat_effects: {e}")
