# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

from ShizuMusic.utils.permissions import is_user_authorized
from ShizuMusic.utils.decorators import register_block_middleware

__all__ = [
    "is_user_authorized",
    "register_block_middleware",
]
