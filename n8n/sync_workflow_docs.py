#!/usr/bin/env python3
"""
Sync WORKFLOW_SYSTEM.md node tables from the workflow JSON files.

How it works
------------
Each section in WORKFLOW_SYSTEM.md that corresponds to a workflow file is
bracketed by a pair of HTML comment markers:

    <!-- WFSYNC:workflow_stem:START -->
    ... auto-generated node table ...
    <!-- WFSYNC:workflow_stem:END -->

This script reads every *.json in n8n/workflows/, builds a node table for
each one by walking the execution graph, and replaces only the content
inside those markers.  Everything outside the markers — prose, headings,
examples — is left untouched.

Run manually:  python n8n/sync_workflow_docs.py
Triggered by:  Claude Code PostToolUse hook on Write/Edit
"""

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
WORKFLOWS_DIR = Path(__file__).parent / "workflows"
DOCS_FILE = Path(__file__).parent / "WORKFLOW_SYSTEM.md"

# ── node type → short label ────────────────────────────────────────────────

NODE_TYPE_LABELS = {
    "n8n-nodes-base.webhook":             "Webhook",
    "n8n-nodes-base.code":                "Code",
    "n8n-nodes-base.if":                  "IF",
    "n8n-nodes-base.httpRequest":         "HTTP",
    "n8n-nodes-base.respondToWebhook":    "Respond",
    "n8n-nodes-base.splitInBatches":      "Batch",
    "n8n-nodes-base.executeWorkflow":     "SubWF",
    "n8n-nodes-base.manualTrigger":       "Manual",
    "n8n-nodes-base.merge":               "Merge",
    "n8n-nodes-base.noOp":               "NoOp",
}


def short_label(node_type: str) -> str:
    return NODE_TYPE_LABELS.get(node_type, node_type.split(".")[-1])


# ── description extraction ─────────────────────────────────────────────────

def describe_node(node: dict) -> str:
    ntype  = node.get("type", "")
    params = node.get("parameters", {})

    if "webhook" in ntype:
        method = params.get("httpMethod", "POST")
        path   = params.get("path", "")
        return f"Receive `{method} /webhook/{path}`"

    if "respondToWebhook" in ntype:
        code = params.get("responseCode", "200")
        body = str(params.get("responseBody", ""))[:60].replace("\n", " ")
        return f"Respond {code}" + (f" — {body}" if body else "")

    if "if" in ntype:
        conds = params.get("conditions", {}).get("conditions", [])
        if conds:
            lv = str(conds[0].get("leftValue", ""))[:50]
            op = conds[0].get("operator", {}).get("operation", "")
            return f"Route on `{lv}` {op}"
        return "Route on condition"

    if "httpRequest" in ntype:
        method   = params.get("method", "GET")
        raw_url  = str(params.get("url", ""))
        url      = re.sub(r"=\{\{[^}]+\}\}", "=…", raw_url)
        url      = re.sub(r"\{\{[^}]+\}\}", "…", url)[:70]
        return f"`{method}` {url}"

    if "code" in ntype:
        js = params.get("jsCode", "")
        # Unescape literal \n sequences stored in JSON strings
        js_expanded = js.replace("\\n", "\n")
        for line in js_expanded.splitlines()[:8]:
            stripped = line.strip()
            if stripped.startswith("//"):
                comment = stripped[2:].strip()
                if len(comment) > 4:          # skip trivial ones
                    return comment[:100]
        return "Code"

    if "splitInBatches" in ntype:
        size = params.get("batchSize", "?")
        return f"Process {size} at a time"

    if "executeWorkflow" in ntype:
        wf_id = (params.get("workflowId") or {})
        if isinstance(wf_id, dict):
            wf_id = wf_id.get("value", "?")
        wait = params.get("options", {}).get("waitForSubWorkflow", False)
        mode = "sync" if wait else "fire-and-forget"
        return f"Call sub-workflow `{wf_id}` ({mode})"

    if "manualTrigger" in ntype:
        return "Manual trigger (n8n UI)"

    return short_label(ntype)


# ── execution-order walk ───────────────────────────────────────────────────

def execution_order(nodes: list, connections: dict) -> list:
    """BFS from root nodes (those with no incoming connections)."""
    all_targets: set = set()
    for src_conns in connections.values():
        for branch in src_conns.get("main", []):
            for edge in branch:
                all_targets.add(edge.get("node"))

    name_to_node = {n["name"]: n for n in nodes}
    roots = [n for n in nodes if n["name"] not in all_targets]
    if not roots:
        roots = nodes[:1]

    visited: set = set()
    ordered: list = []
    queue = list(roots)

    while queue:
        node = queue.pop(0)
        name = node["name"]
        if name in visited:
            continue
        visited.add(name)
        ordered.append(node)
        for branch in connections.get(name, {}).get("main", []):
            for edge in branch:
                tgt = edge.get("node")
                if tgt and tgt not in visited and tgt in name_to_node:
                    queue.append(name_to_node[tgt])

    # Append anything the BFS didn't reach (disconnected helper nodes)
    for node in nodes:
        if node["name"] not in visited:
            ordered.append(node)

    return ordered


# ── table generation ───────────────────────────────────────────────────────

def generate_table(nodes: list, connections: dict) -> str:
    ordered = execution_order(nodes, connections)
    header = "| Step | Node | Type | What it does |\n|---|---|---|---|"
    rows = []
    for i, node in enumerate(ordered, 1):
        name  = node["name"]
        label = short_label(node.get("type", ""))
        desc  = describe_node(node)
        rows.append(f"| {i} | `{name}` | {label} | {desc} |")
    return header + "\n" + "\n".join(rows)


# ── marker-based replacement ───────────────────────────────────────────────

MARKER_RE = re.compile(
    r"(<!-- WFSYNC:(?P<stem>[^:]+):START -->)"
    r".*?"
    r"(<!-- WFSYNC:(?P=stem):END -->)",
    re.DOTALL,
)


def update_docs(docs: str, stem: str, table: str) -> str:
    begin = f"<!-- WFSYNC:{stem}:START -->"
    end   = f"<!-- WFSYNC:{stem}:END -->"
    if begin not in docs:
        return docs  # no marker for this workflow — skip silently

    pattern = re.compile(
        re.escape(begin) + r".*?" + re.escape(end),
        re.DOTALL,
    )
    replacement = f"{begin}\n{table}\n{end}"
    return pattern.sub(replacement, docs)


# ── main ───────────────────────────────────────────────────────────────────

def main() -> None:
    if not DOCS_FILE.exists():
        print(f"[sync_workflow_docs] {DOCS_FILE} not found — nothing to do")
        return

    docs = DOCS_FILE.read_text(encoding="utf-8")
    changed = False

    for wf_file in sorted(WORKFLOWS_DIR.glob("*.json")):
        try:
            wf = json.loads(wf_file.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"[sync_workflow_docs] skip {wf_file.name}: {exc}")
            continue

        nodes       = wf.get("nodes", [])
        connections = wf.get("connections", {})
        stem        = wf_file.stem

        if not nodes:
            continue

        table    = generate_table(nodes, connections)
        new_docs = update_docs(docs, stem, table)

        if new_docs != docs:
            docs    = new_docs
            changed = True
            print(f"[sync_workflow_docs] updated table for {stem}")

    if changed:
        DOCS_FILE.write_text(docs, encoding="utf-8")
        print("[sync_workflow_docs] WORKFLOW_SYSTEM.md saved")
    else:
        print("[sync_workflow_docs] no changes")


if __name__ == "__main__":
    main()
