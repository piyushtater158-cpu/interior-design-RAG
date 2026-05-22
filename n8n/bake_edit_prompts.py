#!/usr/bin/env python3
"""Bake spatial/pixel lock prompts into generate_edit workflow only."""
from __future__ import annotations

import json
import re
from pathlib import Path

from bake_orchestrator_prompts import (
    CUPBOARD_FOOTPRINT_BLOCK,
    DOOR_CLEARANCE_BLOCK,
    STORAGE_PLACEMENT_BLOCK,
)

N8N = Path(__file__).parent
PROMPTS = N8N / "prompts"
WF_PATH = N8N / "workflows" / "generate_edit.json"

ARCHITECTURAL_LOCK = (PROMPTS / "architectural_lock.txt").read_text(encoding="utf-8").strip()
CANVAS_HARD_LOCK_TEMPLATE = (PROMPTS / "image_gen_pixel_lock.txt").read_text(encoding="utf-8").strip()
EDIT_PRACTICAL_FEASIBILITY = (
    PROMPTS / "edit_practical_feasibility.txt"
).read_text(encoding="utf-8").strip()
EDIT_AGENT3_MANDATE = (PROMPTS / "edit_agent3_mandate.txt").read_text(encoding="utf-8").strip()
EDIT_DESIGN_PRINCIPLES = (PROMPTS / "edit_design_principles.txt").read_text(encoding="utf-8").strip()
EDIT_SINGLE_ELEMENT_RULE = (
    PROMPTS / "edit_single_element_rule.txt"
).read_text(encoding="utf-8").strip()
EDIT_NANO_BANANA_PREAMBLE = (
    PROMPTS / "edit_nano_banana_preamble.txt"
).read_text(encoding="utf-8").strip()

EDIT_WORKFLOW_ID = "r1eiHJf1twXOECJd"
BUILD_NODE_NAME = "Build Gemini edit request"
GENERATE_NODE_NAME = "Generate image (Gemini)"
FETCH_IMAGE_MODEL_NODE_NAME = "Fetch image_model"
ATTACH_PARENT_BINARY_NODE_NAME = "Attach parent binary"
VERIFY_WORKFLOW_ID = "56BlN6jqFkXVszX2"
VERIFY_WF_PATH = N8N / "workflows" / "_shared" / "wf_supabase_verify.json"
N8N_BASE = "https://n8n.srv1649259.hstgr.cloud/api/v1"
WRITABLE = ("name", "description", "nodes", "connections", "settings", "staticData", "pinData")

# Task-runner sandbox blocks process.env and $env; secrets use n8n credentials on HTTP nodes.
EDIT_CONFIG_JS = """return [{
  json: {
    ...$json,
    _cfg: {
      supabase_url:    'https://uzghfpxboktnbcbbthns.supabase.co',
      openrouter_base: 'https://openrouter.ai/api/v1',
      orch_model:      'google/gemini-2.5-flash'
    }
  },
  binary: $input.first().binary || {}
}];"""


def _js_escape(s: str) -> str:
    return (
        s.replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("${", "\\${")
        .replace("\r\n", "\n")
        .replace("\n", "\\n")
    )


BUILD_GEMINI_EDIT_JS = r"""const ARCHITECTURAL_LOCK_BLOCK = `__ARCHITECTURAL_LOCK__`;
const DOOR_CLEARANCE_BLOCK = `__DOOR_CLEARANCE__`;
const STORAGE_PLACEMENT_BLOCK = `__STORAGE_PLACEMENT__`;
const CUPBOARD_FOOTPRINT_BLOCK = `__CUPBOARD_FOOTPRINT__`;
const EDIT_NANO_BANANA_PREAMBLE_BLOCK = `__EDIT_NANO_BANANA_PREAMBLE__`;
const EDIT_AGENT3_MANDATE_BLOCK = `__EDIT_AGENT3_MANDATE__`;
const EDIT_DESIGN_PRINCIPLES_BLOCK = `__EDIT_DESIGN_PRINCIPLES__`;
const EDIT_SINGLE_ELEMENT_RULE_BLOCK = `__EDIT_SINGLE_ELEMENT__`;

const FURNITURE_NOUN_RE = /\b(chair|armchair|sofa|couch|bed|table|desk|lamp|rug|carpet|ottoman|stool|bench|dresser|wardrobe|cabinet|shelf|plant|mirror|curtain|nightstand|sideboard|console)\b/i;
const STORAGE_TERM_RE = /\b(cupboard|cupboards|wardrobe|wardrobes|closet|closets|armoire|built-?in\s+storage|hidden\s+storage|storage\s+unit)\b/i;

function collectHttpRows() {
  const items = $input.all();
  if (items.length > 1) {
    return items.map(it => it.json).filter(r => r && (r.value != null || r.key != null));
  }
  const j = items[0]?.json ?? $json;
  if (Array.isArray(j)) return j;
  if (Array.isArray(j?.body)) return j.body;
  if (j?.body && typeof j.body === 'object') return [j.body];
  if (j && typeof j === 'object') return [j];
  return [];
}

function parseModelValue(row) {
  if (!row) return '';
  let v = row.value;
  if (typeof v === 'string') {
    try { v = JSON.parse(v); } catch (_) {}
  }
  return String(v ?? '').replace(/^"|"$/g, '').trim();
}

function normalizeImageModel(raw) {
  let m = (raw || '').trim();
  if (!m) m = 'google/gemini-3.1-flash-image-preview';
  if (!m.includes('/')) m = 'google/' + m;
  return m;
}

const rows = collectHttpRows();
const model = normalizeImageModel(parseModelValue(rows[0]));

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
  try {
    return await this.helpers.getBinaryDataBuffer(itemIndex, 'image');
  } catch (err) {
    const msg = err && err.message ? String(err.message) : String(err);
    throw new Error(`binary_buffer_read_failed:${msg}`);
  }
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

function extractCriteriaSection(criteria, heading) {
  return extractSection(criteria, heading);
}

function extractLineValue(block, key) {
  const re = new RegExp(
    '^\\s*' + key.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '[^:]*:\\s*(.+)$',
    'im'
  );
  const m = (block || '').match(re);
  return m ? m[1].trim() : '';
}

function looksLikeGenerationBrief(body) {
  const b = (body || '').trim();
  if (!b || b.length < 80) return false;
  if (/^is the authoritative/i.test(b)) return false;
  if (/^Complementarity guidance/i.test(b)) return false;
  if (/^A\s+fully\s+furnished/i.test(b)) return true;
  if (/image\s*1\s+is\s+authoritative/i.test(b) && /preserve/i.test(b)) return true;
  if (/attached\s+(room\s+)?photograph/i.test(b) && /preserve.*(?:door|window|opening)/i.test(b)) return true;
  return false;
}

function extractPromptBlock(text) {
  const startRe = /={3,}\s*PROMPT\s*={3,}/gi;
  const endRe = /={3,}\s*END\s*={3,}/i;
  const blocks = [];
  let m;
  while ((m = startRe.exec(text)) !== null) {
    const after = text.slice(m.index + m[0].length);
    const e = after.search(endRe);
    const body = (e < 0 ? after : after.slice(0, e)).trim();
    if (body) blocks.push(body);
  }
  if (!blocks.length) return null;
  for (let i = blocks.length - 1; i >= 0; i--) {
    if (looksLikeGenerationBrief(blocks[i])) return blocks[i];
  }
  return blocks[blocks.length - 1];
}

function extractParentAgentBrief(parentPrompt) {
  const stamped = extractPromptBlock(parentPrompt);
  if (stamped) return stamped;
  const delimited = extractDelimitedBlock(parentPrompt, 'PROMPT');
  if (delimited) return delimited;
  const editIdx = parentPrompt.search(/EDIT \(apply only this change\)/i);
  if (editIdx > 0) return parentPrompt.slice(0, editIdx).trim();
  return parentPrompt;
}

function stripPrependedConstraintBlocks(text) {
  let t = (text || '').trim();
  const patterns = [
    /^OPENING INVENTORY \(non-negotiable\):[\s\S]*?(?=\n\n|$)/im,
    /^STORAGE CONSTRAINTS \(non-negotiable\):[\s\S]*?(?=\n\n|$)/im,
    /\n\nWindow count lock \(mandatory\):[\s\S]*?(?=\n\n[A-Z]|$)/i,
    /\n\nStorage placement \(mandatory\):[\s\S]*?(?=\n\n[A-Z]|$)/i,
    /^PIXEL DIMENSION LOCK[\s\S]*?(?=\n\n[A-Z]|$)/im,
    /^CANVAS HARD LOCK[\s\S]*?(?=\n\n[A-Z]|$)/im,
    /^MANDATORY \(every generation\):[\s\S]*?(?=\n\n[A-Z]|$)/im,
    /^ARCHITECTURAL LOCK — IMAGE 1[\s\S]*?(?=\n\n(?:DOOR CLEARANCE|===|INSTANCE|EDIT |PRIMARY)|$)/im,
  ];
  for (const re of patterns) {
    t = t.replace(re, '').trim();
  }
  return t.replace(/^\n+/, '').trim();
}

function userRequestedStorage(userBrief, promptRaw) {
  return STORAGE_TERM_RE.test(userBrief || '') || STORAGE_TERM_RE.test(promptRaw || '');
}

function parseStorageConstraints(criteria, promptRaw, userBrief) {
  if (!userRequestedStorage(userBrief, promptRaw)) return null;
  const src = ((userBrief || '') + '\n' + (promptRaw || '') + '\n' + (criteria || '')).toLowerCase();
  const photo_has_built_in = /\b(existing|photograph|photo|image\s*1|visible\s+in|as\s+(seen|shown))[^\n]{0,80}built-?in\b/i.test(src)
    || (
      /\bbuilt-?in\s+(wardrobe|cupboard|closet|storage)\b/i.test(src)
      && /\b(photograph|photo|image\s*1|preserve)\b/i.test(src)
    );
  let placement = 'freestanding_new';
  if (photo_has_built_in) placement = 'preserve_photo';
  return { has_storage_in_brief: true, photo_has_built_in, placement };
}

function buildSpatialReq(criteria) {
  let notes = '';
  const spatialM = (criteria || '').match(
    /Spatial structure lock[^\n]*:\s*\n([\s\S]*?)(?=\n\nUser design intent|\nUser design intent)/i
  );
  if (spatialM) {
    notes = spatialM[1].trim();
  } else {
    notes = extractCriteriaSection(criteria, 'Spatial structure lock')
      || extractCriteriaSection(criteria, 'Room type & 3D structure')
      || extractCriteriaSection(criteria, '3D spatial structure');
  }
  if (!notes) return null;
  const req = { notes: notes.slice(0, 500) };
  const lc = (req.notes || '').toLowerCase();
  if (/door/.test(lc)) req.has_doors = true;
  if (/window/.test(lc)) req.has_windows = true;
  if (Object.keys(req).length <= 1 && !req.has_doors && !req.has_windows) return null;
  return req;
}

function parseWindowCountFromCriteria(criteria, brief) {
  const text = ((criteria || '') + '\n' + (brief || ''));
  const m = text.match(/\bexactly\s+(\d+)\s+window/i)
    || text.match(/\b(\d+)\s+vertical\s+windows?/i)
    || text.match(/\brender\s+exactly\s+(\d+)\s+window/i);
  if (m) return parseInt(m[1], 10);
  return null;
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

  return { door_lock, window_lock, light_lock, input_pixels, parse_source, criteria, agentBrief };
}

function narrowEditInstruction(instruction) {
  const original = (instruction || '').trim();
  if (!original) {
    return { original: '', applied: '', single_element_mode: false };
  }

  const multiConj = /\b(and\s+also|,\s*and\s+|;\s*and\s+|plus\s+|as\s+well\s+as)\b/i.test(original);
  const actionVerbs = original.match(/\b(move|place|put|relocate|swap|replace|remove|add|shift|reposition)\b/gi) || [];
  const multiActions = actionVerbs.length >= 2;
  const nounHits = original.match(new RegExp(FURNITURE_NOUN_RE.source, 'gi')) || [];
  const enumerated = nounHits.length >= 2 && /\b(and|both|all|each)\b/i.test(original);

  const isMulti = multiConj || multiActions || enumerated;
  if (!isMulti) {
    return { original, applied: original, single_element_mode: false };
  }

  let applied = original;
  const nounM = original.match(
    /\b((?:the\s+)?(?:[\w-]+\s+){0,4}(?:chair|armchair|sofa|couch|bed|table|desk|lamp|rug|carpet|ottoman|stool|bench|dresser|wardrobe|cabinet|shelf|plant|mirror|curtain|nightstand|sideboard|console))\b/i
  );
  if (nounM) {
    const target = nounM[1];
    const esc = target.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const verbM = original.match(
      new RegExp(`\\b(move|place|put|relocate|swap|replace|remove|add|shift|reposition)[^.;]{0,160}?${esc}`, 'i')
    ) || original.match(new RegExp(`${esc}[^.;]{0,160}`, 'i'));
    applied = verbM ? verbM[0].trim() : `Apply only the change involving the ${target}.`;
  } else {
    applied = (original.split(/(?<=[.!?])\s+/)[0] || original).slice(0, 280);
  }

  return { original, applied, single_element_mode: true };
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

const inputItem = $input.first();
const bin = inputItem.binary?.image;
if (!bin) {
  return [{ json: { _error: { status: 502, body: { error: 'parent_image_missing', code: 'upstream_error', detail: 'binary_not_on_build_input' } } } }];
}

// #region agent log
const _build_debug_pre = { hypothesisId: 'H1', binary_data_kind: typeof bin.data === 'string' ? (bin.data === 'filesystem-v2' ? 'filesystem-v2' : 'inline') : 'other', has_input_binary: Boolean(inputItem.binary?.image) };
// #endregion

let buf;
try {
  buf = await decodeImageBuf(bin, 0);
} catch (err) {
  return [{
    json: {
      _error: { status: 502, body: { error: 'parent_image_decode_failed', code: 'upstream_error', message: String(err?.message || err) } },
      _build_debug: _build_debug_pre,
    },
  }];
}
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
const canvas_hard_lock = `__CANVAS_HARD_LOCK__`
  .replace('{width}', String(input_width))
  .replace('{height}', String(input_height));
const PRACTICAL_FEASIBILITY_BLOCK = `__EDIT_PRACTICAL_FEASIBILITY__`;

const parentCriteria = parsed.criteria || '';
const rawAgentBrief = parsed.agentBrief || '';
let coreBrief = stripPrependedConstraintBlocks(rawAgentBrief);
if (coreBrief.length > 6000) coreBrief = coreBrief.slice(0, 6000);

const spatial_req = buildSpatialReq(parentCriteria);
const SPATIAL_NOTES_BLOCK = (spatial_req && spatial_req.notes)
  ? `=== SPATIAL LOCK FROM PHOTO ===\n${spatial_req.notes}`
  : '';

const storage_constraints = parseStorageConstraints(parentCriteria, parentPrompt, '');
let STORAGE_BLOCK = '';
let CUPBOARD_BLOCK = '';
if (storage_constraints && storage_constraints.placement !== 'none') {
  STORAGE_BLOCK = STORAGE_PLACEMENT_BLOCK;
  if (storage_constraints.placement === 'freestanding_new') {
    CUPBOARD_BLOCK = CUPBOARD_FOOTPRINT_BLOCK;
  }
}

const windowCount = parseWindowCountFromCriteria(parentCriteria, coreBrief);
const WINDOW_COUNT_BLOCK = windowCount != null
  ? `=== WINDOW COUNT LOCK ===\nRender exactly ${windowCount} window opening(s) as in image 1. Forbidden: a third window, sidelights, transoms, or new openings on other walls.`
  : '';

const instance_lock = [
  'INSTANCE STRUCTURE LOCK (from parent generation — highest priority):',
  `Door lock: ${door_lock}`,
  `Window lock: ${window_lock}`,
  `Light: ${light_lock}`,
].join('\n');

const editNarrow = narrowEditInstruction(ctx.instruction);
const appliedInstruction = editNarrow.applied;

const FROZEN_SCENE_HEADER = '=== FROZEN SCENE (parent generation — do not redesign) ===';
const PRIMARY_EDIT_HEADER = '=== PRIMARY EDIT (only mutable directive) ===';

const edit_task = [
  PRIMARY_EDIT_HEADER,
  `Apply ONLY this change inside the locked architectural shell: ${appliedInstruction}`,
  'If this change would move a door, window, or change light direction/geometry, change only styling, materials, or colors — never block openings.',
  'When adding furniture or luxury styling: place pieces on walls away from the entry door; never put tables, seating, or consoles in the door or gate path.',
  'Additional light fixtures are allowed only if window positions and the photograph light direction on walls and shadows stay unchanged.',
].join('\n');

const promptParts = [
  ARCHITECTURAL_LOCK_BLOCK,
  canvas_hard_lock,
  WINDOW_COUNT_BLOCK,
  DOOR_CLEARANCE_BLOCK,
  SPATIAL_NOTES_BLOCK,
  STORAGE_BLOCK,
  CUPBOARD_BLOCK,
  PRACTICAL_FEASIBILITY_BLOCK,
  instance_lock,
  EDIT_NANO_BANANA_PREAMBLE_BLOCK,
  EDIT_AGENT3_MANDATE_BLOCK,
  EDIT_DESIGN_PRINCIPLES_BLOCK,
  coreBrief ? FROZEN_SCENE_HEADER : '',
  coreBrief,
  editNarrow.single_element_mode ? EDIT_SINGLE_ELEMENT_RULE_BLOCK : '',
  edit_task,
].filter(Boolean);

const prompt = promptParts.join('\n\n');

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
const aspect_ratio = pickAspectRatio(input_width, input_height);

const openrouter_body = {
  model,
  modalities: ['image', 'text'],
  messages: [{
    role: 'user',
    content: [
      { type: 'text', text: prompt },
      { type: 'image_url', image_url: { url: `data:${mime};base64,${buf.toString('base64')}` } },
    ],
  }],
};
openrouter_body.image_config = { aspect_ratio, image_size: '1K' };

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
    wants_more_furniture: /\b(more furniture|add furniture|furnish|extra furniture)\b/i.test(ctx.instruction || ''),
    _prompt_debug: {
      generation_prompt_len: prompt.length,
      core_brief_len: coreBrief.length,
      has_canvas_hard_lock_block: Boolean(canvas_hard_lock),
      has_width_lock_language: /WIDTH LOCK/i.test(canvas_hard_lock || ''),
      has_frame_lock_in_prompt: /MANDATORY \(every generation\)/i.test(prompt),
      has_spatial_notes: Boolean(SPATIAL_NOTES_BLOCK),
      has_storage_block: Boolean(STORAGE_BLOCK),
      has_window_count_block: Boolean(WINDOW_COUNT_BLOCK),
      edit_instruction_original: editNarrow.original,
      edit_instruction_applied: appliedInstruction,
      single_element_mode: editNarrow.single_element_mode,
      ...(_build_debug_pre || {}),
      parent_buf_len: buf ? buf.length : 0,
    },
  },
}];
"""

EXTRACT_OUTPUT_JS = r"""const ctx = $('Build Gemini edit request').item.json;
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
  prompt_debug: ctx._prompt_debug || null,
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


def _load_project_env() -> dict[str, str]:
    out: dict[str, str] = {}
    env_path = N8N.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            out[k.strip()] = v.strip()
    return out


def _js_quote(s: str) -> str:
    return s.replace("\\", "\\\\").replace("'", "\\'")


def verify_normalize_js(anon_key: str) -> str:
    k = _js_quote(anon_key)
    return (
        "const item = $input.first().json;\n"
        f"const SUPABASE_APIKEY = '{k}';\n"
        "const raw = item.authorization\n"
        "  || (item.headers && (item.headers.authorization || item.headers.Authorization))\n"
        "  || '';\n"
        "let t = String(raw).trim();\n"
        "while (/^Bearer\\s+/i.test(t)) t = t.replace(/^Bearer\\s+/i, '').trim();\n"
        "const authorization = t ? `Bearer ${t}` : '';\n"
        "return [{ json: { ...item, authorization, supabase_apikey: SUPABASE_APIKEY } }];"
    )


def _api_put_workflow(workflow_id: str, nodes: list, connections: dict, name: str | None = None) -> None:
    import urllib.request

    key = _read_env_api_key()
    req = urllib.request.Request(
        f"{N8N_BASE}/workflows/{workflow_id}",
        headers={"X-N8N-API-KEY": key},
    )
    live = json.loads(urllib.request.urlopen(req).read())
    payload = {k: v for k, v in live.items() if k in WRITABLE}
    payload["nodes"] = nodes
    payload["connections"] = connections
    if name:
        payload["name"] = name
    payload["settings"] = {"executionOrder": (live.get("settings") or {}).get("executionOrder", "v1")}
    put = urllib.request.Request(
        f"{N8N_BASE}/workflows/{workflow_id}",
        data=json.dumps(payload).encode(),
        method="PUT",
        headers={"Content-Type": "application/json", "X-N8N-API-KEY": key},
    )
    urllib.request.urlopen(put).read()


def _supabase_anon_key() -> str:
    env = _load_project_env()
    for key in ("SUPABASE_ANON_KEY", "SUPABASE_ANON"):
        if v := env.get(key, "").strip():
            return v
    mobile = N8N.parent / "mobile-app" / "index.html"
    if mobile.exists():
        m = re.search(r"const SUPABASE_ANON = '([^']+)'", mobile.read_text(encoding="utf-8"))
        if m:
            return m.group(1).strip()
    raise RuntimeError("SUPABASE_ANON_KEY missing (.env or mobile-app/index.html)")


def deploy_verify_workflow() -> None:
    anon = _supabase_anon_key()
    wf = json.loads(VERIFY_WF_PATH.read_text(encoding="utf-8-sig"))
    for node in wf["nodes"]:
        if node["name"] == "Normalize auth header":
            node["parameters"]["jsCode"] = verify_normalize_js(anon)
    VERIFY_WF_PATH.write_text(json.dumps(wf, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    _api_put_workflow(VERIFY_WORKFLOW_ID, wf["nodes"], wf["connections"], wf.get("name"))
    print(f"Deployed wf_supabase_verify ({VERIFY_WORKFLOW_ID})")


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


ATTACH_PARENT_BINARY_JS = r"""const modelRow = $input.first().json;
const pngItem = $('Fetch parent PNG').first();
if (!pngItem?.binary?.image) {
  return [{ json: { _error: { status: 502, body: { error: 'parent_image_missing', code: 'upstream_error' } } } }];
}
return [{
  json: modelRow,
  binary: pngItem.binary,
}];
"""

FETCH_IMAGE_MODEL_NODE = {
    "parameters": {
        "url": "=https://uzghfpxboktnbcbbthns.supabase.co/rest/v1/app_config?key=eq.image_model&select=value",
        "options": {"timeout": 10000},
        "authentication": "predefinedCredentialType",
        "nodeCredentialType": "supabaseApi",
        "headerParameters": {"parameters": []},
    },
    "id": "edit_fetch_image_model",
    "name": FETCH_IMAGE_MODEL_NODE_NAME,
    "type": "n8n-nodes-base.httpRequest",
    "typeVersion": 4.2,
    "position": [3000, 780],
    "credentials": {
        "supabaseApi": {
            "id": "7rZNgbzFZJtpVqub",
            "name": "Supabase account",
        }
    },
}


def _rename_connection_key(connections: dict, old: str, new: str) -> None:
    if old in connections:
        connections[new] = connections.pop(old)


def ensure_fetch_image_model_node(wf: dict) -> None:
    if any(n["name"] == FETCH_IMAGE_MODEL_NODE_NAME for n in wf["nodes"]):
        return
    fetch_png = next(n for n in wf["nodes"] if n["name"] == "Fetch parent PNG")
    pos = fetch_png.get("position") or [2880, 780]
    node = {**FETCH_IMAGE_MODEL_NODE, "position": [pos[0] + 240, pos[1]]}
    wf["nodes"].append(node)


def ensure_attach_parent_binary_node(wf: dict) -> None:
    fetch_model = next(
        (n for n in wf["nodes"] if n["name"] == FETCH_IMAGE_MODEL_NODE_NAME),
        None,
    )
    if fetch_model is None:
        ensure_fetch_image_model_node(wf)
        fetch_model = next(n for n in wf["nodes"] if n["name"] == FETCH_IMAGE_MODEL_NODE_NAME)
    pos = fetch_model.get("position") or [3120, 780]
    existing = next(
        (n for n in wf["nodes"] if n["name"] == ATTACH_PARENT_BINARY_NODE_NAME),
        None,
    )
    if existing:
        existing["parameters"]["jsCode"] = ATTACH_PARENT_BINARY_JS
        existing["position"] = [pos[0] + 240, pos[1]]
        return
    wf["nodes"].append(
        {
            "parameters": {"jsCode": ATTACH_PARENT_BINARY_JS},
            "id": "edit_attach_parent_binary",
            "name": ATTACH_PARENT_BINARY_NODE_NAME,
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [pos[0] + 240, pos[1]],
        }
    )


def patch_edit_workflow_graph(wf: dict) -> None:
    for node in wf["nodes"]:
        if node["name"] == "Build Flux edit request":
            node["name"] = BUILD_NODE_NAME
        elif node["name"] == "Generate image (Flux)":
            node["name"] = GENERATE_NODE_NAME
        elif node["name"] == "Respond 200":
            rb = node["parameters"].get("responseBody", "")
            if "backend_id:    'flux'" in rb:
                node["parameters"]["responseBody"] = rb.replace(
                    "backend_id:    'flux'", "backend_id:    'gemini'"
                )

    ensure_fetch_image_model_node(wf)
    ensure_attach_parent_binary_node(wf)

    conn = wf["connections"]
    _rename_connection_key(conn, "Build Flux edit request", BUILD_NODE_NAME)
    _rename_connection_key(conn, "Generate image (Flux)", GENERATE_NODE_NAME)

    conn["Fetch parent PNG"] = {
        "main": [[{"node": FETCH_IMAGE_MODEL_NODE_NAME, "type": "main", "index": 0}]]
    }
    conn[FETCH_IMAGE_MODEL_NODE_NAME] = {
        "main": [[{"node": ATTACH_PARENT_BINARY_NODE_NAME, "type": "main", "index": 0}]]
    }
    conn[ATTACH_PARENT_BINARY_NODE_NAME] = {
        "main": [[{"node": BUILD_NODE_NAME, "type": "main", "index": 0}]]
    }

    build_ok = conn.get("Build ok?", {}).get("main", [])
    for branch in build_ok:
        for link in branch:
            if link.get("node") in ("Generate image (Flux)", GENERATE_NODE_NAME):
                link["node"] = GENERATE_NODE_NAME


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--deploy", action="store_true", help="Push workflow to n8n")
    args = parser.parse_args()

    wf = json.loads(WF_PATH.read_text(encoding="utf-8"))
    canvas_escaped = _js_escape(CANVAS_HARD_LOCK_TEMPLATE)

    build_js = (
        BUILD_GEMINI_EDIT_JS.replace("__ARCHITECTURAL_LOCK__", _js_escape(ARCHITECTURAL_LOCK))
        .replace("__DOOR_CLEARANCE__", _js_escape(DOOR_CLEARANCE_BLOCK))
        .replace("__STORAGE_PLACEMENT__", _js_escape(STORAGE_PLACEMENT_BLOCK))
        .replace("__CUPBOARD_FOOTPRINT__", _js_escape(CUPBOARD_FOOTPRINT_BLOCK))
        .replace("__EDIT_NANO_BANANA_PREAMBLE__", _js_escape(EDIT_NANO_BANANA_PREAMBLE))
        .replace("__EDIT_AGENT3_MANDATE__", _js_escape(EDIT_AGENT3_MANDATE))
        .replace("__EDIT_DESIGN_PRINCIPLES__", _js_escape(EDIT_DESIGN_PRINCIPLES))
        .replace("__EDIT_SINGLE_ELEMENT__", _js_escape(EDIT_SINGLE_ELEMENT_RULE))
        .replace("__EDIT_PRACTICAL_FEASIBILITY__", _js_escape(EDIT_PRACTICAL_FEASIBILITY))
        .replace("__CANVAS_HARD_LOCK__", canvas_escaped)
    )

    patch_edit_workflow_graph(wf)

    for node in wf["nodes"]:
        if node["name"] == "Config":
            node["parameters"]["jsCode"] = EDIT_CONFIG_JS
        elif node["name"] == BUILD_NODE_NAME:
            node["parameters"]["jsCode"] = build_js
        elif node["name"] == "Extract output PNG":
            node["parameters"]["jsCode"] = EXTRACT_OUTPUT_JS

    WF_PATH.write_text(json.dumps(wf, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Baked edit locks into {WF_PATH}")
    print(f"  build_gemini js length: {len(build_js)}")
    if args.deploy:
        deploy_edit_workflow(wf)
        deploy_verify_workflow()


if __name__ == "__main__":
    main()
