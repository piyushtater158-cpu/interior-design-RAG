"""
Collapse caption + tagger room + detected_objects to one canonical room_type string.
Matches supabase/migrations/015_reference_images_canonical_room_type.sql (six UI rooms).
"""

from __future__ import annotations

_ROOM_KEYWORDS: list[tuple[str, int, list[str]]] = [
    (
        "bedroom",
        1,
        [
            "bedroom",
            "master bedroom",
            "guest bedroom",
            "guest room",
            "nightstand",
            "wardrobe",
            "dresser",
            "headboard",
        ],
    ),
    ("kids room", 2, ["kids room", "nursery", "playroom", "toddler", "crib", "bunk bed"]),
    ("dining room", 3, ["dining room", "banquette", "breakfast nook", "dining table"]),
    (
        "kitchen",
        4,
        [
            "kitchen",
            "backsplash",
            "pantry",
            "range hood",
            "cooktop",
            "countertop",
            "kitchen island",
        ],
    ),
    ("mandir", 5, ["mandir", "puja", "altar", "shrine"]),
    (
        "living room",
        6,
        [
            "living room",
            "living area",
            "family room",
            "great room",
            "lounge",
            "sofa",
            "sectional",
            "tv wall",
            "media wall",
            "study room",
            "hallway",
            "corridor",
        ],
    ),
]

_ALLOWED = frozenset(
    {"bedroom", "kids room", "dining room", "kitchen", "mandir", "living room"}
)


def _haystack(caption: str, room: str, objects: list[str] | None) -> str:
    parts = [
        (caption or "").lower().strip(),
        (room or "").lower().strip(),
        " ".join((o or "").lower().strip() for o in (objects or [])),
    ]
    return " ".join(p for p in parts if p).strip()


def _from_caption_room_objects(caption: str, room: str, objects: list[str] | None) -> str | None:
    h = _haystack(caption, room, objects)
    if not h:
        return None
    best_pos = 10**9
    best_rank = 99
    best_slug: str | None = None
    for slug, rank, kws in _ROOM_KEYWORDS:
        minp: int | None = None
        for kw in kws:
            p = h.find(kw)
            if p >= 0 and (minp is None or p < minp):
                minp = p
        if minp is not None:
            if minp < best_pos or (minp == best_pos and rank < best_rank):
                best_pos, best_rank, best_slug = minp, rank, slug
    return best_slug


def _from_room_string_only(room: str) -> str:
    rl = " ".join((room or "").lower().split())
    if rl == "bedroom":
        return "bedroom"
    if rl in ("kids room", "kids_room", "nursery"):
        return "kids room"
    if rl in ("dining room", "dining"):
        return "dining room"
    if rl == "kitchen":
        return "kitchen"
    if rl == "mandir":
        return "mandir"
    if rl in (
        "living room",
        "living",
        "lounge",
        "living area",
        "study room",
        "study",
        "hallway",
        "hall",
        "unknown",
    ):
        return "living room"
    return "living room"


def pick_canonical_room_type(
    caption: str,
    room_type: str,
    detected_objects: list[str] | None = None,
) -> str:
    """
    Return one of: bedroom, kids room, dining room, kitchen, mandir, living room.
    Default: living room (matches migration 015).
    """
    hit = _from_caption_room_objects(caption, room_type, detected_objects)
    if hit:
        return hit
    r = _from_room_string_only(room_type)
    if r in _ALLOWED:
        return r
    return "living room"
