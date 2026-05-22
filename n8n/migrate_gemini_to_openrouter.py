#!/usr/bin/env python3
"""
migrate_gemini_to_openrouter.py
Structurally migrate Gemini direct-API calls to OpenRouter in three workflows.

Changes per workflow:
  1. Build Gemini request  -> Build image gen request  (OpenAI/OpenRouter format)
  2. Agent 3 (Gemini) / Call Gemini  -> rewrite URL + auth header
  3. Extract output PNG  -> parse OpenRouter choices[] instead of candidates[]
  4. Collect image parts (orchestrated only)  -> build OpenAI image_url parts

Usage:
  python n8n/migrate_gemini_to_openrouter.py --check    # dry-run
  python n8n/migrate_gemini_to_openrouter.py --apply    # patch in-place
"""

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent.parent
WF   = ROOT / "n8n" / "workflows"

# ---------------------------------------------------------------------------
# New code snippets (OpenRouter / OpenAI format)
# ---------------------------------------------------------------------------

# generate_orchestrated.json — Collect image parts (unchanged key, new format)
COLLECT_CODE_ORCHESTRATED = r"""const items = $input.all();
items.sort((a, b) => a.json.idx - b.json.idx);
const parts = items.map(it => {
  const bin = it.binary.image;
  return {
    type: 'image_url',
    image_url: { url: `data:${bin.mimeType || 'image/png'};base64,${bin.data}` }
  };
});
return [{ json: { ...items[0].json, image_parts: parts } }];"""

# generate_orchestrated.json — Build image gen request
BUILD_CODE_ORCHESTRATED = r"""let rows;
if (Array.isArray($json)) {
  rows = $json;
} else if (Array.isArray($json?.body)) {
  rows = $json.body;
} else if ($json?.body && typeof $json.body === 'object') {
  rows = [$json.body];
} else if ($json && typeof $json === 'object' && ($json.value != null || $json.key != null)) {
  rows = [$json];
} else {
  rows = [];
}
const model = (rows[0] && rows[0].value) || 'google/gemini-3.1-flash-image-preview';
const ctx   = $('Collect image parts').item.json;

const openrouter_body = {
  model,
  messages: [{
    role: 'user',
    content: [{ type: 'text', text: ctx.agent_prompt }, ...(ctx.image_parts || [])]
  }]
};

return [{ json: { ...ctx, model, openrouter_body } }];"""

# generate_edit.json — Build image gen request
BUILD_CODE_EDIT = r"""const ctx = $('Check cap').item.json;
const bin = $input.item.binary.image;
const template = `You are editing an interior design photograph.

TASK: Apply ONLY the specific change requested below. Do not modify any other
element of the image. Preserve all geometry, lighting, and unaffected objects
exactly.

REQUESTED CHANGE: {instruction}
`;
const prompt = template.replace('{instruction}', ctx.instruction);

const openrouter_body = {
  model: ctx.model || 'google/gemini-3.1-flash-image-preview',
  messages: [{
    role: 'user',
    content: [
      { type: 'text', text: prompt },
      { type: 'image_url', image_url: { url: `data:${bin.mimeType || 'image/png'};base64,${bin.data}` } }
    ]
  }]
};
return [{ json: { ...ctx, prompt, openrouter_body } }];"""

# generate_commit.json — Build image gen request
BUILD_CODE_COMMIT = r"""const rows  = Array.isArray($json) ? $json : ($json.body || []);
const model = (rows[0] && rows[0].value) || 'google/gemini-3.1-flash-image-preview';
const ctx   = $('Collect image parts').item.json;

const template = `You are an interior design rendering engine.

TASK: Generate a photorealistic image of the SAME room shown in the first input
image, redesigned in the style of the reference images provided.

HARD CONSTRAINTS:
- Preserve the input room's geometry exactly: wall positions, window positions
  and sizes, door positions, ceiling height.
- Preserve lighting direction from the input photo.
- Use furniture, materials, colors, and styling cues from the reference images.
- Output must be photorealistic, no illustrations or cartoons.
- Do not add text, watermarks, logos, or signatures.
- Do not add people.

STYLE: {style_tag}
ROOM TYPE: {room_type}

OUTPUT QUALITY: Maximum resolution and detail. This is the final deliverable.
`;

const prompt = template
  .replace('{style_tag}', ctx.parent.style_tag || '')
  .replace('{room_type}', ctx.parent.room_type || '');

const openrouter_body = {
  model,
  messages: [{
    role: 'user',
    content: [{ type: 'text', text: prompt }, ...(ctx.image_parts || [])]
  }]
};

return [{ json: { ...ctx, model, prompt, openrouter_body } }];"""

# Extract output PNG — OpenRouter response parser (same for all three)
EXTRACT_IMAGE_PARTS_FN = r"""function collectImageParts(message) {
  const out = [];
  if (Array.isArray(message.images)) {
    for (const p of message.images) {
      if (p && (p.type === 'image_url' || p.image_url)) out.push(p);
    }
  }
  const content = message.content;
  if (Array.isArray(content)) {
    for (const p of content) {
      if (p && p.type === 'image_url') out.push(p);
    }
  } else if (typeof content === 'string' && content.trim()) {
    const m = content.match(/data:image\/[^;]+;base64,[A-Za-z0-9+/=]+/);
    if (m) out.push({ type: 'image_url', image_url: { url: m[0] } });
  }
  return out;
}"""

EXTRACT_CODE_ORCHESTRATED = r"""const ctx  = $('Build Gemini request').item.json;
const resp = $json;
const msg = (resp.choices && resp.choices[0] && resp.choices[0].message) || {};
""" + EXTRACT_IMAGE_PARTS_FN + r"""

const imgPart = collectImageParts(msg)[0];
if (!imgPart) {
  return [{ json: { _error: { status: 502, body: { error: 'no_image_in_response', code: 'upstream_error', has_images: Array.isArray(msg.images), content_type: typeof msg.content } } } }];
}
const dataUrl = imgPart.image_url && imgPart.image_url.url;
const match   = dataUrl && dataUrl.match(/^data:([^;]+);base64,(.+)$/s);
if (!match) {
  return [{ json: { _error: { status: 502, body: { error: 'invalid_image_data_url', code: 'upstream_error' } } } }];
}
const mime = match[1];
const b64  = match[2];
const latency_ms = Date.now() - ctx.started_at_ms;

return [{
  json: {
    user_id:              ctx.user_id,
    session_id:           ctx.session_id,
    parent_generation_id: null,
    kind:                 'orchestrated',
    input_image_path:     `user-uploads/${ctx.user_id}/${ctx.upload_id}`,
    room_type:            ctx.inferred_room || null,
    style_tag:            ctx.style_tag || null,
    reference_image_ids:  ctx.picked_reference_ids,
    prompt:               ctx.agent_prompt,
    criteria:             ctx.criteria,
    model_config:         'A',
    model_id:             ctx.model,
    latency_ms,
    cost_usd:             0
  },
  binary: { output_png: { data: b64, mimeType: mime, fileExtension: 'png', fileName: 'output.png' } }
}];"""

EXTRACT_CODE_EDIT = r"""const ctx  = $('Attach model').item.json;
const resp = $json;
const content = (resp.choices && resp.choices[0] && resp.choices[0].message && resp.choices[0].message.content) || [];
const parts   = Array.isArray(content) ? content : [];
const imgPart = parts.find(p => p.type === 'image_url');
if (!imgPart) {
  return [{ json: { _error: { status: 502, body: { error: 'no_image_in_response', code: 'upstream_error' } } } }];
}
const dataUrl = imgPart.image_url && imgPart.image_url.url;
const match   = dataUrl && dataUrl.match(/^data:([^;]+);base64,(.+)$/s);
if (!match) {
  return [{ json: { _error: { status: 502, body: { error: 'invalid_image_data_url', code: 'upstream_error' } } } }];
}
const mime = match[1];
const b64  = match[2];
const latency_ms = Date.now() - ctx.started_at_ms;

return [{
  json: {
    user_id:             ctx.user_id,
    session_id:          ctx.session_id,
    parent_generation_id: ctx.parent.id,
    kind:                'edit',
    input_image_path:    ctx.parent.output_image_path,
    room_type:           ctx.parent.room_type,
    style_tag:           ctx.parent.style_tag,
    reference_image_ids: ctx.parent.reference_image_ids,
    prompt:              ctx.prompt,
    model_config:        'A',
    model_id:            ctx.model,
    latency_ms,
    cost_usd:            0
  },
  binary: { output_png: { data: b64, mimeType: mime, fileExtension: 'png', fileName: 'output.png' } }
}];"""

EXTRACT_CODE_COMMIT = r"""const ctx  = $('Build Gemini request').item.json;
const resp = $json;
const msg = (resp.choices && resp.choices[0] && resp.choices[0].message) || {};
""" + EXTRACT_IMAGE_PARTS_FN + r"""

const imgPart = collectImageParts(msg)[0];
if (!imgPart) {
  return [{ json: { _error: { status: 502, body: { error: 'no_image_in_response', code: 'upstream_error', has_images: Array.isArray(msg.images), content_type: typeof msg.content } } } }];
}
const dataUrl = imgPart.image_url && imgPart.image_url.url;
const match   = dataUrl && dataUrl.match(/^data:([^;]+);base64,(.+)$/s);
if (!match) {
  return [{ json: { _error: { status: 502, body: { error: 'invalid_image_data_url', code: 'upstream_error' } } } }];
}
const mime = match[1];
const b64  = match[2];
const latency_ms = Date.now() - ctx.started_at_ms;

return [{
  json: {
    user_id:             ctx.user_id,
    session_id:          ctx.session_id,
    parent_generation_id: ctx.parent.id,
    kind:                'commit',
    input_image_path:    ctx.parent.input_image_path,
    room_type:           ctx.parent.room_type,
    style_tag:           ctx.parent.style_tag,
    reference_image_ids: ctx.parent.reference_image_ids,
    prompt:              ctx.prompt,
    model_config:        'A',
    model_id:            ctx.model,
    latency_ms,
    cost_usd:            0
  },
  binary: { output_png: { data: b64, mimeType: mime, fileExtension: 'png', fileName: 'output.png' } }
}];"""

# OpenRouter HTTP node parameters (replaces Gemini direct call)
def openrouter_http_params(body_ref: str, timeout: int = 120000, retry: bool = True) -> dict:
    params = {
        "method": "POST",
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "sendHeaders": True,
        "headerParameters": {
            "parameters": [
                {
                    "name": "Authorization",
                    "value": "=Bearer {{ $env.OPENROUTER_API_KEY }}"
                },
                {
                    "name": "Content-Type",
                    "value": "application/json"
                }
            ]
        },
        "sendBody": True,
        "specifyBody": "json",
        "jsonBody": f"={{{{ JSON.stringify($json.{body_ref}) }}}}",
        "options": {"timeout": timeout}
    }
    if retry:
        params["options"]["retry"] = {"tryTimes": 3, "waitBetweenTries": 2000}
    return params


# ---------------------------------------------------------------------------
# Patch specs per workflow
# ---------------------------------------------------------------------------

PATCHES = {
    "generate_orchestrated.json": [
        # Collect image parts: switch to OpenAI image_url format
        {
            "node_id": "collect",
            "field": "parameters.jsCode",
            "new_value": COLLECT_CODE_ORCHESTRATED,
            "description": "Collect image parts -> OpenAI image_url format",
        },
        # Build Gemini request -> Build image gen request (OpenRouter format)
        {
            "node_id": "build_gemini",
            "field": "parameters.jsCode",
            "new_value": BUILD_CODE_ORCHESTRATED,
            "description": "Build Gemini request -> OpenRouter body format",
        },
        # Agent 3 (Gemini) -> OpenRouter HTTP call
        {
            "node_id": "gemini_call",
            "field": "parameters",
            "new_value": openrouter_http_params("openrouter_body", retry=False),
            "description": "Agent 3 (Gemini) -> OpenRouter API call",
        },
        # Extract output PNG -> parse OpenRouter response
        {
            "node_id": "extract_png",
            "field": "parameters.jsCode",
            "new_value": EXTRACT_CODE_ORCHESTRATED,
            "description": "Extract output PNG -> parse OpenRouter choices[]",
        },
    ],
    "generate_edit.json": [
        # Build Gemini request -> OpenRouter format
        {
            "node_id": "build_gemini",
            "field": "parameters.jsCode",
            "new_value": BUILD_CODE_EDIT,
            "description": "Build Gemini request -> OpenRouter body format",
        },
        # Call Gemini -> OpenRouter HTTP call
        {
            "node_id": "gemini_call",
            "field": "parameters",
            "new_value": openrouter_http_params("openrouter_body", retry=True),
            "description": "Call Gemini -> OpenRouter API call",
        },
        # Extract output PNG -> parse OpenRouter response
        {
            "node_id": "extract",
            "field": "parameters.jsCode",
            "new_value": EXTRACT_CODE_EDIT,
            "description": "Extract output PNG -> parse OpenRouter choices[]",
        },
    ],
    "generate_commit.json": [
        # Build Gemini request -> OpenRouter format
        {
            "node_id": "build_gemini",
            "field": "parameters.jsCode",
            "new_value": BUILD_CODE_COMMIT,
            "description": "Build Gemini request -> OpenRouter body format",
        },
        # Call Gemini -> OpenRouter HTTP call
        {
            "node_id": "gemini_call",
            "field": "parameters",
            "new_value": openrouter_http_params("openrouter_body", retry=True),
            "description": "Call Gemini -> OpenRouter API call",
        },
        # Extract output PNG -> parse OpenRouter response
        {
            "node_id": "extract_png",
            "field": "parameters.jsCode",
            "new_value": EXTRACT_CODE_COMMIT,
            "description": "Extract output PNG -> parse OpenRouter choices[]",
        },
    ],
}


def set_nested(obj: dict, field_path: str, value) -> None:
    parts = field_path.split(".")
    for p in parts[:-1]:
        obj = obj[p]
    obj[parts[-1]] = value


def get_nested(obj: dict, field_path: str):
    parts = field_path.split(".")
    for p in parts:
        obj = obj[p]
    return obj


def apply_patches(wf: dict, patches: list) -> list[str]:
    nodes_by_id = {n["id"]: n for n in wf.get("nodes", [])}
    log = []
    for patch in patches:
        node = nodes_by_id.get(patch["node_id"])
        if not node:
            log.append(f"  MISSING node id={patch['node_id']} — skipping")
            continue
        try:
            old = get_nested(node, patch["field"])
            if old == patch["new_value"]:
                log.append(f"  ALREADY DONE: {patch['description']}")
            else:
                set_nested(node, patch["field"], patch["new_value"])
                log.append(f"  patched: {patch['description']}")
        except (KeyError, TypeError) as e:
            log.append(f"  ERROR on {patch['description']}: {e}")
    return log


def main() -> None:
    dry_run = "--check" in sys.argv
    apply   = "--apply" in sys.argv

    if not dry_run and not apply:
        print(__doc__)
        sys.exit(1)

    total = 0
    for fname, patches in PATCHES.items():
        path = WF / fname
        wf   = json.loads(path.read_text(encoding="utf-8"))
        print(f"\n{fname}")

        if dry_run:
            nodes_by_id = {n["id"]: n for n in wf.get("nodes", [])}
            for patch in patches:
                node = nodes_by_id.get(patch["node_id"])
                if not node:
                    print(f"  MISSING node id={patch['node_id']}")
                else:
                    print(f"  would patch: {patch['description']}")
                total += 1
        else:
            log = apply_patches(wf, patches)
            for line in log:
                print(line)
                if "patched:" in line:
                    total += 1
            path.write_text(json.dumps(wf, indent=2, ensure_ascii=False), encoding="utf-8")
            print("  -> written")

    if dry_run:
        print(f"\nDry run: {total} patch(es) would be applied. Run --apply to patch.")
    else:
        print(f"\nApplied {total} patch(es).")
        # Verify no Gemini keys remain in patched files
        remaining = []
        for fname in PATCHES:
            text = (WF / fname).read_text(encoding="utf-8")
            if "AIzaSy" in text or "generativelanguage.googleapis" in text:
                remaining.append(fname)
        if remaining:
            print(f"\nWARNING: Gemini artifacts still found in: {remaining}")
        else:
            print("Verification: no Gemini direct-API references remain in patched files.")


if __name__ == "__main__":
    main()
