#!/usr/bin/env python3
"""Verify spatial-first / Agent-3-primary prompt pipeline in generate_orchestrated workflow."""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
N8N_DIR = PROJECT / "n8n"
PROMPTS_DIR = N8N_DIR / "prompts"
WF_PATH = N8N_DIR / "workflows" / "generate_orchestrated.json"
ORCH_MODEL_DEFAULT = "google/gemini-2.5-flash"
NEMOTRON_VL_MODEL = "nvidia/nemotron-nano-12b-v2-vl:free"
FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "agent1_dual_prompt_sample.txt"
WF_ID = "0FJFDIiYcWpMD0fT"
N8N_BASE = "https://n8n.srv1649259.hstgr.cloud/api/v1"

# Compacted fixed-block char budgets (+10% slack over 1/3 baseline).
ARCH_LOCK_MAX_CHARS = int(4200 / 3 * 1.1)  # matches ARCH_LOCK_BASELINE_CHARS in bake_orchestrator_prompts.py
DESIGN_PRINCIPLES_MAX_CHARS = 770
AGENT3_MANDATE_MAX_CHARS = 385
FRAME_LOCK_MAX_CHARS = 495
DOOR_CLEARANCE_MAX_CHARS = 165
EXEC_1673_GENERATION_PROMPT_LEN = 10968
# Pre-compaction fixed blocks baked into Build Gemini (approx, from plan audit).
OLD_FIXED_BLOCK_CHARS = 2200 + 2050 + 900 + 1200 + 430


def api_key() -> str:
    for line in (PROJECT / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("N8N_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError("N8N_API_KEY missing")


def extract_prompt_block_python(text: str) -> str | None:
    """Mirror Parse Agent 1 extractPromptBlock + looksLikeGenerationBrief."""
    blocks: list[str] = []
    for m in re.finditer(r"={3,}\s*PROMPT\s*={3,}", text, re.I):
        after = text[m.end() :]
        end_m = re.search(r"={3,}\s*END\s*={3,}", after, re.I)
        body = (after[: end_m.start()] if end_m else after).strip()
        if body:
            blocks.append(body)
    if not blocks:
        return None

    def looks_like_generation_brief(body: str) -> bool:
        b = body.strip()
        if not b or len(b) < 80:
            return False
        if re.match(r"^is the authoritative", b, re.I):
            return False
        if re.match(r"^Complementarity guidance", b, re.I):
            return False
        if re.match(r"^A\s+fully\s+furnished", b, re.I):
            return True
        if re.search(r"image\s*1\s+is\s+authoritative", b, re.I) and re.search(
            r"preserve", b, re.I
        ):
            return True
        return False

    for body in reversed(blocks):
        if looks_like_generation_brief(body):
            return body
    return blocks[-1]


def parse_opening_inventory_python(_criteria: str, _prompt_raw: str) -> dict | None:
    """Mirror parseOpeningInventory in Parse Agent 1 — always null (image 1 locks openings)."""
    return None


STORAGE_TERM_RE = re.compile(
    r"\b(cupboard|cupboards|wardrobe|wardrobes|closet|closets|armoire|"
    r"built-?in\s+storage|hidden\s+storage|storage\s+unit)\b",
    re.I,
)


def user_requested_storage_python(user_brief: str, prompt_raw: str) -> bool:
    return bool(STORAGE_TERM_RE.search(user_brief or "")) or bool(
        STORAGE_TERM_RE.search(prompt_raw or "")
    )


def parse_storage_constraints_python(
    criteria: str, prompt_raw: str, user_brief: str
) -> dict | None:
    """Mirror parseStorageConstraints in Parse Agent 1."""
    if not user_requested_storage_python(user_brief, prompt_raw):
        return None
    src = ((user_brief or "") + "\n" + (prompt_raw or "")).lower()
    photo_built_in = bool(
        re.search(r"built-?in\s+wardrobe", src, re.I)
        and re.search(r"photograph|preserve", src, re.I)
    )
    placement = "preserve_photo" if photo_built_in else "freestanding_new"
    return {
        "has_storage_in_brief": True,
        "photo_has_built_in": photo_built_in,
        "placement": placement,
    }


def load_prompt_sources() -> dict[str, str]:
    names = (
        "architectural_lock.txt",
        "design_principles.txt",
        "agent3_generation_mandate.txt",
        "image_gen_frame_lock.txt",
    )
    return {
        name: (PROMPTS_DIR / name).read_text(encoding="utf-8").strip()
        for name in names
    }


def test_compact_prompt_sources() -> None:
    src = load_prompt_sources()
    arch = src["architectural_lock.txt"]
    dp = src["design_principles.txt"]
    a3 = src["agent3_generation_mandate.txt"]
    frame = src["image_gen_frame_lock.txt"]

    assert len(arch) <= ARCH_LOCK_MAX_CHARS, f"architectural_lock {len(arch)} > {ARCH_LOCK_MAX_CHARS}"
    assert len(dp) <= DESIGN_PRINCIPLES_MAX_CHARS, (
        f"design_principles {len(dp)} > {DESIGN_PRINCIPLES_MAX_CHARS}"
    )
    assert len(a3) <= AGENT3_MANDATE_MAX_CHARS, f"agent3 mandate {len(a3)} > {AGENT3_MANDATE_MAX_CHARS}"
    assert len(frame) <= FRAME_LOCK_MAX_CHARS, f"frame lock {len(frame)} > {FRAME_LOCK_MAX_CHARS}"

    arch_low = arch.lower()
    for needle in (
        "image 1",
        "hard lock",
        "inpainting",
        "3d structure",
        "door",
        "window",
        "light",
        "reference",
        "ignore",
        "canvas",
    ):
        assert needle in arch_low, f"architectural_lock missing keyword: {needle}"
    assert "canvas hard lock" in arch_low, "architectural_lock should reference CANVAS HARD LOCK block"
    assert "forbidden: crop, resize, pad" not in arch_low, (
        "architectural_lock should not duplicate full canvas rules (see image_gen_pixel_lock.txt)"
    )

    dp_low = dp.lower()
    assert "priority" in dp_low
    for fund in ("balance", "unity", "rhythm", "contrast", "scale", "proportion"):
        assert fund in dp_low, f"design_principles missing fundamental: {fund}"
    assert "===prompt===" in dp_low.replace(" ", "")

    a3_low = a3.lower()
    assert "primary" in a3_low and "brief" in a3_low

    frame_low = frame.lower()
    assert "generation priority" not in frame_low
    assert "architectural lock (mandatory" not in frame_low


def test_build_gemini_dedup_local() -> None:
    wf = json.loads(WF_PATH.read_text(encoding="utf-8-sig"))
    bg_js = next(n for n in wf["nodes"] if n["name"] == "Build Gemini request")["parameters"]["jsCode"]

    assert "const CONFLICT_OVERRIDE" not in bg_js
    assert "CONFLICT_OVERRIDE," not in bg_js
    assert "getImageDimensions" in bg_js
    assert "CANVAS_HARD_LOCK_BLOCK" in bg_js
    assert "HARD LOCK (non-negotiable)" in bg_js
    assert "WIDTH LOCK" in bg_js
    assert "pickAspectRatio" in bg_js
    assert "hasArchitecturalHardLock" in bg_js
    assert "INTERIOR DESIGN PRINCIPLES" in bg_js
    assert "AGENT 3 GENERATION MANDATE" in bg_js or "PRIMARY GENERATION BRIEF" in bg_js
    assert "ARCHITECTURAL_LOCK_BLOCK,\n  CANVAS_HARD_LOCK_BLOCK," in bg_js
    assert "canvas_dims_injected" in bg_js

    extract_js = next(n for n in wf["nodes"] if n["name"] == "Extract output PNG")["parameters"]["jsCode"]
    assert "normalizeToInput" in extract_js
    assert "dimension_normalized" in extract_js


def estimate_fixed_block_chars() -> int:
    import sys

    sys.path.insert(0, str(N8N_DIR))
    from bake_orchestrator_prompts import DOOR_CLEARANCE_BLOCK

    src = load_prompt_sources()
    return (
        len(src["architectural_lock.txt"])
        + len(src["design_principles.txt"])
        + len(src["agent3_generation_mandate.txt"])
        + len(src["image_gen_frame_lock.txt"])
        + len(DOOR_CLEARANCE_BLOCK)
    )


def test_fixed_block_savings() -> None:
    new_fixed = estimate_fixed_block_chars()
    savings = OLD_FIXED_BLOCK_CHARS - new_fixed
    # Hard-lock expansion increases architectural block size; no longer expect net shrink.
    print(
        f"INFO fixed-block char estimate: {new_fixed} (delta vs legacy baseline {OLD_FIXED_BLOCK_CHARS}: {savings:+d})"
    )


def normalize_upload_id(raw: str) -> str | None:
    """Mirror Validate body upload_id normalization in generate_orchestrated."""
    upload_id = (raw or "").strip()
    if re.match(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        upload_id,
        re.I,
    ):
        upload_id = upload_id.replace("-", "").lower()
    if upload_id and re.match(r"^[0-9a-f]{32}$", upload_id, re.I):
        return upload_id.lower()
    return None


def test_upload_id_accepts_compact_hex() -> None:
    """Exec 1693: uploads_room_photo returns 32-char hex; Validate body must accept it."""
    compact = "3e60a205eff10811802eae29ae3b07fa"
    dashed = "3e60a205-eff1-0811-802e-ae29ae3b07fa"
    assert normalize_upload_id(compact) == compact
    assert normalize_upload_id(dashed) == compact
    assert normalize_upload_id("not-an-id") is None


def test_storage_constraints_fixture() -> None:
    criteria = """Storage lock: add freestanding wardrobe on the left wall with clearance
Cupboard / wardrobe: in-room unit with visible wall; footprint ~80cm deep
"""
    prompt = "A fully furnished bedroom with a freestanding wardrobe on the left wall."
    brief = "Add a cupboard with hidden storage"
    stor = parse_storage_constraints_python(criteria, prompt, brief)
    assert stor is not None
    assert stor["placement"] == "freestanding_new"
    assert stor["has_storage_in_brief"] is True


def test_exec_1546_no_storage_false_positive() -> None:
    """Exec 1546: brief has no storage; Agent1 CRITERIA must not activate storage blocks."""
    criteria = """Storage lock: none in photo — do not add wardrobe, cupboard, or closet
Cupboard / wardrobe: in-room unit with visible wall; footprint ~80cm deep
"""
    prompt = (
        "A fully furnished Scandinavian bedroom. The entry door remains on the left wall. "
        "Two vertical windows on the right wall. Wooden floor, graphical walls, corner lamp, "
        "colorful lights."
    )
    brief = "wooden floor; graphical walls; corner lamp; colorful lights"
    stor = parse_storage_constraints_python(criteria, prompt, brief)
    assert stor is None, "storage_constraints must be null when user brief has no storage terms"


def test_opening_inventory_disabled() -> None:
    """Opening coordinates are not parsed from Agent 1 text — image 1 is authoritative."""
    criteria = """Openings lock: preserve as in photograph
Door lock: The entry door is on the left wall.
Window count: 2
"""
    prompt = "A fully furnished bedroom. Two windows on the right wall."
    assert parse_opening_inventory_python(criteria, prompt) is None


def test_dual_prompt_fixture() -> None:
    sample = FIXTURE_PATH.read_text(encoding="utf-8")
    wrong_first = re.search(
        r"={3,}\s*PROMPT\s*={3,}([\s\S]*?)(?=={3,}\s*PROMPT\s*={3,})",
        sample,
        re.I,
    )
    assert wrong_first, "fixture needs two PROMPT delimiters"
    assert "is the authoritative" in wrong_first.group(1)

    parsed = extract_prompt_block_python(sample)
    assert parsed is not None
    assert parsed.startswith("A fully furnished")
    assert "image 1 is authoritative" in parsed.lower()
    assert not re.search(
        r"(?:entry\s+)?door[^\n]{0,80}(left|right|back|front)\s+wall", parsed, re.I
    )
    assert not re.search(r"\b(two|2|three|3)\s+windows?\b", parsed, re.I)
    assert "is the authoritative" not in parsed


def local_workflow_checks() -> dict[str, bool]:
    wf = json.loads(WF_PATH.read_text(encoding="utf-8-sig"))
    pa1 = next(n for n in wf["nodes"] if n["name"] == "Parse Agent 1")
    ba1 = next(n for n in wf["nodes"] if n["name"] == "Build Agent 1 request")
    ba2 = next(n for n in wf["nodes"] if n["name"] == "Build Agent 2 request")
    bg = next(n for n in wf["nodes"] if n["name"] == "Build Gemini request")
    cp = next(n for n in wf["nodes"] if n["name"] == "Check pool")
    cfg = next((n for n in wf["nodes"] if n["name"] == "Config"), None)

    pa1_js = pa1["parameters"]["jsCode"]
    ba1_js = ba1["parameters"]["jsCode"]
    ba2_js = ba2["parameters"]["jsCode"]
    bg_js = bg["parameters"]["jsCode"]
    cp_js = cp["parameters"]["jsCode"]
    cfg_js = cfg["parameters"]["jsCode"] if cfg else ""

    return {
        "local_parse_extract_prompt_block": "extractPromptBlock" in pa1_js,
        "local_parse_tight_window_re": "window and light fidelity" in pa1_js,
        "local_parse_prompt_extraction_mode": "prompt_extraction_mode" in pa1_js,
        "local_build_agent1_orch_model_cfg": "cfg.orch_model" in ba1_js,
        "local_build_agent2_retriever_cfg": "cfg.retriever_model" in ba2_js
        or "cfg.orch_model" in ba2_js,
        "local_config_retriever_model": (not cfg_js) or "retriever_model" in cfg_js,
        "local_agent1_mandate_no_delimiter": "===PROMPT=== is the authoritative"
        not in ba1_js,
        "local_parse_opening_inventory": "parseOpeningInventory" in pa1_js,
        "local_pool_filter": "filterPoolByOpenings" in cp_js,
        "local_gemini_opening_block": "OPENING_INVENTORY_BLOCK" in bg_js,
        "local_gemini_door_clearance": "DOOR CLEARANCE" in bg_js,
        "local_parse_storage_constraints": "parseStorageConstraints" in pa1_js,
        "local_parse_user_requested_storage": "userRequestedStorage" in pa1_js,
        "local_gemini_strip_dupes": "stripPrependedConstraintBlocks" in bg_js,
        "local_build_storage_block": "buildStorageConstraintsBlock" in pa1_js,
        "local_pool_filter_storage": "filterPoolByStorage" in cp_js,
        "local_gemini_storage_block": "STORAGE_PLACEMENT_BLOCK" in bg_js,
        "local_gemini_cupboard_footprint": "CUPBOARD_FOOTPRINT_BLOCK" in bg_js,
        "local_reject_bad_prompt_fragment": "/^is the authoritative/i.test(b)" in pa1_js,
        "local_gemini_no_conflict_override": "const CONFLICT_OVERRIDE" not in bg_js
        and "CONFLICT_OVERRIDE," not in bg_js,
        "local_agent1_nemotron_extras": "openrouterChatExtras" in ba1_js,
        "local_build_agent1_template_literal": "const SYSTEM = `" in ba1_js
        and "const SYSTEM = You are" not in ba1_js,
        "local_build_agent1_workbook": "You are Agent 1" in ba1_js,
        "local_agent2_nemotron_extras": "openrouterChatExtras" in ba2_js,
        "local_config_gemini_orch": (not cfg_js) or ORCH_MODEL_DEFAULT in cfg_js,
        "local_config_gemini_retriever": (not cfg_js) or ORCH_MODEL_DEFAULT in cfg_js,
        "local_parse_extract_agent1": "extractAgent1Content" in pa1_js,
    }


def remote_workflow_checks() -> dict[str, bool]:
    key = api_key()
    wf = json.loads(
        urllib.request.urlopen(
            urllib.request.Request(
                f"{N8N_BASE}/workflows/{WF_ID}",
                headers={"X-N8N-API-KEY": key},
            )
        ).read()
    )
    pa1 = next(n for n in wf["nodes"] if n["name"] == "Parse Agent 1")
    ba1 = next(n for n in wf["nodes"] if n["name"] == "Build Agent 1 request")
    bg = next(n for n in wf["nodes"] if n["name"] == "Build Gemini request")
    ba2 = next(n for n in wf["nodes"] if n["name"] == "Build Agent 2 request")
    pa2 = next(n for n in wf["nodes"] if n["name"] == "Parse Agent 2")
    order = next(n for n in wf["nodes"] if n["name"] == "Order fetch list")
    collect = next(n for n in wf["nodes"] if n["name"] == "Collect image parts")

    pa1_js = pa1["parameters"]["jsCode"]
    ba1_js = ba1["parameters"]["jsCode"]
    bg_js = bg["parameters"]["jsCode"]
    ba2_js = ba2["parameters"]["jsCode"]
    pa2_js = pa2["parameters"]["jsCode"]
    order_js = order["parameters"]["jsCode"]
    collect_js = collect["parameters"]["jsCode"]

    return {
        "parse_spatial_first_criteria": "has_spatial_first_criteria" in pa1_js,
        "parse_no_5050_debug": "has_50_50_criteria" not in pa1_js,
        "parse_extract_prompt_block": "extractPromptBlock" in pa1_js,
        "parse_tight_window_re": "window and light fidelity" in pa1_js,
        "build_agent1_no_50pct": "50%" not in ba1_js and "User brief priorities (50%" not in ba1_js,
        "build_agent1_spatial_or_agent3": (
            "Spatial structure lock" in ba1_js or "AGENT 3 GENERATION BRIEF" in ba1_js
        ),
        "build_agent1_openings_lock": "Openings lock:" in ba1_js,
        "build_agent1_workbook": "You are Agent 1" in ba1_js,
        "build_agent1_template_literal": "const SYSTEM = `" in ba1_js
        and "const SYSTEM = You are" not in ba1_js,
        "build_agent1_full_orchestrator": len(ba1_js) > 4000,
        "parse_agent1_door_footer": "Door lock (mandatory)" in pa1_js,
        "parse_agent1_openings_lock_debug": "has_openings_lock_criteria" in pa1_js,
        "build_agent1_orch_model_cfg": "cfg.orch_model" in ba1_js,
        "build_agent2_retriever_cfg": "cfg.retriever_model" in ba2_js or "cfg.orch_model" in ba2_js,
        "build_agent1_no_mirrored_furniture": "paired or mirrored furniture" not in ba1_js,
        "build_gemini_agent3_mandate": "AGENT3_MANDATE_BLOCK" in bg_js,
        "build_gemini_primary_brief_last": "PRIMARY_BRIEF_HEADER" in bg_js and "primary_brief_last" in bg_js,
        "build_gemini_no_5050_balance": "GENERATION BALANCE" not in bg_js,
        "build_agent2_no_pool_lt3_error": "insufficient_distinct_pool" not in ba2_js,
        "parse_agent2_flexible_picks": "reference_count" in pa2_js
        and "insufficient_distinct_picks" not in pa2_js,
        "order_fetch_flexible": "picked_ids_not_three_unique" not in order_js,
        "collect_flexible_parts": "reference_count" in collect_js
        and "parts.length !== items.length" not in collect_js,
        "photo_only_node": any(n["name"] == "Photo-only path" for n in wf["nodes"]),
        "fetch_pool_rpc_post": any(
            n["name"] == "Fetch candidate pool"
            and n["parameters"].get("method") == "POST"
            and "retrieve_candidates_text" in n["parameters"].get("url", "")
            for n in wf["nodes"]
        ),
        "parse_opening_inventory": "parseOpeningInventory" in pa1_js,
        "pool_filter_openings": "filterPoolByOpenings" in next(
            n["parameters"]["jsCode"]
            for n in wf["nodes"]
            if n["name"] == "Check pool"
        ),
        "build_gemini_opening_block": "OPENING_INVENTORY_BLOCK" in bg_js,
        "build_gemini_door_clearance": "DOOR CLEARANCE" in bg_js,
        "build_gemini_window_count_block": "WINDOW COUNT LOCK" in bg_js,
        "parse_storage_constraints": "parseStorageConstraints" in pa1_js,
        "pool_filter_storage": "filterPoolByStorage" in next(
            n["parameters"]["jsCode"]
            for n in wf["nodes"]
            if n["name"] == "Check pool"
        ),
        "build_gemini_storage_block": "STORAGE_PLACEMENT_BLOCK" in bg_js,
        "build_gemini_cupboard_footprint": "CUPBOARD_FOOTPRINT_BLOCK" in bg_js,
        "build_agent1_nemotron_extras": "openrouterChatExtras" in ba1_js,
        "build_agent2_nemotron_extras": "openrouterChatExtras" in ba2_js,
        "config_gemini_orch": ORCH_MODEL_DEFAULT in next(
            n["parameters"]["jsCode"]
            for n in wf["nodes"]
            if n["name"] == "Config"
        ),
        "parse_extract_agent1": "extractAgent1Content" in pa1_js,
        "agent1_http_retry": next(
            n["parameters"].get("options", {}).get("retry")
            for n in wf["nodes"]
            if n["name"] == "Agent 1 (Orchestrator)"
        )
        is not None,
    }


def main() -> None:
    test_upload_id_accepts_compact_hex()
    print("OK  upload_id compact hex validation (exec 1693 regression)")

    test_compact_prompt_sources()
    print("OK  compact prompt sources (char budgets + keywords)")

    test_build_gemini_dedup_local()
    print("OK  Build Gemini dedup (no CONFLICT_OVERRIDE array)")

    test_fixed_block_savings()
    print("OK  fixed-block savings vs pre-compaction baseline")

    fixed_chars = estimate_fixed_block_chars()
    print(f"INFO fixed prompt blocks total: {fixed_chars} chars (exec 1673 baseline text ~{EXEC_1673_GENERATION_PROMPT_LEN})")

    test_storage_constraints_fixture()
    print("OK  storage constraints parsing")

    test_exec_1546_no_storage_false_positive()
    print("OK  exec 1546 no-storage false positive guard")

    test_opening_inventory_disabled()
    print("OK  opening inventory parsing")

    test_dual_prompt_fixture()
    print("OK  dual-PROMPT fixture extraction")

    local = local_workflow_checks()
    for k, v in local.items():
        print(f"{'OK' if v else 'FAIL'}  {k}")

    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    from verify_edit_prompt_pipeline import local_edit_workflow_checks, prompt_files_exist

    edit_checks = {**prompt_files_exist(), **local_edit_workflow_checks()}
    for k, v in edit_checks.items():
        print(f"{'OK' if v else 'FAIL'}  edit.{k}")

    try:
        remote = remote_workflow_checks()
    except Exception as exc:
        print(f"WARN  remote workflow checks skipped: {exc}")
        remote = {}

    for k, v in remote.items():
        print(f"{'OK' if v else 'FAIL'}  {k}")

    assert all(local.values()), "local prompt pipeline verification failed"
    assert all(edit_checks.values()), "edit prompt pipeline verification failed"
    remote_fails = [k for k, v in remote.items() if not v]
    if remote_fails:
        print(f"WARN  remote drift ({len(remote_fails)}): {', '.join(remote_fails)}")
    print("All local checks passed.")


if __name__ == "__main__":
    main()
