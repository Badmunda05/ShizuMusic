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



# chat_id -> queue list
chat_queues: dict[int, list] = {}


def get_queue(chat_id: int) -> list:
    return chat_queues.get(chat_id, [])


def add_to_queue(chat_id: int, song: dict) -> int:
    queue = chat_queues.setdefault(chat_id, [])
    queue.append(song)
    return len(queue)


def push_front(chat_id: int, song: dict) -> int:
    queue = chat_queues.setdefault(chat_id, [])
    queue.insert(0, song)
    return len(queue)


def pop_current(chat_id: int) -> dict | None:
    queue = chat_queues.get(chat_id)

    if not queue:
        return None

    return queue.pop(0)


def remove_from_queue(chat_id: int, index: int) -> dict | None:
    queue = chat_queues.get(chat_id)

    if not queue:
        return None

    if index < 0 or index >= len(queue):
        return None

    return queue.pop(index)


def peek_current(chat_id: int) -> dict | None:
    queue = chat_queues.get(chat_id)

    if not queue:
        return None

    return queue[0]


def peek_next(chat_id: int) -> dict | None:
    queue = chat_queues.get(chat_id)

    if not queue or len(queue) < 2:
        return None

    return queue[1]


def clear_queue(chat_id: int) -> list:
    return chat_queues.pop(chat_id, [])


def queue_size(chat_id: int) -> int:
    return len(chat_queues.get(chat_id, []))


def is_empty(chat_id: int) -> bool:
    return queue_size(chat_id) == 0
