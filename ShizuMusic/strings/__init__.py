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
#
#  Language system
#  ----------------
#  Every user-facing string lives in strings/langs/<code>.yml as `key: "text"`.
#
#  Adding a language is just dropping a new file in — nothing else to touch:
#    1. Copy strings/langs/en.yml to strings/langs/<code>.yml
#       (<code> = the language code you want, e.g. "hi", "pa", "es").
#    2. Translate the values (leave the keys alone).
#    3. Add a top-level `name:` key — that's the label shown in /language.
#    That's it — this loader picks it up automatically on the next start,
#    no code change needed.
#
#  If a new file is missing some keys (a translation still in progress),
#  the English text is used for those keys instead of crashing/blank text.
#  If a file is broken or missing its `name:` key, it is skipped (logged),
#  the bot still boots, and everyone else keeps working.
# --------------------------------------------------------------------------------

import logging
import os
import re

import yaml

logger = logging.getLogger(__name__)

_LANGS_DIR = os.path.join(os.path.dirname(__file__), "langs")

# A language *code* is the file name without ".yml" — keep it to something
# sane (2-3 letters, optionally "-REGION") so it can't collide with real
# option/callback data elsewhere in the bot.
_CODE_RE = re.compile(r"^[a-z]{2,3}(-[a-z]{2,3})?$")

languages: dict = {}          # code -> {key: text, ...}
languages_present: dict = {}  # code -> display name (for the /language menu)

DEFAULT_LANG = "en"


def get_string(lang: str) -> dict:
    """Strings for `lang`, or English if it isn't loaded/valid."""
    return languages.get(lang) or languages[DEFAULT_LANG]


def _load_one(code: str, path: str) -> dict | None:
    try:
        with open(path, encoding="utf8") as f:
            data = yaml.safe_load(f) or {}
    except Exception as e:
        logger.warning(f"[strings] {code}.yml is not valid YAML, skipping: {e}")
        return None

    if not isinstance(data, dict) or not data.get("name"):
        logger.warning(
            f"[strings] {code}.yml has no top-level 'name:' key, skipping. "
            "(every language file needs one — see strings/langs/en.yml)"
        )
        return None

    return data


def _load_all() -> None:
    languages.clear()
    languages_present.clear()

    if not os.path.isdir(_LANGS_DIR):
        logger.error(f"[strings] langs directory missing: {_LANGS_DIR}")
        return

    # English loads first — it's the fallback every other language borrows
    # missing keys from, so it has to exist before we look at anything else.
    en_path = os.path.join(_LANGS_DIR, f"{DEFAULT_LANG}.yml")
    base = _load_one(DEFAULT_LANG, en_path) if os.path.exists(en_path) else None
    if base is None:
        logger.error("[strings] strings/langs/en.yml is missing or broken — "
                      "the bot needs this file to run.")
        base = {"name": "🇺🇸 English"}
    languages[DEFAULT_LANG] = base
    languages_present[DEFAULT_LANG] = base["name"]

    for filename in sorted(os.listdir(_LANGS_DIR)):
        if not filename.endswith(".yml"):
            continue

        code = filename[:-4]
        if code == DEFAULT_LANG:
            continue

        if not _CODE_RE.match(code):
            logger.warning(
                f"[strings] '{filename}' isn't a valid language code "
                "(expected 2-3 letters, e.g. 'hi.yml' or 'pa.yml'), skipping."
            )
            continue

        data = _load_one(code, os.path.join(_LANGS_DIR, filename))
        if data is None:
            continue

        # fill anything the translation hasn't gotten to yet with English
        for key, value in languages[DEFAULT_LANG].items():
            data.setdefault(key, value)

        languages[code] = data
        languages_present[code] = data["name"]


_load_all()
