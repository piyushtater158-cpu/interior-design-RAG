#!/usr/bin/env python3
"""Verify Agent-3-parity prompt assembly in generate_edit workflow."""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
N8N_DIR = PROJECT / "n8n"
EDIT_WF_PATH = N8N_DIR / "workflows" / "generate_edit.json"
PROMPTS_DIR = N8N_DIR / "prompts"

BUILD_NODE = "Build Gemini edit request"
FETCH_MODEL_NODE = "Fetch image_model"
ATTACH_NODE = "Attach parent binary"


def local_edit_workflow_checks() -> dict[str, bool]:
    wf = json.loads(EDIT_WF_PATH.read_text(encoding="utf-8-sig"))
    build = next(n for n in wf["nodes"] if n["name"] == BUILD_NODE)
    cfg = next(n for n in wf["nodes"] if n["name"] == "Config")
    js = build["parameters"]["jsCode"]
    cfg_js = cfg["parameters"]["jsCode"]
    conn = wf["connections"]

    fetch_png_next = (
        conn.get("Fetch parent PNG", {}).get("main", [[]])[0][0].get("node")
        == FETCH_MODEL_NODE
    )
    fetch_model_next = (
        conn.get(FETCH_MODEL_NODE, {}).get("main", [[]])[0][0].get("node") == ATTACH_NODE
    )
    attach_next = (
        conn.get(ATTACH_NODE, {}).get("main", [[]])[0][0].get("node") == BUILD_NODE
    )

    return {
        "gemini_image_model": "normalizeImageModel" in js
        and "gemini-3.1-flash-image-preview" in js,
        "no_flux_model": "black-forest-labs/flux.2-max" not in js,
        "modalities_image_text": "modalities: ['image', 'text']" in js,
        "image_size_1k": "image_size: '1K'" in js,
        "fetch_image_model_node": any(n["name"] == FETCH_MODEL_NODE for n in wf["nodes"]),
        "attach_parent_binary_node": any(n["name"] == ATTACH_NODE for n in wf["nodes"]),
        "fetch_parent_to_fetch_model": fetch_png_next,
        "fetch_model_to_attach": fetch_model_next,
        "attach_to_build": attach_next,
        "build_reads_input_binary": "inputItem.binary" in js,
        "door_clearance_block": "DOOR_CLEARANCE_BLOCK" in js and "DOOR CLEARANCE" in js,
        "edit_nano_banana_preamble": "EDIT_NANO_BANANA_PREAMBLE_BLOCK" in js,
        "edit_agent3_mandate": "EDIT_AGENT3_MANDATE_BLOCK" in js,
        "edit_design_principles": "EDIT_DESIGN_PRINCIPLES_BLOCK" in js,
        "edit_single_element_rule": "EDIT_SINGLE_ELEMENT_RULE_BLOCK" in js,
        "narrow_edit_instruction": "narrowEditInstruction" in js,
        "frozen_scene_header": "FROZEN SCENE" in js,
        "primary_edit_header": "PRIMARY EDIT" in js,
        "build_spatial_req": "buildSpatialReq" in js,
        "parse_storage_constraints": "parseStorageConstraints" in js,
        "parse_window_count": "parseWindowCountFromCriteria" in js,
        "strip_prepended_dupes": "stripPrependedConstraintBlocks" in js,
        "extract_prompt_block": "extractPromptBlock" in js,
        "window_count_block": "WINDOW COUNT LOCK" in js,
        "prompt_debug": "_prompt_debug" in js,
        "architectural_lock": "ARCHITECTURAL_LOCK_BLOCK" in js,
        "canvas_hard_lock": "canvas_hard_lock" in js and "CANVAS HARD LOCK" in js and "WIDTH LOCK" in js,
        "no_frame_lock_block": "FRAME_LOCK_BLOCK" not in js,
        "no_frame_lock_in_prompt_parts": "FRAME_LOCK_BLOCK," not in js,
        "structure_lock_persist": "EDIT (apply only this change)" in js,
        "config_no_process_env": "process.env" not in cfg_js and "$env" not in cfg_js,
        "generate_node_gemini": any(n["name"] == "Generate image (Gemini)" for n in wf["nodes"]),
        "openrouter_credential_linked": any(
            (n.get("credentials") or {}).get("openRouterApi", {}).get("name") == "OpenRouter account"
            for n in wf["nodes"]
            if n["name"] == "Generate image (Gemini)"
        ),
        "extract_refs_build_gemini": "$('Build Gemini edit request')" in next(
            n["parameters"]["jsCode"]
            for n in wf["nodes"]
            if n["name"] == "Extract output PNG"
        ),
        "respond_backend_gemini": any(
            "backend_id:    'gemini'" in n["parameters"].get("responseBody", "")
            for n in wf["nodes"]
            if n["name"] == "Respond 200"
        ),
    }


def prompt_files_exist() -> dict[str, bool]:
    names = (
        "edit_agent3_mandate.txt",
        "edit_design_principles.txt",
        "edit_single_element_rule.txt",
        "edit_practical_feasibility.txt",
        "edit_nano_banana_preamble.txt",
        "architectural_lock.txt",
    )
    return {f"prompt_file_{n}": (PROMPTS_DIR / n).is_file() for n in names}


def main() -> int:
    files = prompt_files_exist()
    for k, v in files.items():
        print(f"{'OK' if v else 'FAIL'}  {k}")

    checks = {**files, **local_edit_workflow_checks()}
    for k, v in checks.items():
        if not k.startswith("prompt_file_"):
            print(f"{'OK' if v else 'FAIL'}  {k}")

    if not all(checks.values()):
        failed = [k for k, v in checks.items() if not v]
        print(f"FAILED: {', '.join(failed)}")
        return 1
    print("All edit prompt pipeline checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
