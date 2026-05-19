#!/usr/bin/env python3
"""Audit n8n execution for opening/door constraint pipeline."""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
N8N_BASE = "https://n8n.srv1649259.hstgr.cloud/api/v1"


def api_key() -> str:
    for line in (PROJECT / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("N8N_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError("N8N_API_KEY missing")


def fetch_execution(exec_id: str) -> dict:
    req = urllib.request.Request(
        f"{N8N_BASE}/executions/{exec_id}?includeData=true",
        headers={"X-N8N-API-KEY": api_key()},
    )
    return json.loads(urllib.request.urlopen(req).read())


def find_node_runs(data: dict, node_name: str) -> list[dict]:
    out: list[dict] = []
    run_data = data.get("data", {}).get("resultData", {}).get("runData", {})
    for name, runs in run_data.items():
        if name != node_name:
            continue
        for run in runs:
            for branch in run.get("data", {}).get("main", []) or []:
                for item in branch or []:
                    if item and item.get("json"):
                        out.append(item["json"])
    return out


def audit(exec_id: str) -> dict:
    ex = fetch_execution(exec_id)
    report: dict = {"execution_id": exec_id, "status": ex.get("status")}

    pa1 = find_node_runs(ex, "Parse Agent 1")
    if pa1:
        j = pa1[0]
        ap = j.get("agent_prompt") or ""
        report["parse_agent1"] = {
            "agent_prompt_len": len(ap),
            "agent_prompt_start": ap[:220],
            "opening_inventory": j.get("opening_inventory"),
            "spatial_req": j.get("spatial_req"),
            "_prompt_debug": j.get("_prompt_debug"),
            "has_exactly_n_windows": bool(re.search(r"exactly\s+\d+\s+window", ap, re.I)),
            "has_door_clearance": bool(
                re.search(r"door swing|door approach|blocking.*door|clear.*door", ap, re.I)
            ),
            "has_opening_inventory": "OPENING INVENTORY" in ap,
            "storage_constraints": j.get("storage_constraints"),
            "has_storage_constraints": "STORAGE CONSTRAINTS" in ap,
        }

    bg = find_node_runs(ex, "Build Gemini request")
    if bg:
        j = bg[0]
        dbg = j.get("_prompt_debug") or {}
        body = j.get("openrouter_body") or {}
        text = ""
        for part in (body.get("messages") or [{}])[0].get("content") or []:
            if isinstance(part, dict) and part.get("type") == "text":
                text = part.get("text") or ""
                break
        report["build_gemini"] = {
            **dbg,
            "generation_text_len": len(text),
            "has_opening_inventory_block": "OPENING INVENTORY" in text,
            "has_door_clearance_block": "DOOR CLEARANCE" in text or "door swing arc" in text.lower(),
            "has_window_count_block": bool(re.search(r"exactly\s+\d+\s+window", text, re.I)),
            "has_spatial_lock_from_photo": "SPATIAL LOCK FROM PHOTO" in text,
            "has_storage_block": "STORAGE CONSTRAINTS" in text,
            "has_cupboard_footprint_block": "CUPBOARD FOOTPRINT" in text,
        }

    pa2 = find_node_runs(ex, "Parse Agent 2")
    if pa2:
        report["parse_agent2"] = {
            "picked_reference_ids": pa2[0].get("picked_reference_ids"),
            "reference_count": pa2[0].get("reference_count"),
        }

    cp = find_node_runs(ex, "Check pool")
    if cp:
        pool_dbg = cp[0].get("_pool_debug") or {}
        report["check_pool"] = pool_dbg
        report["pool_filtered_storage"] = pool_dbg.get("pool_filtered_storage")

    pa1_info = report.get("parse_agent1") or {}
    bg_info = report.get("build_gemini") or {}
    brief_text = ""
    validate = find_node_runs(ex, "Validate body")
    if validate:
        brief_text = (validate[0].get("brief") or validate[0].get("user_brief") or "").lower()
    storage_re = re.compile(
        r"\b(cupboard|cupboards|wardrobe|wardrobes|closet|closets|armoire|"
        r"built-?in\s+storage|hidden\s+storage|storage\s+unit)\b",
        re.I,
    )
    user_wants_storage = bool(storage_re.search(brief_text))
    stor_constraints = pa1_info.get("storage_constraints")
    gen_text = ""
    if bg:
        body = bg[0].get("openrouter_body") or {}
        for part in (body.get("messages") or [{}])[0].get("content") or []:
            if isinstance(part, dict) and part.get("type") == "text":
                gen_text = part.get("text") or ""
                break
    opening_dupes = len(re.findall(r"OPENING INVENTORY \(non-negotiable\)", gen_text, re.I))
    storage_dupes = len(re.findall(r"STORAGE CONSTRAINTS \(non-negotiable\)", gen_text, re.I))
    report["quality_flags"] = {
        "storage_false_positive": bool(
            not user_wants_storage
            and (stor_constraints or pa1_info.get("has_storage_constraints"))
        ),
        "prompt_duplicate_opening_blocks": opening_dupes > 1,
        "prompt_duplicate_storage_blocks": storage_dupes > 1,
        "generation_prompt_len": bg_info.get("generation_prompt_len")
        or len(gen_text),
        "user_brief_has_storage_terms": user_wants_storage,
    }

    return report


def main() -> None:
    exec_id = sys.argv[1] if len(sys.argv) > 1 else "1512"
    report = audit(exec_id)
    out_path = PROJECT / "n8n" / f"audit_exec_{exec_id}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
