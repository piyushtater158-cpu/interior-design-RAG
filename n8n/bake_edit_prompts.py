#!/usr/bin/env python3
"""Bake spatial/pixel lock prompts into generate_edit workflow only."""
from __future__ import annotations

import json
from pathlib import Path

N8N = Path(__file__).parent
PROMPTS = N8N / "prompts"
WF_PATH = N8N / "workflows" / "generate_edit.json"

FRAME_LOCK = (PROMPTS / "image_gen_frame_lock.txt").read_text(encoding="utf-8").strip()
ARCHITECTURAL_LOCK = (PROMPTS / "architectural_lock.txt").read_text(encoding="utf-8").strip()
PIXEL_LOCK_TEMPLATE = (PROMPTS / "image_gen_pixel_lock.txt").read_text(encoding="utf-8").strip()
EDIT_PRACTICAL_FEASIBILITY = (
    PROMPTS / "edit_practical_feasibility.txt"
).read_text(encoding="utf-8").strip()

EDIT_WORKFLOW_ID = "r1eiHJf1twXOECJd"
N8N_BASE = "https://n8n.srv1649259.hstgr.cloud/api/v1"


def _js_escape(s: str) -> str:
    return (
        s.replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("${", "\\${")
        .replace("\r\n", "\n")
        .replace("\n", "\\n")
    )


BUILD_FLUX_EDIT_JS = r"""const EDIT_MODEL = 'black-forest-labs/flux.2-max';

const FRAME_LOCK_BLOCK = `__FRAME_LOCK__`;
const ARCHITECTURAL_LOCK_BLOCK = `__ARCHITECTURAL_LOCK__`;

function sniffMime(buf) {
  if (!buf || buf.length < 4) return 'image/png';
  if (buf[0] === 0xff && buf[1] === 0xd8) return 'image/jpeg';
  if (buf[0] === 0x89 && buf[1] === 0x50) return 'image/png';
  return 'image/png';
}

function getImageDimensions(buf) {
  if (!buf || buf.length < 24) return null;
  if (buf[0] === 0x89 && buf[1] === 0x50 && buf[2] === 0x4e && buf[3] === 0x47) {
    return { width: buf.readUInt32BE(16), height: buf.readUInt32BE(20) };
  }
  if (buf[0] === 0xff && buf[1] === 0xd8) {
    let i = 2;
    while (i < buf.length - 9) {
      if (buf[i] !== 0xff) { i++; continue; }
      const marker = buf[i + 1];
      const len = buf.readUInt16BE(i + 2);
      if (marker === 0xc0 || marker === 0xc2 || marker === 0xc1) {
        return { height: buf.readUInt16BE(i + 5), width: buf.readUInt16BE(i + 7) };
      }
      if (len < 2) break;
      i += 2 + len;
    }
  }
  return null;
}

async function decodeImageBuf(bin, itemIndex) {
  if (!bin?.data) return null;
  const raw = bin.data;
  if (raw !== 'filesystem-v2' && typeof raw === 'string' && raw.length > 256) {
    const dec = Buffer.from(raw, 'base64');
    if (dec.length > 100 && dec[0] !== 0x7b) return dec;
  }
  return await this.helpers.getBinaryDataBuffer(itemIndex, 'image');
}

function extractDelimitedBlock(text, tag) {
  const startRe = new RegExp(`={3,}\\s*${tag}\\s*={3,}`, 'i');
  const endRe = /={3,}\s*END\s*={3,}/i;
  const s = (text || '').search(startRe);
  if (s < 0) return null;
  const after = text.slice(s).replace(startRe, '');
  const e = after.search(endRe);
  if (e < 0) return after.trim();
  return after.slice(0, e).trim();
}

function extractSection(text, heading) {
  const re = new RegExp(
    heading.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '[^:]*:\\s*\\n?([\\s\\S]*?)(?=\\n[A-Za-z][^:\\n]{0,80}:|$)',
    'i'
  );
  const m = (text || '').match(re);
  return m ? m[1].trim() : '';
}

function extractLineValue(block, key) {
  const re = new RegExp(
    '^\\s*' + key.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '[^:]*:\\s*(.+)$',
    'im'
  );
  const m = (block || '').match(re);
  return m ? m[1].trim() : '';
}

function extractParentAgentBrief(parentPrompt) {
  const stamped = extractDelimitedBlock(parentPrompt, 'PROMPT');
  if (stamped) return stamped;
  const editIdx = parentPrompt.search(/EDIT \(apply only this change\)/i);
  if (editIdx > 0) return parentPrompt.slice(0, editIdx).trim();
  return parentPrompt;
}

function extractDoorLockFromBrief(brief) {
  const text = brief || '';
  const sentences = text.split(/(?<=[.!?])\s+/);
  const hits = sentences.filter((s) =>
    /entry\s+door|door\s+.*unobstructed|door\s+approach|do not relocate the door|door\s+swing|door\s+path|gate\s+path/i.test(s)
  );
  if (hits.length) return hits.join(' ').trim().slice(0, 500);
  const m = text.match(/entry\s+door[^\n.]{0,280}/i);
  return m ? m[0].trim() : '';
}

function extractWindowLockFromBrief(brief) {
  const text = brief || '';
  const sentences = text.split(/(?<=[.!?])\s+/);
  const hits = sentences.filter((s) =>
    /window|windows remain|do not add.*window|asymmetric.*window/i.test(s)
  );
  if (hits.length) return hits.slice(0, 2).join(' ').trim().slice(0, 500);
  const m = text.match(/(?:exactly\s+)?\d+\s+vertical\s+windows?[^\n.]{0,200}/i)
    || text.match(/windows?\s+(?:on|are on)\s+the\s+[^\n.]{0,200}/i);
  return m ? m[0].trim() : '';
}

function parseStructureLock(parentPrompt) {
  let door_lock = '';
  let window_lock = '';
  let light_lock = '';
  let input_pixels = '';
  let parse_source = 'none';

  const stamped = extractDelimitedBlock(parentPrompt, 'STRUCTURE_LOCK');
  if (stamped) {
    parse_source = 'structure_lock_block';
    door_lock = extractLineValue(stamped, 'Door lock') || extractLineValue(stamped, 'Door');
    window_lock = extractLineValue(stamped, 'Window lock') || extractLineValue(stamped, 'Windows');
    light_lock = extractLineValue(stamped, 'Light') || extractLineValue(stamped, 'Lighting');
    input_pixels = extractLineValue(stamped, 'InputPixels');
  }

  const criteria = extractDelimitedBlock(parentPrompt, 'CRITERIA') || '';
  if (!door_lock) {
    door_lock = extractLineValue(criteria, 'Door lock')
      || extractSection(criteria, 'Door lock')
      || extractSection(criteria, 'Spatial structure lock');
  }
  if (!window_lock) {
    window_lock = extractLineValue(criteria, 'Window lock')
      || extractSection(criteria, 'Window lock');
  }
  if (!light_lock) {
    light_lock = extractLineValue(criteria, 'Light')
      || extractSection(criteria, 'Light')
      || extractSection(criteria, 'Daylight & ambience')
      || extractSection(criteria, 'Daylight & ambience target');
  }

  const agentBrief = extractParentAgentBrief(parentPrompt);
  if (!door_lock) {
    door_lock = extractDoorLockFromBrief(agentBrief);
    if (door_lock && parse_source === 'none') parse_source = 'parent_prompt_door';
  }
  if (!window_lock) {
    window_lock = extractWindowLockFromBrief(agentBrief);
    if (window_lock && parse_source === 'none') parse_source = 'parent_prompt_window';
  }
  if (!light_lock) {
    const lm = agentBrief.match(/natural light[^\n.]{0,220}/i)
      || agentBrief.match(/light direction[^\n.]{0,220}/i);
    if (lm) {
      light_lock = lm[0].trim();
      if (parse_source === 'none') parse_source = 'parent_prompt_light';
    }
  }
  if (parse_source === 'none' && (door_lock || window_lock || light_lock)) {
    parse_source = 'criteria_fallback';
  }

  return { door_lock, window_lock, light_lock, input_pixels, parse_source };
}

function buildEditClearanceBlock(door_lock, window_lock, instruction) {
  const inst = (instruction || '').toLowerCase();
  const wantsMoreFurniture = /\b(more furniture|add furniture|furnish|extra furniture|additional furniture)\b/i.test(inst);
  const lines = [
    'HARD CONSTRAINT — PRACTICAL FEASIBILITY (overrides styling requests):',
    'Every placement must be physically possible: stable on the floor, real-world scale, no floating or overlapping objects, no blocking circulation.',
    door_lock
      ? `DOOR/GATE PATH: ${door_lock} Never place tables, dining sets, chairs, consoles, plants, or decor in the door approach zone or within ~90 cm (3 ft) of the door plane.`
      : 'DOOR/GATE PATH: Keep every visible door or gate approach zone completely clear — no furniture or decor in the entry path or door swing arc.',
    window_lock
      ? `WINDOW PATH: ${window_lock} Do not block window openings or sills with tall furniture or large decor.`
      : 'WINDOW PATH: Do not block any window opening; preserve natural light access from the photograph.',
    'CIRCULATION: Maintain clear walking paths between entry, windows, and furniture groupings.',
  ];
  if (wantsMoreFurniture) {
    lines.push(
      'MORE FURNITURE RULE: Add pieces only on walls away from the entry door — never satisfy “more furniture” by placing seating or tables in front of the door or gate.'
    );
  }
  return lines.join('\n');
}

function buildStructureLockBlock(door, win, light, pixels) {
  return [
    '===STRUCTURE_LOCK===',
    `Door lock: ${door}`,
    `Window lock: ${win}`,
    `Light: ${light}`,
    `InputPixels: ${pixels}`,
    '===END===',
  ].join('\n');
}

const ctx = $('Check cap').item.json;
const parentPrompt = (ctx.parent && ctx.parent.prompt) || '';
const parsed = parseStructureLock(parentPrompt);

if (!parsed.door_lock && !parsed.window_lock && !parsed.light_lock) {
  return [{
    json: {
      _error: {
        status: 400,
        body: {
          error: 'structure_lock_missing',
          code: 'invalid_state',
          parse_source: parsed.parse_source,
        },
      },
    },
  }];
}

const bin = $input.item.binary?.image;
if (!bin) {
  return [{ json: { _error: { status: 502, body: { error: 'parent_image_missing', code: 'upstream_error' } } } }];
}

let buf = await decodeImageBuf(bin, 0);
if (buf && buf[0] === 0x7b) {
  try {
    const p = JSON.parse(buf.toString('utf8'));
    if (p?.type === 'Buffer' && Array.isArray(p.data)) buf = Buffer.from(p.data);
  } catch (_) {}
}
const ok = buf && buf.length > 100 && ((buf[0] === 0xff && buf[1] === 0xd8) || (buf[0] === 0x89 && buf[1] === 0x50));
if (!ok) {
  return [{ json: { _error: { status: 502, body: { error: 'parent_image_invalid', code: 'upstream_error' } } } }];
}

const dims = getImageDimensions(buf);
if (!dims || !dims.width || !dims.height) {
  return [{ json: { _error: { status: 502, body: { error: 'parent_image_dimensions_unknown', code: 'upstream_error' } } } }];
}

const input_width = dims.width;
const input_height = dims.height;
const pixelLabel = `${input_width}x${input_height}`;
const input_pixels = parsed.input_pixels || pixelLabel;

const door_lock = parsed.door_lock
  || 'The entry door/gate stays on its photographed wall — approach zone must remain completely clear (no furniture in the door path).';
const window_lock = parsed.window_lock
  || 'Preserve every window exactly as in the input photograph — do not block openings with furniture or decor.';
const light_lock = parsed.light_lock
  || 'Preserve light direction and shadows exactly as in the input photograph.';

const structure_lock_block = buildStructureLockBlock(door_lock, window_lock, light_lock, input_pixels);

const pixel_lock = `__PIXEL_LOCK__`.replace('{width}', String(input_width)).replace('{height}', String(input_height));

const PRACTICAL_FEASIBILITY_BLOCK = `__EDIT_PRACTICAL_FEASIBILITY__`;

const instance_lock = [
  'INSTANCE STRUCTURE LOCK (from parent generation — highest priority):',
  `Door lock: ${door_lock}`,
  `Window lock: ${window_lock}`,
  `Light: ${light_lock}`,
].join('\n');

const clearance_block = buildEditClearanceBlock(door_lock, window_lock, ctx.instruction);

const edit_task = [
  'EDIT TASK (only mutable region):',
  `Apply ONLY this change inside the locked architectural shell: ${ctx.instruction}`,
  'If this change would move a door, window, or change light direction/geometry, change only styling, materials, or colors — never block openings.',
  'When adding furniture or luxury styling: place pieces on walls away from the entry door; never put tables, seating, or consoles in the door or gate path.',
  'Additional light fixtures are allowed only if window positions and the photograph light direction on walls and shadows stay unchanged.',
].join('\n');

const prompt = [
  'You are editing an interior design photograph. The attached image is the sole source of truth for architecture, frame, and pixels.',
  '',
  FRAME_LOCK_BLOCK,
  '',
  ARCHITECTURAL_LOCK_BLOCK,
  '',
  PRACTICAL_FEASIBILITY_BLOCK,
  '',
  pixel_lock,
  '',
  instance_lock,
  '',
  clearance_block,
  '',
  edit_task,
].join('\n');

function pickAspectRatio(w, h) {
  const r = w / h;
  const choices = [
    ['1:1', 1], ['5:4', 5 / 4], ['4:3', 4 / 3], ['3:2', 3 / 2], ['16:9', 16 / 9],
    ['4:5', 4 / 5], ['3:4', 3 / 4], ['2:3', 2 / 3], ['9:16', 9 / 16],
  ];
  let best = '4:3';
  let bestDelta = Infinity;
  for (const [label, ratio] of choices) {
    const delta = Math.abs(Math.log(r / ratio));
    if (delta < bestDelta) {
      bestDelta = delta;
      best = label;
    }
  }
  return best;
}

const mime = sniffMime(buf) || bin.mimeType || 'image/png';
const model = EDIT_MODEL;
const aspect_ratio = pickAspectRatio(input_width, input_height);

const openrouter_body = {
  model,
  modalities: ['image'],
  image_config: { aspect_ratio },
  messages: [{
    role: 'user',
    content: [
      { type: 'text', text: prompt },
      { type: 'image_url', image_url: { url: `data:${mime};base64,${buf.toString('base64')}` } },
    ],
  }],
};

const saved_prompt = `${structure_lock_block}\n\nEDIT (apply only this change): ${ctx.instruction}`;

return [{
  json: {
    ...ctx,
    model,
    prompt: saved_prompt,
    openrouter_body,
    input_width,
    input_height,
    aspect_ratio,
    structure_lock_block,
    door_lock,
    window_lock,
    light_lock,
    structure_parse_source: parsed.parse_source,
    clearance_block,
    wants_more_furniture: /\b(more furniture|add furniture|furnish|extra furniture)\b/i.test(ctx.instruction || ''),
  },
}];
"""

EXTRACT_OUTPUT_JS = r"""const ctx = $('Build Flux edit request').item.json;
const resp = $json;
const msg = (resp.choices && resp.choices[0] && resp.choices[0].message) || {};

function collectImageParts(message) {
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
}

function getImageDimensions(buf) {
  if (!buf || buf.length < 24) return null;
  if (buf[0] === 0x89 && buf[1] === 0x50 && buf[2] === 0x4e && buf[3] === 0x47) {
    return { width: buf.readUInt32BE(16), height: buf.readUInt32BE(20) };
  }
  if (buf[0] === 0xff && buf[1] === 0xd8) {
    let i = 2;
    while (i < buf.length - 9) {
      if (buf[i] !== 0xff) { i++; continue; }
      const marker = buf[i + 1];
      const len = buf.readUInt16BE(i + 2);
      if (marker === 0xc0 || marker === 0xc2 || marker === 0xc1) {
        return { height: buf.readUInt16BE(i + 5), width: buf.readUInt16BE(i + 7) };
      }
      if (len < 2) break;
      i += 2 + len;
    }
  }
  return null;
}

const imgPart = collectImageParts(msg)[0];
if (!imgPart) {
  return [{
    json: {
      _error: {
        status: 502,
        body: {
          error: 'no_image_in_response',
          code: 'upstream_error',
          has_images: Array.isArray(msg.images),
          content_type: typeof msg.content,
        },
      },
    },
  }];
}
const dataUrl = imgPart.image_url && imgPart.image_url.url;
const match = dataUrl && dataUrl.match(/^data:([^;]+);base64,(.+)$/s);
if (!match) {
  return [{ json: { _error: { status: 502, body: { error: 'invalid_image_data_url', code: 'upstream_error' } } } }];
}
let mime = match[1];
let b64 = match[2];
let outBuf = Buffer.from(b64, 'base64');
let outDim = getImageDimensions(outBuf);
const expectedW = ctx.input_width;
const expectedH = ctx.input_height;
let dimension_match = true;
let dimension_normalized = false;
let normalize_method = null;

async function normalizeToInput(buf, targetW, targetH) {
  try {
    const sharp = require('sharp');
    const resized = await sharp(buf)
      .resize(targetW, targetH, { fit: 'fill', kernel: sharp.kernel.lanczos3 })
      .png()
      .toBuffer();
    return { buf: resized, method: 'sharp' };
  } catch (_) {}
  return null;
}

if (!outDim || outDim.width !== expectedW || outDim.height !== expectedH) {
  const normalized = await normalizeToInput(outBuf, expectedW, expectedH);
  if (normalized?.buf) {
    outBuf = normalized.buf;
    outDim = getImageDimensions(outBuf) || { width: expectedW, height: expectedH };
    b64 = outBuf.toString('base64');
    dimension_normalized = true;
    normalize_method = normalized.method;
    mime = 'image/png';
  } else {
    dimension_match = false;
  }
}

const latency_ms = Date.now() - ctx.started_at_ms;
const model_config = JSON.stringify({
  dimension_match,
  dimension_normalized,
  normalize_method,
  aspect_ratio: ctx.aspect_ratio || null,
  input_width: expectedW,
  input_height: expectedH,
  output_width: outDim?.width || null,
  output_height: outDim?.height || null,
  structure_parse_source: ctx.structure_parse_source || null,
  debug_session: 'a12a5f',
});

return [{
  json: {
    user_id: ctx.user_id,
    session_id: ctx.session_id,
    parent_generation_id: ctx.parent.id,
    kind: 'edit',
    input_image_path: ctx.parent.output_image_path,
    room_type: ctx.parent.room_type,
    style_tag: ctx.parent.style_tag,
    reference_image_ids: ctx.parent.reference_image_ids,
    prompt: ctx.prompt,
    model_config,
    model_id: ctx.model,
    latency_ms,
    cost_usd: 0,
  },
  binary: {
    output_png: {
      data: b64,
      mimeType: mime,
      fileExtension: 'png',
      fileName: 'output.png',
    },
  },
}];
"""


def _read_env_api_key() -> str:
    env_path = N8N.parent / ".env"
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("N8N_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError("N8N_API_KEY missing")


def deploy_edit_workflow(wf: dict) -> None:
    import urllib.request

    key = _read_env_api_key()
    req = urllib.request.Request(
        f"{N8N_BASE}/workflows/{EDIT_WORKFLOW_ID}",
        headers={"X-N8N-API-KEY": key},
    )
    live = json.loads(urllib.request.urlopen(req).read())
    payload = {k: v for k, v in live.items() if k in ("name", "description", "nodes", "connections", "settings", "staticData", "pinData")}
    payload["nodes"] = wf["nodes"]
    payload["connections"] = wf["connections"]
    payload["settings"] = {"executionOrder": (live.get("settings") or {}).get("executionOrder", "v1")}
    put = urllib.request.Request(
        f"{N8N_BASE}/workflows/{EDIT_WORKFLOW_ID}",
        data=json.dumps(payload).encode(),
        method="PUT",
        headers={"Content-Type": "application/json", "X-N8N-API-KEY": key},
    )
    urllib.request.urlopen(put).read()
    if not live.get("active"):
        act = urllib.request.Request(
            f"{N8N_BASE}/workflows/{EDIT_WORKFLOW_ID}/activate",
            data=b"{}",
            method="POST",
            headers={"Content-Type": "application/json", "X-N8N-API-KEY": key},
        )
        urllib.request.urlopen(act).read()
    print(f"Deployed generate_edit ({EDIT_WORKFLOW_ID})")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--deploy", action="store_true", help="Push workflow to n8n")
    args = parser.parse_args()

    wf = json.loads(WF_PATH.read_text(encoding="utf-8"))
    pixel_escaped = _js_escape(PIXEL_LOCK_TEMPLATE)

    build_js = (
        BUILD_FLUX_EDIT_JS.replace("__FRAME_LOCK__", _js_escape(FRAME_LOCK))
        .replace("__ARCHITECTURAL_LOCK__", _js_escape(ARCHITECTURAL_LOCK))
        .replace("__EDIT_PRACTICAL_FEASIBILITY__", _js_escape(EDIT_PRACTICAL_FEASIBILITY))
        .replace("__PIXEL_LOCK__", pixel_escaped)
    )

    for node in wf["nodes"]:
        if node["name"] == "Build Flux edit request":
            node["parameters"]["jsCode"] = build_js
        elif node["name"] == "Extract output PNG":
            node["parameters"]["jsCode"] = EXTRACT_OUTPUT_JS

    # Route Build Flux errors to Extract ok? false branch via _error on same path
    for node in wf["nodes"]:
        if node["name"] == "Generate image (Flux)":
            pass

    WF_PATH.write_text(json.dumps(wf, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Baked edit locks into {WF_PATH}")
    print(f"  frame_lock lines: {len(FRAME_LOCK.splitlines())}")
    print(f"  architectural_lock lines: {len(ARCHITECTURAL_LOCK.splitlines())}")
    print(f"  practical_feasibility lines: {len(EDIT_PRACTICAL_FEASIBILITY.splitlines())}")
    print(f"  build_flux js length: {len(build_js)}")
    if args.deploy:
        deploy_edit_workflow(wf)


if __name__ == "__main__":
    main()
