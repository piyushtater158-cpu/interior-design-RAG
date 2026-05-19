#!/usr/bin/env python3
"""Replay Parse Agent 1 prompt extraction on historical execution Agent 1 outputs."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_prompt_pipeline import extract_prompt_block_python

N8N_DIR = Path(__file__).resolve().parents[1]

OPENING_WALL_RE = re.compile(
    r"(?:entry\s+)?door[^\n]{0,80}(left|right|back|front)\s+wall|"
    r"windows?[^\n]{0,80}(left|right|back|front)\s+wall|"
    r"window\s+count:\s*\d+",
    re.I,
)


def agent1_content_from_exec(path: Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    blob = json.dumps(data)
    for pat in (
        r'"content":\s*"((?:\\.|[^"\\])*)"\s*,\s*"role":\s*"assistant"',
        r'"role":\s*"assistant"\s*,\s*"content":\s*"((?:\\.|[^"\\])*)"',
    ):
        m = re.search(pat, blob)
        if m and "===CRITERIA===" in m.group(1):
            raw = m.group(1)
            return raw.encode().decode("unicode_escape")
    raise RuntimeError(f"no Agent 1 content in {path.name}")


def main() -> None:
    for name in ("exec_1503_full.json", "exec_1512_full.json", "exec_1473_full.json"):
        path = N8N_DIR / name
        if not path.exists():
            print(f"SKIP {name} (missing)")
            continue
        content = agent1_content_from_exec(path)
        parsed = extract_prompt_block_python(content)
        assert parsed, f"{name}: no prompt extracted"
        assert parsed.startswith("A fully furnished") or re.search(
            r"image\s*1\s+is\s+authoritative", parsed, re.I
        ), f"{name}: wrong prompt start: {parsed[:80]!r}"
        assert "is the authoritative" not in parsed, name
        if OPENING_WALL_RE.search(parsed):
            print(f"WARN {name}: legacy run still has verbalized openings in PROMPT")
        else:
            print(f"OK  {name} -> {len(parsed)} chars, no verbalized opening walls")


if __name__ == "__main__":
    main()
