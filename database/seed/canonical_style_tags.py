"""
Collapse caption + tagger output to a single DB style slug (six UI styles).
Mirrors supabase/migrations/014_reference_images_style_slug_from_caption.sql intent
so local seed inserts do not violate reference_images_style_tags_one_of_six.
"""

from __future__ import annotations

# (slug, tie_rank, keywords) — lower tie_rank wins on equal earliest match (japandi first).
_SLUG_KEYWORDS: list[tuple[str, int, list[str]]] = [
    (
        "japandi",
        1,
        [
            "japandi",
            "wabi-sabi",
            "wabisabi",
            "wabi sabi",
            "japanese minimal",
            "zen minimal",
            "japanese",
        ],
    ),
    (
        "scandinavian",
        2,
        [
            "scandinavian",
            "scandi",
            "nordic",
            "hygge",
            "swedish",
            "danish design",
            "danish",
            "minimalist",
        ],
    ),
    (
        "midcentury",
        3,
        [
            "midcentury",
            "mid-century-modern",
            "mid century modern",
            "mid-century",
            "mid century",
            "mcm",
            "teak",
            "eames",
            "saarinen",
        ],
    ),
    (
        "traditional",
        4,
        [
            "traditional",
            "classic",
            "neo-contemporary",
            "farmhouse",
            "victorian",
            "ornate",
            "colonial",
            "baroque",
        ],
    ),
    (
        "industrial",
        5,
        [
            "industrial",
            "brutalist",
            "concrete",
            "exposed brick",
            "steel",
            "loft",
            "warehouse",
            "futuristic",
        ],
    ),
    (
        "boho",
        6,
        [
            "boho",
            "bohemian",
            "eclectic",
            "rustic",
            "rattan",
            "wicker",
            "macrame",
            "biophilic",
            "modern-ethnic-fusion",
        ],
    ),
]


def _haystack(caption: str, tags: list[str]) -> str:
    cap = (caption or "").lower().strip()
    tail = " ".join((t or "").lower().strip() for t in tags)
    return f"{cap} {tail}".strip()


def _from_caption_and_tags(caption: str, tags: list[str]) -> str | None:
    h = _haystack(caption, tags)
    if not h:
        return None
    best_pos = 10**9
    best_rank = 99
    best_slug: str | None = None
    for slug, rank, kws in _SLUG_KEYWORDS:
        minp: int | None = None
        for kw in kws:
            p = h.find(kw)
            if p >= 0 and (minp is None or p < minp):
                minp = p
        if minp is not None:
            if minp < best_pos or (minp == best_pos and rank < best_rank):
                best_pos, best_rank, best_slug = minp, rank, slug
    return best_slug


def _from_tags_only(tags: list[str]) -> str:
    """Same alias collapse order as migration 013 (first matching tag wins)."""
    for t in tags:
        tl = (t or "").lower().strip()
        if tl in ("scandinavian", "scandi", "nordic"):
            return "scandinavian"
        if tl in ("japandi", "japanese"):
            return "japandi"
        if tl in ("midcentury", "mid-century-modern", "mid century modern", "mcm"):
            return "midcentury"
        if tl in ("traditional", "classic", "neo-contemporary", "farmhouse"):
            return "traditional"
        if tl in ("industrial", "loft", "futuristic"):
            return "industrial"
        if tl in ("boho", "bohemian", "eclectic", "rustic", "modern-ethnic-fusion", "biophilic"):
            return "boho"
        if tl in ("minimalist",):
            return "scandinavian"
    return "scandinavian"


def pick_canonical_style_tags_singleton(caption: str, tags: list[str] | None) -> list[str]:
    """
    Return exactly one-element text[] for reference_images.style_tags.
    Default slug when nothing matches: scandinavian (matches migration 014).
    """
    tags = [x for x in (tags or []) if x]
    hit = _from_caption_and_tags(caption, tags)
    if hit:
        return [hit]
    if not tags:
        return ["scandinavian"]
    if len(tags) == 1:
        return [_from_tags_only(tags)]
    return [_from_tags_only(tags)]
