#!/usr/bin/env python3
"""Bake design-principles prompts into generate_orchestrated workflow JSON."""
from __future__ import annotations

import json
import re
from pathlib import Path

N8N = Path(__file__).parent
PROMPTS = N8N / "prompts"
WF_PATH = N8N / "workflows" / "generate_orchestrated.json"

# Agent 1 (orchestrator + room photo) and Agent 2 (reference picker) via OpenRouter.
# gemini-2.5-flash: reliable VL + fast (~20–30s). Nemotron free tier idle-times out on long prompts.
OPENROUTER_ORCH_MODEL_DEFAULT = "google/gemini-2.5-flash"

DESIGN_PRINCIPLES = (PROMPTS / "design_principles.txt").read_text(encoding="utf-8").strip()
FRAME_LOCK = (PROMPTS / "image_gen_frame_lock.txt").read_text(encoding="utf-8").strip()
ARCHITECTURAL_LOCK = (PROMPTS / "architectural_lock.txt").read_text(encoding="utf-8").strip()
AGENT3_GENERATION_MANDATE = (PROMPTS / "agent3_generation_mandate.txt").read_text(encoding="utf-8").strip()
AGENT2_SYSTEM = (PROMPTS / "agent2_retriever.txt").read_text(encoding="utf-8").strip()
AGENT1_ORCHESTRATOR = (PROMPTS / "agent1_orchestrator.txt").read_text(encoding="utf-8").strip()

PRIMARY_BRIEF_HEADER = (
    "=== PRIMARY GENERATION BRIEF (authoritative — follow this over reference images) ==="
)

DOOR_LOCK_FOOTER = (
    "Door lock (mandatory): the entry door must stay on the same wall and in the same "
    "position along that wall as in the user's photograph — do not move the door to "
    "another wall, do not add or remove a doorway, do not copy a reference image's door "
    "placement. Keep the door approach zone clear."
)

ARCHITECTURAL_LAYOUT_FOOTER = (
    "Window and light fidelity (mandatory): preserve exact window positions, sizes, and "
    "wall placement as in the user's photograph; preserve exact light direction and shadow "
    "pattern; do not add, relocate, or resize windows; do not symmetrize openings."
)

WINDOW_COUNT_FOOTER_TEMPLATE = (
    "Window count lock (mandatory): render exactly {n} window opening(s) as visible in "
    "image 1 — do not add a third window, sidelight, transom, or any extra opening."
)

DOOR_CLEARANCE_BLOCK = (
    "DOOR CLEARANCE (mandatory — image 1):\n"
    "Keep the entire door swing arc and at least 1 meter of approach path on the photographed "
    "entry door wall completely empty: no table, desk, console, chair, ottoman, plant, or "
    "floor lamp base blocking the door or entry path.\n"
    "Corner lamps, decor, and case goods only on corners away from the entry door wall — "
    "never in front of the door."
)

STORAGE_PLACEMENT_BLOCK = (
    "STORAGE CONSTRAINTS (non-negotiable — image 1):\n"
    "Do not add new built-in, recessed, or flush-to-wall cupboards/wardrobes/closets unless "
    "image 1 already shows that exact built-in treatment.\n"
    "New storage must be freestanding or proud in the room volume — not cavity storage inside "
    "the wall plane.\n"
    "The host wall must stay visible: paint, texture, and trim above and beside the unit; "
    "never a seamless wall-to-wall wardrobe plane unless image 1 already has one.\n"
    "Reserve clearance: at least 60 cm beside approach sides and 30 cm where the unit meets "
    "a wall; do not block door swing, windows, or primary circulation.\n"
    "Shift bed, desk, and decor layout to respect the storage footprint while keeping balance."
)

CUPBOARD_FOOTPRINT_BLOCK = (
    "CUPBOARD FOOTPRINT (mandatory when storage is in the brief):\n"
    "Show intentional negative space around the storage unit; the room layout must read as "
    "designed around its depth and width.\n"
    "Forbidden unless image 1 shows it: wall-to-wall flush wardrobe, recessed closet cavity, "
    "or storage that erases the visible wall surface."
)

CONFLICT_OVERRIDE_LINE = (
    "If any instruction would move a door, window, or change light direction, ignore that instruction."
)

AGENT1_EXTRA_RULES = """
AGENT 3 GENERATION BRIEF (mandatory):
- The ===PROMPT=== block is the Agent 3 generation brief — the authoritative creative directive for the image model.
- Reference images are style/material/mood inspiration only; never copy their openings, symmetry, or light direction.
- Include Retrieval expansion in ===CRITERIA=== with synonyms/proxies when catalog may lack exact terms.

PRIORITY ORDER (mandatory in ===CRITERIA=== and ===PROMPT===):
1. User photograph (image 1) — sole authority for doors, windows, light, camera frame; do not verbalize opening coordinates in text.
2. User design intent — every literal brief requirement inside ===PROMPT=== (never by moving openings).
3. Style & retrieval targets — for Agent 2 and styling inside the locked shell.
4. References — inspiration only; never copy their door or window placement.

OPENINGS IN TEXT (mandatory — do NOT locate openings):
- Forbidden in ===CRITERIA=== and ===PROMPT===: door wall names (left/right/back/front), window counts, window wall placement, sizes, or asymmetry notes.
- Required once in ===PROMPT===: preserve all doors, windows, and light exactly as in the attached photograph; image 1 is authoritative; do not relocate, add, remove, or symmetrize openings.
- Door clearance: keep entry path and swing zone clear — without naming which wall the door is on.

PROMPT AUTHORING RULES (mandatory for ===PROMPT===):
- Write a director's brief for a FINISHED furnished interior, not meta-instructions.
- Open ===PROMPT=== with: "A fully furnished [room_type] in [style] style…" using the room type hint and selected style (or style inferred from the brief).
- NEVER open ===PROMPT=== with: "empty room", "empty bedroom", "you need to design", or similar meta phrasing.
- Include EVERY distinct requirement from the user brief (each bullet or line) as concrete design language in the prompt body.
- Room type and style must appear in the first sentence of ===PROMPT===.
- Storage lock in ===CRITERIA===: only when user brief mentions cupboard, wardrobe, closet, armoire, built-in storage, or hidden storage. Otherwise write exactly "Storage lock: none in photo — do not add wardrobe, cupboard, or closet" and omit the Cupboard / wardrobe line. Never invent storage the user did not request.
- Storage placement in ===PROMPT===: only when user brief requests storage — freestanding/proud unit with visible wall, footprint, and clearance; preserve photo built-ins only when observed.
- Ban superficial-only adjectives without placement or material detail.
- Daylight: mood from brief only; light direction comes from image 1 — no compass or window-wall labels.

FRAME LOCK (mandatory in every ===PROMPT=== block):
- The first image sent to the image model is always the user's room photograph.
- Exact same camera position, viewing angle, lens field of view, and aspect ratio as that photograph.
- Full room coverage: show the entire room visible in the input — no crop, zoom-in, tighter framing, or camera relocation.
- No perspective change relative to the user's photo.
- Reference images are style/material/lighting inspiration only — never copy their camera angles or crops.
""".strip()

CRITERIA_FORMAT = r"""===CRITERIA===
Spatial structure lock (from photograph — highest priority):
Openings lock: <preserve all doors/windows as in attached photograph; image 1 authoritative — no door/window wall positions or counts in text>
Door clearance: <swing zone and entry path empty; no furniture blocking door path — no door wall name>
Light: <mood/quality only; no window walls or compass exposure>
Storage lock: <if user brief mentions storage: preserve existing built-in OR add freestanding unit; else write exactly: none in photo — do not add wardrobe, cupboard, or closet>
Cupboard / wardrobe: <only when user brief requests storage — in-room unit with visible wall; footprint; not recessed unless in photo; otherwise omit this line>

User design intent (for Agent 3 prompt and retrieval):
- <bullet list of literal requirements from the user brief>

Style & retrieval targets:
<style, room type, cohesive palette, mood, material family>

Retrieval expansion (when catalog may lack exact terms):
<synonyms, material families, mood proxies, scale cues for search>

Architectural lock (for retrieval and generation):
<preserve user photo openings; reject refs implying different door wall or extra/missing windows; clear entry path>

Room type & 3D structure notes:
<proportions and circulation — no door/window wall coordinates>

Daylight & ambience target:
<mood from brief; light from image 1 only>

Style & material palette:
<free-text>

Functional requirements:
<free-text>

Agent 3 mandate:
- The PROMPT section is the authoritative image-generation brief; references are style-only; image 1 locks openings.

Complementarity guidance for references (up to 3):
Reference 1 should best cover <style / materials without conflicting opening layout vs user photo>.
Reference 2 should best cover <complementary materials or mood>.
Reference 3 should best cover <ambient mood — not catalog opening placement>.
===END==="""

PARSE_AGENT1_JS = r"""const ctx = $('Build Agent 1 request').item.json;

function normalizeOpenRouterResponse(raw) {
  let resp = raw;
  if (resp && resp.body && typeof resp.body === 'object') resp = resp.body;
  if (typeof resp === 'string') {
    try { resp = JSON.parse(resp); } catch (_) {}
  }
  return resp || {};
}

function extractAgent1Content(resp) {
  const r = normalizeOpenRouterResponse(resp);
  if (r.error) {
    return {
      error: r.error,
      content: '',
      debug: { reason: 'openrouter_error', message: r.error.message, code: r.error.code },
    };
  }
  const msg = r.choices && r.choices[0] && r.choices[0].message;
  if (!msg) {
    return { content: '', debug: { reason: 'no_message', keys: Object.keys(r) } };
  }
  let content = msg.content;
  if (Array.isArray(content)) {
    content = content
      .map((p) => (typeof p === 'string' ? p : (p && p.text) || ''))
      .filter(Boolean)
      .join('\n');
  }
  if (typeof content !== 'string') content = content ? String(content) : '';
  return { content: content.trim(), model: r.model, debug: { reason: 'ok', model: r.model } };
}

const resp = normalizeOpenRouterResponse($json);
const extracted = extractAgent1Content(resp);
if (extracted.error) {
  const errMsg = extracted.error.message || 'upstream_error';
  const errCode = extracted.error.code || 502;
  return [{
    json: {
      _error: {
        status: 502,
        body: {
          error: 'agent1_upstream_error',
          code: 'upstream_error',
          upstream_message: errMsg,
          upstream_code: errCode,
        },
      },
      _agent1_parse_debug: extracted.debug,
    },
  }];
}
const content = extracted.content;
if (!content) {
  return [{
    json: {
      _error: {
        status: 502,
        body: { error: 'agent1_empty_response', code: 'upstream_error' },
      },
      _agent1_parse_debug: extracted.debug,
    },
  }];
}

function extractBlock(text, startTag) {
  const startRe = new RegExp(`={3,}\\s*${startTag}\\s*={3,}`, 'i');
  const endRe   = /={3,}\s*END\s*={3,}/i;
  const s = text.search(startRe);
  if (s < 0) return null;
  const after = text.slice(s).replace(startRe, '');
  const e = after.search(endRe);
  if (e < 0) return after.trim();
  return after.slice(0, e).trim();
}

function extractDelimitedBlockLast(text, startTag) {
  const startRe = new RegExp(`={3,}\\s*${startTag}\\s*={3,}`, 'gi');
  const endRe   = /={3,}\s*END\s*={3,}/i;
  let lastStart = -1;
  let lastHeaderLen = 0;
  let m;
  while ((m = startRe.exec(text)) !== null) {
    lastStart = m.index;
    lastHeaderLen = m[0].length;
  }
  if (lastStart < 0) return null;
  const after = text.slice(lastStart + lastHeaderLen);
  const e = after.search(endRe);
  if (e < 0) return after.trim();
  return after.slice(0, e).trim();
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
  const endRe   = /={3,}\s*END\s*={3,}/i;
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

function extractCriteriaSection(criteria, heading) {
  const re = new RegExp(
    heading.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '[^:]*:\\s*\\n([\\s\\S]*?)(?=\\n[A-Za-z][^:\\n]{0,80}:|$)',
    'i'
  );
  const m = (criteria || '').match(re);
  return m ? m[1].trim() : '';
}

function briefTerms(brief) {
  return (brief || '')
    .split(/\n+/)
    .map((line) => line.replace(/^[\s\-*•\d.)]+/, '').trim())
    .filter((t) => t.length >= 3);
}

const MOOD_WORDS = [
  'cozy', 'warm', 'calm', 'serene', 'dramatic', 'moody', 'bright', 'airy',
  'minimal', 'luxurious', 'earthy', 'playful', 'romantic', 'inviting', 'soft',
];

function inferMoodTags(criteria, brief) {
  const text = ((criteria || '') + ' ' + (brief || '')).toLowerCase();
  const found = MOOD_WORDS.filter((w) => text.includes(w));
  if (ctx.style_tag && !found.includes(ctx.style_tag.toLowerCase())) {
    found.push(ctx.style_tag);
  }
  return [...new Set(found)].slice(0, 8);
}

function parseOpeningInventory(_criteria, _promptRaw) {
  // Openings come from image 1 + ARCHITECTURAL_LOCK at generation time — not from
  // Agent 1 text (verbalized door/window locations override the pixel lock).
  return null;
}

function buildOpeningInventoryBlock(inv) {
  if (!inv) return '';
  const lines = ['OPENING INVENTORY (non-negotiable):'];
  if (inv.door_wall) {
    lines.push(
      `Entry door on the ${inv.door_wall} wall only — same position and size as image 1; do not relocate the door.`
    );
  }
  if (inv.window_count != null) {
    const ww = inv.window_walls && inv.window_walls.length
      ? ` on the ${inv.window_walls.join(' and ')} wall(s)`
      : '';
    lines.push(
      `Exactly ${inv.window_count} window opening(s)${ww} as in image 1 — do not add a third window, sidelight, transom, or extra opening on any wall.`
    );
  } else {
    lines.push('Preserve the exact window count and wall placement from image 1 — do not add or remove windows.');
  }
  lines.push(
    'No furniture, tables, consoles, chairs, ottomans, plants, or lamp bases in the door swing zone or blocking the entry path.'
  );
  lines.push(
    'Place corner lamps and floor decor only on corners away from the entry door wall — never in front of the door.'
  );
  return lines.join(' ');
}

const STORAGE_TERM_RE = /\b(cupboard|cupboards|wardrobe|wardrobes|closet|closets|armoire|built-?in\s+storage|hidden\s+storage|storage\s+unit)\b/i;

function userRequestedStorage(userBrief, promptRaw) {
  return STORAGE_TERM_RE.test(userBrief || '') || STORAGE_TERM_RE.test(promptRaw || '');
}

function parseStorageConstraints(criteria, promptRaw, userBrief) {
  if (!userRequestedStorage(userBrief, promptRaw)) return null;

  const src = ((userBrief || '') + '\n' + (promptRaw || '')).toLowerCase();
  const photo_has_built_in = /\b(existing|photograph|photo|image\s*1|visible\s+in|as\s+(seen|shown))[^\n]{0,80}built-?in\b/i.test(src)
    || (
      /\bbuilt-?in\s+(wardrobe|cupboard|closet|storage)\b/i.test(src)
      && /\b(photograph|photo|image\s*1|preserve)\b/i.test(src)
    )
    || (
      /\brecessed\s+(wardrobe|cupboard|closet|storage)\b/i.test(src)
      && /\b(photograph|photo|preserve)\b/i.test(src)
    );

  let placement = 'freestanding_new';
  if (photo_has_built_in && /\bpreserve\b/i.test(src)) {
    placement = 'preserve_photo';
  } else if (photo_has_built_in) {
    placement = 'preserve_photo';
  }

  let host_wall = null;
  const wallM = src.match(
    /(?:storage|cupboard|wardrobe|closet)[^\n]{0,100}?(left|right|back|front|rear)\s+wall/i
  ) || src.match(
    /(?:on|against)\s+the\s+(left|right|back|front|rear)\s+wall[^\n]{0,60}(?:cupboard|wardrobe|closet|storage)/i
  );
  if (wallM) host_wall = wallM[1].replace('rear', 'back');

  let unit_type = null;
  if (/\bcupboard/i.test(src)) unit_type = 'cupboard';
  else if (/\bwardrobe/i.test(src)) unit_type = 'wardrobe';
  else if (/\bcloset/i.test(src)) unit_type = 'closet';
  else if (/\barmoire/i.test(src)) unit_type = 'armoire';
  else unit_type = 'storage';

  const clearance_notes = 'At least 60 cm beside approach sides and 30 cm at the wall; do not block door or windows.';
  let footprint_notes = '';
  const fpM = (promptRaw || '').match(/footprint[:\s]+([^\n]+)/i);
  if (fpM) footprint_notes = fpM[1].trim().slice(0, 120);
  else if (placement === 'freestanding_new') {
    footprint_notes = 'Allocate visible floor depth for the unit; shift other furniture accordingly.';
  }

  return {
    has_storage_in_brief: true,
    photo_has_built_in,
    placement,
    host_wall,
    unit_type,
    clearance_notes,
    footprint_notes,
  };
}

function buildStorageConstraintsBlock(constraints) {
  if (!constraints) return '';
  if (constraints.placement === 'none' && !constraints.has_storage_in_brief) return '';
  const lines = ['STORAGE CONSTRAINTS (non-negotiable):'];
  if (constraints.placement === 'preserve_photo') {
    lines.push(
      'Preserve the existing built-in storage exactly as in image 1 — same wall and recess treatment; do not add a second built-in or freestanding duplicate.'
    );
  } else if (constraints.placement === 'freestanding_new') {
    const wall = constraints.host_wall ? ` on the ${constraints.host_wall} wall` : '';
    const typ = constraints.unit_type || 'storage unit';
    lines.push(
      `Add a freestanding or proud ${typ}${wall} — not recessed, not flush, not built into the wall cavity.`
    );
    lines.push(
      'The host wall surface (paint, texture, trim) must remain visible above and beside the unit.'
    );
    lines.push(constraints.clearance_notes);
    if (constraints.footprint_notes) lines.push(constraints.footprint_notes);
  } else if (constraints.photo_has_built_in) {
    lines.push('Do not add new built-in or wall-flush storage; match image 1 only.');
  }
  lines.push('Never block the entry door, windows, or primary circulation with storage volume.');
  return lines.join(' ');
}

function buildSpatialReq(criteria, openingInventory) {
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

function normalizeAgentPrompt(rawPrompt, ctx, inferredRoom) {
  let prompt = (rawPrompt || '').trim();
  const roomLabel = inferredRoom || ctx.room_hint || 'interior';
  const styleLabel = ctx.style_tag || 'as specified in the brief';
  const bannedOpening =
    /^(\s*)?(you need to design|design an? empty|an? empty\s+(room|bedroom|kitchen|living|dining|bathroom|office))/i;
  let openingRewritten = false;
  if (bannedOpening.test(prompt)) {
    prompt = prompt.replace(bannedOpening, '').trim().replace(/^,\s*/, '');
    prompt = `A fully furnished, photorealistic ${roomLabel} in ${styleLabel} style. ${prompt}`;
    openingRewritten = true;
  }
  const terms = briefTerms(ctx.brief);
  const missing = terms.filter((t) => !prompt.toLowerCase().includes(t.toLowerCase()));
  if (missing.length > 0) {
    prompt += `\n\nUser requirements (mandatory): ${terms.join('; ')}.`;
  }
  if (/\bcorner\s+lamp/i.test(ctx.brief || '') && !/away from the entry door wall/i.test(prompt)) {
    prompt += '\nPlace corner lamps only on corners away from the entry door wall — never in front of the door or blocking the door path.';
  }
  const doorWallRe = /door\s+(on\s+the\s+)?(left|right|back|front|rear)|entry\s+door\s+(on|at|near|along)|door\s+(stays|remains)\s+on|do not\s+(move|relocate)\s+the\s+door|door\s+to\s+any\s+other\s+wall|same\s+position\s+as\s+the\s+photograph/i;
  const doorClearRe = /door\s+swing|door\s+approach\s+zone|blocking\s+(?:door|entry)|no\s+furniture[^\n]{0,40}door|clear[^\n]{0,30}door\s+(?:swing|path)|unobstructed[^\n]{0,20}door/i;
  const windowLightRe = /window and light fidelity|preserve exact window(?:\s+positions)?|do not symmetrize|windows remain on|window fidelity subsection|exact window positions|preserve.*light direction|light direction.*(?:photograph|first image|image 1)|asymmetric(?:\s+window|\s+placement)/i;
  let doorFooterAppended = false;
  let architecturalFooterAppended = false;
  if (!doorWallRe.test(prompt) || !doorClearRe.test(prompt)) {
    prompt += `\n\n__DOOR_LOCK_FOOTER__`;
    doorFooterAppended = true;
  }
  if (!windowLightRe.test(prompt)) {
    prompt += `\n\n__ARCHITECTURAL_FOOTER__`;
    architecturalFooterAppended = true;
  }
  const compassLightRe = /(east|west|north|south)[- ]facing|morning sun|afternoon sun|evening sun/i;
  if (compassLightRe.test(prompt) && !/as (seen|shown|visible) in the photograph|match(es)? the photograph/i.test(prompt)) {
    prompt += '\n\nLight direction must match the user photograph exactly — do not change which wall receives sunlight.';
  }
  return {
    prompt,
    openingRewritten,
    missing_brief_terms: missing,
    brief_term_count: terms.length,
    door_footer_appended: doorFooterAppended,
    architectural_footer_appended: architecturalFooterAppended,
    has_door_lock_language: doorWallRe.test(prompt),
    has_architectural_lock_language: windowLightRe.test(prompt),
  };
}

const criteria = extractBlock(content, 'CRITERIA');
const promptRaw = extractPromptBlock(content);
if (!criteria || !promptRaw) {
  return [{ json: { _error: { status: 502, body: { error: 'agent1_bad_format', code: 'upstream_error', raw: content.slice(0, 500) } } } }];
}
const _looksLikeGenerationBrief = looksLikeGenerationBrief(promptRaw);

const roomWordsRaw = ['bedroom','living room','kitchen','dining room','bathroom','office','study room','kids room','nursery','hallway','entryway','mandir'];
const roomWords = [...roomWordsRaw].sort((a, b) => b.length - a.length);
const lc = (criteria + ' ' + (ctx.brief || '') + ' ' + (ctx.room_hint || '')).toLowerCase();
let inferred_room = ctx.room_hint || null;
if (!inferred_room) {
  for (const w of roomWords) { if (lc.includes(w)) { inferred_room = w; break; } }
}

const retrievalExpansion = extractCriteriaSection(criteria, 'Retrieval expansion');
const ftsParts = [ctx.brief, retrievalExpansion, ctx.style_tag, inferred_room, ctx.room_hint].filter(Boolean);
const fts_search_text = ftsParts.join(' ').replace(/\s+/g, ' ').trim();

const opening_inventory = parseOpeningInventory(criteria, promptRaw);
const storage_constraints = parseStorageConstraints(criteria, promptRaw, ctx.brief);
const normalized = normalizeAgentPrompt(promptRaw, ctx, inferred_room);
const prompt = normalized.prompt;

const mood_tags = inferMoodTags(criteria, ctx.brief);
const spatial_req = buildSpatialReq(criteria, opening_inventory);

const _hasFrameLock = /camera position|full[- ]frame|entire room|no crop/i.test(prompt);
const _hasSpatialCriteria = /spatial structure lock/i.test(criteria);
const _hasArchCriteria = /architectural lock/i.test(criteria);
const _hasAgent3Mandate = /agent 3 mandate/i.test(criteria);
const _hasOpeningsLockCriteria = /openings\s+lock/i.test(criteria);

return [{
  json: {
    ...ctx,
    criteria,
    agent_prompt: prompt,
    inferred_room,
    fts_search_text,
    mood_tags,
    spatial_req,
    opening_inventory,
    storage_constraints,
    _prompt_debug: {
      prompt_len: prompt.length,
      prompt_extraction_mode: 'last_delimited_block',
      looks_like_generation_brief: _looksLikeGenerationBrief,
      opening_inventory: opening_inventory,
      storage_constraints: storage_constraints,
      window_count: opening_inventory ? opening_inventory.window_count : null,
      door_wall: opening_inventory ? opening_inventory.door_wall : null,
      has_frame_lock_language: _hasFrameLock,
      has_spatial_first_criteria: _hasSpatialCriteria,
      has_openings_lock_criteria: _hasOpeningsLockCriteria,
      has_architectural_criteria: _hasArchCriteria,
      has_agent3_mandate_criteria: _hasAgent3Mandate,
      opening_rewritten: normalized.openingRewritten,
      missing_brief_terms: normalized.missing_brief_terms,
      brief_term_count: normalized.brief_term_count,
      door_footer_appended: normalized.door_footer_appended,
      architectural_footer_appended: normalized.architectural_footer_appended,
      has_architectural_lock_language: normalized.has_architectural_lock_language,
      fts_search_len: fts_search_text.length,
      mood_tag_count: mood_tags.length,
    },
  },
}];
""".replace("__DOOR_LOCK_FOOTER__", DOOR_LOCK_FOOTER.replace("\\", "\\\\").replace("`", "\\`")).replace(
    "__ARCHITECTURAL_FOOTER__", ARCHITECTURAL_LAYOUT_FOOTER.replace("\\", "\\\\").replace("`", "\\`")
)


def _js_escape(s: str) -> str:
    # Backticks and `${` must be escaped — SYSTEM is embedded in a JS template literal.
    return (
        s.replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("${", "\\${")
    )


def _validate_build_agent1_js(js: str) -> None:
    """Fail fast if Agent 1 system prompt is not a valid template literal (exec 1603)."""
    if "const SYSTEM = `" not in js:
        raise ValueError(
            "Build Agent 1 request: missing opening backtick on const SYSTEM "
            "(paste agent1_orchestrator.txt via bake_orchestrator_prompts.py, not n8n UI)"
        )
    if re.search(r"const SYSTEM = You are", js):
        raise ValueError(
            "Build Agent 1 request: SYSTEM prompt is raw text, not a quoted template literal"
        )
    if "${styleContext}`;" not in js:
        raise ValueError("Build Agent 1 request: missing ${styleContext} suffix on SYSTEM")
    if "You are Agent 1" not in js:
        raise ValueError("Build Agent 1 request: workbook Agent 1 opener not found in SYSTEM")


def _debug_bake_log(message: str, data: dict | None = None, hypothesis_id: str = "H-bake") -> None:
    # #region agent log
    import time

    log_path = Path(__file__).resolve().parents[1] / "debug-82710b.log"
    payload = {
        "sessionId": "82710b",
        "timestamp": int(time.time() * 1000),
        "location": "bake_orchestrator_prompts.py",
        "message": message,
        "data": data or {},
        "hypothesisId": hypothesis_id,
        "runId": "bake-agent1",
    }
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload) + "\n")
    # #endregion


BUILD_AGENT1_JS_TEMPLATE = r"""const ctx  = $input.item.json;
const b64  = ctx.upload_b64;
const mime = ctx.upload_mime || 'image/jpeg';
const dataUri = `data:${mime};base64,${b64}`;

const styleContext = ctx.style_tag
  ? `The user has selected style: "${ctx.style_tag}". Use this as the primary style direction.`
  : 'No style was pre-selected. Infer the best style from the user brief and room photo.';

const SYSTEM = `__AGENT1_SYSTEM__

${styleContext}`;

const cfg = $('Config').first().json._cfg || {};
const orchModel = (cfg.orch_model || '__OPENROUTER_ORCH_MODEL_DEFAULT__').trim();

function openrouterChatExtras(model) {
  const m = (model || '').toLowerCase();
  if (m.includes('nemotron-nano-12b-v2-vl')) {
    return { reasoning: { enabled: false } };
  }
  return {};
}

const openrouter_body = {
  model: orchModel,
  messages: [
    { role: 'system', content: SYSTEM },
    { role: 'user', content: [
      { type: 'text', text: `User brief:\n${ctx.brief}\n\n${ctx.style_tag ? `Selected style: ${ctx.style_tag}\n\n` : ''}Room type hint: ${ctx.room_hint || '(infer from photo)'}\n\nRoom photograph attached. Ground ALL 3D spatial reasoning in this image — do not assume, only observe.` },
      { type: 'image_url', image_url: { url: dataUri } }
    ]}
  ],
  temperature: 0.2,
  max_tokens: 2048,
  ...openrouterChatExtras(orchModel),
};

return [{ json: { ...ctx, openrouter_body } }];
"""


BUILD_GEMINI_JS = r'''function collectHttpRows() {
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
let ctx;
try {
  ctx = $('Collect image parts').item.json;
} catch (_) {
  ctx = $('Photo-only path').item.json;
}
if (ctx._error) {
  return [{ json: { _error: ctx._error } }];
}
const IMAGE_GEN_CONSTRAINTS = `__FRAME_LOCK__`;
const ARCHITECTURAL_LOCK_BLOCK = `__ARCHITECTURAL_LOCK__`;
const AGENT3_MANDATE_BLOCK = `__AGENT3_MANDATE__`;
const DESIGN_PRINCIPLES_BLOCK = `__DESIGN_PRINCIPLES__`;
const CONFLICT_OVERRIDE = `__CONFLICT_OVERRIDE__`;
const PRIMARY_BRIEF_HEADER = `__PRIMARY_BRIEF_HEADER__`;

function hasFrameLock(text) {
  const t = (text || '').toLowerCase();
  return t.includes('mandatory (every generation)') && t.includes('first attached image');
}

function stripPrependedConstraintBlocks(text) {
  let t = (text || '').trim();
  const patterns = [
    /^OPENING INVENTORY \(non-negotiable\):[\s\S]*?(?=\n\n|$)/im,
    /^STORAGE CONSTRAINTS \(non-negotiable\):[\s\S]*?(?=\n\n|$)/im,
    /\n\nWindow count lock \(mandatory\):[\s\S]*?(?=\n\n[A-Z]|$)/i,
    /\n\nStorage placement \(mandatory\):[\s\S]*?(?=\n\n[A-Z]|$)/i,
  ];
  for (const re of patterns) {
    t = t.replace(re, '').trim();
  }
  return t.replace(/^\n+/, '').trim();
}

let agentPrompt = stripPrependedConstraintBlocks((ctx.agent_prompt || '').trim());
const briefSnippet = (ctx.brief || '').trim();
const styleTag = (ctx.style_tag || '').trim();
const roomHint = (ctx.inferred_room || ctx.room_hint || '').trim();
if (briefSnippet && !agentPrompt.toLowerCase().includes(briefSnippet.slice(0, 40).toLowerCase())) {
  agentPrompt += `\n\nDesign brief: ${briefSnippet}`;
}
if (styleTag && !agentPrompt.toLowerCase().includes(styleTag.toLowerCase())) {
  agentPrompt += `\nStyle: ${styleTag}.`;
}
if (roomHint && !agentPrompt.toLowerCase().includes(roomHint.toLowerCase())) {
  agentPrompt += `\nRoom type: ${roomHint}.`;
}

const coreBrief = hasFrameLock(agentPrompt) ? agentPrompt : IMAGE_GEN_CONSTRAINTS + '\n\n' + agentPrompt;
const refCount = typeof ctx.reference_count === 'number' ? ctx.reference_count : Math.max(0, (ctx.image_parts || []).length - 1);
const refNote = refCount < 3
  ? `Only ${refCount} reference image(s) attached; follow image 1 and the primary generation brief. References are style inspiration only.\n\n`
  : '';

function buildOpeningInventoryBlockFromCtx(inv) {
  if (!inv) return '';
  const lines = ['=== OPENING INVENTORY (non-negotiable — image 1) ==='];
  if (inv.door_wall) {
    lines.push(`Entry door stays on the ${inv.door_wall} wall at the same position as image 1.`);
  }
  if (inv.window_count != null) {
    const ww = inv.window_walls && inv.window_walls.length
      ? ` on the ${inv.window_walls.join(' and ')} wall(s)`
      : '';
    lines.push(`Exactly ${inv.window_count} window opening(s)${ww}; do not add any extra window.`);
  }
  return lines.join('\n');
}

const OPENING_INVENTORY_BLOCK = buildOpeningInventoryBlockFromCtx(ctx.opening_inventory);
const DOOR_CLEARANCE_BLOCK = `__DOOR_CLEARANCE_BLOCK__`;
let WINDOW_COUNT_BLOCK = '';
const inv = ctx.opening_inventory;
if (inv && inv.window_count != null) {
  WINDOW_COUNT_BLOCK = `=== WINDOW COUNT LOCK ===\nRender exactly ${inv.window_count} window opening(s) as in image 1. Forbidden: a third window, sidelights, transoms, or new openings on other walls.`;
}
const SPATIAL_NOTES_BLOCK = (ctx.spatial_req && ctx.spatial_req.notes)
  ? `=== SPATIAL LOCK FROM PHOTO ===\n${ctx.spatial_req.notes}`
  : '';
const stor = ctx.storage_constraints;
const STORAGE_PLACEMENT_BLOCK = (stor && stor.placement !== 'none')
  ? `__STORAGE_PLACEMENT_BLOCK__`
  : '';
let CUPBOARD_FOOTPRINT_BLOCK = '';
if (stor && stor.placement === 'freestanding_new') {
  CUPBOARD_FOOTPRINT_BLOCK = `__CUPBOARD_FOOTPRINT_BLOCK__`;
}

const generationPrompt = [
  ARCHITECTURAL_LOCK_BLOCK,
  OPENING_INVENTORY_BLOCK,
  DOOR_CLEARANCE_BLOCK,
  WINDOW_COUNT_BLOCK,
  SPATIAL_NOTES_BLOCK,
  STORAGE_PLACEMENT_BLOCK,
  CUPBOARD_FOOTPRINT_BLOCK,
  AGENT3_MANDATE_BLOCK,
  refNote,
  DESIGN_PRINCIPLES_BLOCK,
  CONFLICT_OVERRIDE,
  PRIMARY_BRIEF_HEADER,
  coreBrief,
].filter(Boolean).join('\n\n');

const openrouter_body = {
  model,
  messages: [{
    role: 'user',
    content: [{ type: 'text', text: generationPrompt }, ...(ctx.image_parts || [])]
  }]
};

return [{
  json: {
    ...ctx,
    model,
    openrouter_body,
    _prompt_debug: {
      agent_prompt_len: agentPrompt.length,
      generation_prompt_len: generationPrompt.length,
      frame_lock_prepended: generationPrompt.length > agentPrompt.length,
      has_frame_lock_in_agent: hasFrameLock(ctx.agent_prompt || ''),
      has_architectural_lock_block: true,
      has_agent3_mandate_block: true,
      has_design_principles_block: true,
      primary_brief_last: true,
      reference_count: refCount,
      brief_appended: Boolean(briefSnippet),
      has_opening_inventory_block: Boolean(OPENING_INVENTORY_BLOCK),
      has_door_clearance_block: true,
      has_window_count_block: Boolean(WINDOW_COUNT_BLOCK),
      has_spatial_notes_block: Boolean(SPATIAL_NOTES_BLOCK),
      has_storage_block: Boolean(STORAGE_PLACEMENT_BLOCK),
      has_cupboard_footprint_block: Boolean(CUPBOARD_FOOTPRINT_BLOCK),
      storage_placement: stor ? stor.placement : null,
      agent_prompt_stripped_dupes: agentPrompt.length !== ((ctx.agent_prompt || '').trim().length),
    },
  },
}];
'''.replace("__FRAME_LOCK__", _js_escape(FRAME_LOCK)).replace(
    "__ARCHITECTURAL_LOCK__", _js_escape(ARCHITECTURAL_LOCK)
).replace(
    "__AGENT3_MANDATE__", _js_escape(AGENT3_GENERATION_MANDATE)
).replace(
    "__DESIGN_PRINCIPLES__", _js_escape(DESIGN_PRINCIPLES)
).replace(
    "__CONFLICT_OVERRIDE__", _js_escape(CONFLICT_OVERRIDE_LINE)
).replace(
    "__PRIMARY_BRIEF_HEADER__", _js_escape(PRIMARY_BRIEF_HEADER)
).replace(
    "__DOOR_CLEARANCE_BLOCK__", _js_escape(DOOR_CLEARANCE_BLOCK)
).replace(
    "__STORAGE_PLACEMENT_BLOCK__", _js_escape(STORAGE_PLACEMENT_BLOCK)
).replace(
    "__CUPBOARD_FOOTPRINT_BLOCK__", _js_escape(CUPBOARD_FOOTPRINT_BLOCK)
)


BUILD_AGENT2_JS_TEMPLATE = r"""const ctx  = $json;
function dedupePool(arr) {
  const seen = new Set();
  const seenUrl = new Set();
  const out = [];
  for (const r of arr) {
    if (!r || r.id == null) continue;
    const id = r.id.toString().toLowerCase();
    const u = (r.source_url || '').split('?')[0].trim().toLowerCase();
    if (seen.has(id)) continue;
    if (u && seenUrl.has(u)) continue;
    seen.add(id);
    if (u) seenUrl.add(u);
    out.push(r);
  }
  return out;
}
const pool = dedupePool(ctx.pool || []);
const reference_count_target = Math.min(3, pool.length);

const SYSTEM = `__AGENT2_SYSTEM__`;

const cards = pool.map(r => {
  const style   = Array.isArray(r.style_tags) ? r.style_tags.join(',') : '';
  const colors  = Array.isArray(r.dominant_colors) ? r.dominant_colors.join(',') : '';
  const cap     = (r.caption_enhanced || r.caption || '').replace(/\s+/g, ' ').trim().slice(0, 200);

  let spatialLine = '';
  const s = r.spatial_sig || r.spatial_signature;
  if (s && typeof s === 'object') {
    let openingsCount = '';
    if (Array.isArray(s.openings)) {
      let n = 0;
      for (const o of s.openings) {
        if (o && o.type === 'window') n += parseInt(o.approx_count, 10) || 1;
      }
      if (n) openingsCount = ` openings=${n}`;
    }
    spatialLine = `\n  spatial: shape=${s.room_shape||'?'} depth=${s.depth_cues||'?'} ceil=${s.ceiling_height||'?'} win=${s.window_wall||'?'} light=${s.light_direction||'?'}${openingsCount}`;
  }

  return `[id=${r.id}] ${cap}${spatialLine}\n  style:[${style}] colors:[${colors}] room:${r.room_type||'?'}`;
}).join('\n\n');

const pickHint = reference_count_target < 3
  ? `\n\nPick up to ${reference_count_target} reference id(s) from the pool (fewer available).`
  : '';

const user = `===CRITERIA===\n${ctx.criteria}\n===END===\n\n===CANDIDATES===\n${cards}\n===END===${pickHint}`;

const cfg = $('Config').first().json._cfg || {};
const retrieverModel = (cfg.retriever_model || cfg.orch_model || '__OPENROUTER_ORCH_MODEL_DEFAULT__').trim();

function openrouterChatExtras(model) {
  const m = (model || '').toLowerCase();
  if (m.includes('nemotron-nano-12b-v2-vl')) {
    return { reasoning: { enabled: false } };
  }
  return {};
}

const openrouter_body = {
  model: retrieverModel,
  messages: [
    { role: 'system', content: SYSTEM },
    { role: 'user',   content: user }
  ],
  temperature: 0.2,
  max_tokens: 512,
  ...openrouterChatExtras(retrieverModel),
};

return [{ json: { ...ctx, pool, reference_count_target, openrouter_body } }];
"""

PARSE_AGENT2_JS = r"""const ctx  = $('Build Agent 2 request').item.json;
const resp = $json;
const content = (resp.choices && resp.choices[0] && resp.choices[0].message && resp.choices[0].message.content) || '';
const uuidRe = /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/gi;
const matches = (content.match(uuidRe) || []).map(s => s.toLowerCase());

const poolRows = ctx.pool || [];
const poolIds = new Set(poolRows.map(r => r.id.toString().toLowerCase()));
const seen = new Set();
const picks = [];
const target = Math.min(3, poolRows.length);

for (const m of matches) {
  if (!poolIds.has(m)) continue;
  if (seen.has(m)) continue;
  seen.add(m);
  picks.push(m);
  if (picks.length >= target) break;
}

if (picks.length < target && target > 0) {
  const sorted = [...poolRows].sort((a, b) => (b.quality_score || 0) - (a.quality_score || 0));
  for (const r of sorted) {
    const id = r.id.toString().toLowerCase();
    if (seen.has(id)) continue;
    seen.add(id);
    picks.push(id);
    if (picks.length >= target) break;
  }
}

return [{ json: { ...ctx, picked_reference_ids: picks, reference_count: picks.length } }];
"""

ORDER_FETCH_LIST_JS = r"""function collectHttpRows() {
  const items = $input.all();
  if (items.length > 1) {
    return items.map(it => it.json).filter(r => r && r.id != null);
  }
  const j = items[0]?.json ?? $json;
  if (Array.isArray(j)) return j;
  if (Array.isArray(j?.body)) return j.body;
  if (j?.body && typeof j.body === 'object' && j.body.id != null) return [j.body];
  if (j && typeof j === 'object' && j.id != null) return [j];
  return [];
}
const ctx  = $('Parse Agent 2').item.json;
const refs = collectHttpRows();
const byId = {};
refs.forEach(r => { byId[r.id.toString().toLowerCase()] = r.source_url; });

const pickIds = [];
const seenId = new Set();
for (const raw of ctx.picked_reference_ids || []) {
  const id = raw.toString().toLowerCase();
  if (seenId.has(id)) continue;
  seenId.add(id);
  pickIds.push(id);
}
const refUrls = pickIds.map(id => byId[id]).filter(Boolean);
if (!ctx.upload_url) {
  return [{ json: { _error: { status: 500, body: { error: 'upload_url_missing', code: 'internal_error' } } } }];
}
const norm = (u) => (u || '').split('?')[0].trim().toLowerCase();
const seenUrl = new Set();
const uniqueRefUrls = [];
for (const u of refUrls) {
  const n = norm(u);
  if (seenUrl.has(n)) continue;
  seenUrl.add(n);
  uniqueRefUrls.push(u);
}
const urls = [ctx.upload_url, ...uniqueRefUrls];
return urls.map((url, i) => ({
  json: { ...ctx, picked_reference_ids: pickIds, reference_count: uniqueRefUrls.length, idx: i, fetch_url: url },
}));
"""

COLLECT_IMAGE_PARTS_JS = r"""function sniffMime(buf) {
  if (!buf || buf.length < 4) return 'image/jpeg';
  if (buf[0] === 0xff && buf[1] === 0xd8) return 'image/jpeg';
  if (buf[0] === 0x89 && buf[1] === 0x50) return 'image/png';
  return 'image/jpeg';
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
const items = $input.all();
items.sort((a, b) => (a.json.idx ?? 0) - (b.json.idx ?? 0));
const parts = [];
const debug = [];
for (let i = 0; i < items.length; i++) {
  const it = items[i];
  const bin = it.binary?.image;
  if (!bin) continue;
  let buf = await decodeImageBuf(bin, i);
  if (buf && buf[0] === 0x7b) {
    try {
      const p = JSON.parse(buf.toString('utf8'));
      if (p?.type === 'Buffer' && Array.isArray(p.data)) buf = Buffer.from(p.data);
    } catch (_) {}
  }
  const ok = buf && buf.length > 100 && ((buf[0] === 0xff && buf[1] === 0xd8) || (buf[0] === 0x89 && buf[1] === 0x50));
  debug.push({ idx: it.json.idx, bytes: buf?.length || 0, ok });
  if (!ok) continue;
  const mime = sniffMime(buf) || bin.mimeType || it.json.image_mime || 'image/jpeg';
  parts.push({
    type: 'image_url',
    image_url: { url: `data:${mime};base64,${buf.toString('base64')}` }
  });
}
if (parts.length < 1) {
  return [{ json: { _error: { status: 502, body: { error: 'image_parts_invalid', code: 'upstream_error', expected_min: 1, got: parts.length, debug } } } }];
}
const reference_count = Math.max(0, parts.length - 1);
return [{ json: { ...items[0].json, image_parts: parts, reference_count, _image_parts_debug: { count: parts.length, reference_count, debug } } }];
"""

PHOTO_ONLY_PATH_JS = r"""function sniffMime(buf) {
  if (!buf || buf.length < 4) return 'image/jpeg';
  if (buf[0] === 0xff && buf[1] === 0xd8) return 'image/jpeg';
  if (buf[0] === 0x89 && buf[1] === 0x50) return 'image/png';
  return 'image/jpeg';
}
const ctx = $('Parse Agent 1').item.json;
if (!ctx.upload_b64) {
  return [{ json: { _error: { status: 500, body: { error: 'upload_b64_missing', code: 'internal_error' } } } }];
}
const buf = Buffer.from(ctx.upload_b64, 'base64');
const mime = ctx.upload_mime || sniffMime(buf);
const image_parts = [{
  type: 'image_url',
  image_url: { url: `data:${mime};base64,${ctx.upload_b64}` },
}];
return [{
  json: {
    ...ctx,
    picked_reference_ids: [],
    reference_count: 0,
    image_parts,
    skip_agent2: true,
    _image_parts_debug: { count: 1, reference_count: 0, photo_only: true },
  },
}];
"""

CHECK_POOL_JS = r"""function collectHttpRows() {
  const items = $input.all();
  if (items.length > 1) {
    return items.map(it => it.json).filter(r => r && r.id != null);
  }
  const j = items[0]?.json ?? $json;
  if (Array.isArray(j)) return j;
  if (Array.isArray(j?.body)) return j.body;
  if (j?.body && typeof j.body === 'object' && j.body.id != null) return [j.body];
  if (j && typeof j === 'object' && j.id != null) return [j];
  return [];
}
function dedupePool(arr) {
  const seen = new Set();
  const seenUrl = new Set();
  const out = [];
  for (const r of arr) {
    if (!r || r.id == null) continue;
    const id = r.id.toString().toLowerCase();
    const u = (r.source_url || '').split('?')[0].trim().toLowerCase();
    if (seen.has(id)) continue;
    if (u && seenUrl.has(u)) continue;
    seen.add(id);
    if (u) seenUrl.add(u);
    out.push(r);
  }
  return out;
}
function catalogWindowCount(row) {
  const sig = row.spatial_sig || row.spatial_signature;
  if (!sig || typeof sig !== 'object') return null;
  if (Array.isArray(sig.openings)) {
    let n = 0;
    for (const o of sig.openings) {
      if (o && o.type === 'window') n += parseInt(o.approx_count, 10) || 1;
    }
    return n || null;
  }
  return null;
}

function captionWindowCount(row) {
  const cap = ((row.caption_enhanced || row.caption || '') + '').toLowerCase();
  const m = cap.match(/\b(three|3)\s+windows?\b/);
  if (m) return 3;
  const m2 = cap.match(/\b(two|2)\s+windows?\b/);
  if (m2) return 2;
  return null;
}

function refDoorWall(row) {
  const cap = ((row.caption_enhanced || row.caption || '') + '').toLowerCase();
  const m = cap.match(/(?:entry|door)[^\n]{0,60}?(left|right|back|front|rear)\s+wall/);
  return m ? m[1].replace('rear', 'back') : null;
}

function filterPoolByOpenings(rows, openingInventory) {
  if (!openingInventory) return { pool: rows, removed: [] };
  const maxW = openingInventory.window_count;
  const doorWall = openingInventory.door_wall;
  const removed = [];
  const kept = [];
  for (const r of rows) {
    let drop = false;
    let reason = '';
    if (maxW != null) {
      const cw = catalogWindowCount(r) ?? captionWindowCount(r);
      if (cw != null && cw > maxW) {
        drop = true;
        reason = `window_count_${cw}_gt_${maxW}`;
      }
    }
    if (!drop && doorWall) {
      const rd = refDoorWall(r);
      if (rd && rd !== doorWall) {
        drop = true;
        reason = `door_wall_conflict_${rd}`;
      }
    }
    if (drop) removed.push({ id: r.id, reason });
    else kept.push(r);
  }
  return { pool: kept.length ? kept : rows, removed };
}

const BUILTIN_STORAGE_CAP_RE = /\b(built-?in\s+(wardrobe|cupboard|closet|storage)|built-?in\s+against|recessed\s+wardrobe|wall-?to-?wall|flush\s+wardrobe|wardrobe\s+dominates)\b/i;

function refHasBuiltInStorage(row) {
  const cap = ((row.caption_enhanced || row.caption || '') + '').toLowerCase();
  return BUILTIN_STORAGE_CAP_RE.test(cap);
}

function filterPoolByStorage(rows, storageConstraints, openingInventory) {
  const dropBuiltIns = Boolean(openingInventory && !storageConstraints)
    || (storageConstraints && (
      storageConstraints.placement === 'freestanding_new'
      || (storageConstraints.has_storage_in_brief && !storageConstraints.photo_has_built_in)
    ));
  if (!dropBuiltIns) return { pool: rows, removed: [] };
  const removed = [];
  const kept = [];
  for (const r of rows) {
    if (refHasBuiltInStorage(r)) {
      removed.push({ id: r.id, reason: 'builtin_storage_bleed' });
    } else {
      kept.push(r);
    }
  }
  return { pool: kept.length ? kept : rows, removed };
}

const http_items = $input.all().length;
const rawPool = dedupePool(collectHttpRows());
const ctx  = $('Parse Agent 1').item.json;
const filteredOpenings = filterPoolByOpenings(rawPool, ctx.opening_inventory);
const filteredStorage = filterPoolByStorage(
  filteredOpenings.pool,
  ctx.storage_constraints,
  ctx.opening_inventory
);
const pool = filteredStorage.pool;
const pool_empty    = pool.length === 0;
const pool_fallback = pool.length < 3;
return [{
  json: {
    ...ctx,
    pool,
    pool_empty,
    pool_fallback,
    _pool_debug: {
      http_items,
      distinct_raw: rawPool.length,
      distinct: pool.length,
      target: 20,
      meets_target: pool.length >= 20,
      fts: true,
      pool_filtered_removed: filteredOpenings.removed,
      pool_filtered_storage: filteredStorage.removed,
    },
  },
}];
"""


FETCH_POOL_RPC_PARAMS = {
    "method": "POST",
    "url": "https://uzghfpxboktnbcbbthns.supabase.co/rest/v1/rpc/retrieve_candidates_text",
    "sendHeaders": True,
    "headerParameters": {
        "parameters": [
            {"name": "Authorization", "value": "=Bearer {{ $json.bearer_token }}"},
            {"name": "Accept", "value": "application/json"},
            {"name": "Content-Type", "value": "application/json"},
        ]
    },
    "sendBody": True,
    "specifyBody": "json",
    "jsonBody": (
        "={{ JSON.stringify({ "
        "p_search_text: ($json.fts_search_text || $json.brief || '').trim(), "
        "p_room_type: $json.inferred_room || null, "
        "p_style_tag: $json.style_tag || null, "
        "p_user_id: $json.user_id, "
        "p_spatial_req: ($json.spatial_req && typeof $json.spatial_req === 'object' "
        "&& Object.keys($json.spatial_req).length > 0) ? $json.spatial_req : null, "
        "p_mood_tags: (Array.isArray($json.mood_tags) && $json.mood_tags.length > 0) "
        "? $json.mood_tags : null, "
        "p_k: 20 }) }}"
    ),
    "options": {"timeout": 15000},
    "authentication": "genericCredentialType",
    "genericAuthType": "httpHeaderAuth",
}


def patch_build_agent1_system(js: str) -> str:
    dp = _js_escape(DESIGN_PRINCIPLES)
    arch = _js_escape(ARCHITECTURAL_LOCK)
    rules = _js_escape(AGENT1_EXTRA_RULES)
    criteria_esc = _js_escape(CRITERIA_FORMAT)

    # Inject architectural lock before design principles in Agent 1 SYSTEM
    if "ARCHITECTURAL LOCK (apply in criteria" not in js and "ARCHITECTURAL LOCK (mandatory" not in js:
        arch_inject = (
            "\\n\\nARCHITECTURAL LOCK (apply in ===CRITERIA=== and ===PROMPT===):\\n"
            + arch.replace("\n", "\\n")
            + "\\n\\n"
        )
        for anchor in (
            "\\n\\nDESIGN PRINCIPLES (apply in criteria",
            "\n\nDESIGN PRINCIPLES (apply in criteria",
        ):
            if anchor in js:
                js = js.replace(anchor, arch_inject + "DESIGN PRINCIPLES (apply in criteria", 1)
                break

    # Strip legacy symmetry / 50-50 language from baked SYSTEM if present
    for bad in (
        "paired or mirrored furniture",
        "balanced composition on focal walls",
        "use balanced composition on focal walls",
        "50% User brief priorities",
        "50% Aesthetic compatibility",
        "Dual weighting (mandatory",
        "DUAL WEIGHTING (mandatory",
    ):
        js = js.replace(bad, "")

    a3 = _js_escape(AGENT3_GENERATION_MANDATE)
    if "AGENT 3 GENERATION BRIEF" not in js and "Agent 3 generation brief" not in js:
        a3_inject = "\\n\\nAGENT 3 GENERATION BRIEF (write ===PROMPT=== for image model):\\n" + a3.replace("\n", "\\n") + "\\n\\n"
        for anchor in ("\\n\\nARCHITECTURAL LOCK (apply", "\\n\\nDESIGN PRINCIPLES (apply"):
            if anchor in js:
                js = js.replace(anchor, a3_inject + anchor.lstrip("\\n\\n"), 1)
                break

    # Inject design principles + dual-weight rules after styleContext block
    if "DESIGN PRINCIPLES (apply in criteria" not in js:
        inject = (
            "\\n\\nDESIGN PRINCIPLES (apply in criteria and ===PROMPT===):\\n"
            + dp.replace("\n", "\\n")
            + "\\n\\n"
            + rules.replace("\n", "\\n")
            + "\\n\\n"
        )
        for anchor in (
            "${styleContext}\\n\\nPROMPT AUTHORING RULES",
            "${styleContext}\n\nPROMPT AUTHORING RULES",
        ):
            if anchor in js:
                js = js.replace(anchor, "${styleContext}" + inject + "PROMPT AUTHORING RULES", 1)
                break
        else:
            js = js.replace(
                "Output format",
                inject.replace("\\n\\n", "\\n\\n", 1) + "Output format",
                1,
            )

    # Replace or upgrade CRITERIA template (inside JS template literal)
    needs_criteria = "===CRITERIA===" in js and (
        "Spatial structure lock" not in js
        or "Door lock:" not in js
        or "User brief priorities (50%)" in js
        or "Aesthetic compatibility (50%)" in js
    )
    if needs_criteria:
        criteria_js = criteria_esc.replace("\\", "\\\\").replace("`", "\\`").replace("\n", "\\n")
        js = re.sub(
            r"(?<!===PROMPT===\)\n)===CRITERIA===[\s\S]*?===END===",
            criteria_js,
            js,
            count=1,
        )

    if "DOOR LOCK (mandatory in every" not in js:
        door_rules = (
            "\\n\\nDOOR LOCK (mandatory in every ===PROMPT=== block — highest architectural priority):\\n"
            "- Entry door stays on the photographed wall at the photographed position; never relocate, add, or remove the door.\\n"
            "- Forbidden: door on a different wall, relocated entry, copying reference door placement, furniture blocking door swing.\\n"
            "- Door lock subsection in ===PROMPT=== must name the observed door wall before describing windows.\\n"
        )
        for anchor in (
            "ARCHITECTURAL LOCK (windows and light",
            "ARCHITECTURAL LOCK (mandatory in every",
            "FRAME LOCK (mandatory in every ===PROMPT=== block):",
        ):
            if anchor in js:
                js = js.replace(anchor, door_rules + anchor, 1)
                break

    return js


def _ensure_photo_only_node(wf: dict) -> bool:
    nodes = wf.get("nodes", [])
    if any(n.get("name") == "Photo-only path" for n in nodes):
        return False
    # Place near Collect image parts / Fetch image_model
    collect = next((n for n in nodes if n.get("name") == "Collect image parts"), None)
    pos = collect["position"] if collect else [6240, 900]
    nodes.append({
        "parameters": {"jsCode": PHOTO_ONLY_PATH_JS},
        "id": "photo_only_path",
        "name": "Photo-only path",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [pos[0] - 480, pos[1] - 180],
    })
    conns = wf.setdefault("connections", {})
    conns["Photo-only path"] = {
        "main": [[{"node": "Fetch image_model", "type": "main", "index": 0}]]
    }
    # Photo-only still loads image_model config before Build Gemini
    empty = conns.get("Empty pool?", {}).get("main", [[], []])
    if empty and empty[0]:
        empty[0] = [{"node": "Photo-only path", "type": "main", "index": 0}]
    else:
        conns["Empty pool?"] = {
            "main": [
                [{"node": "Photo-only path", "type": "main", "index": 0}],
                [{"node": "Need fallback?", "type": "main", "index": 0}],
            ]
        }
    return True


def main() -> None:
    wf = json.loads(WF_PATH.read_text(encoding="utf-8-sig"))
    changed: list[str] = []
    agent1_js = (
        BUILD_AGENT1_JS_TEMPLATE.replace("__AGENT1_SYSTEM__", _js_escape(AGENT1_ORCHESTRATOR))
        .replace("__OPENROUTER_ORCH_MODEL_DEFAULT__", OPENROUTER_ORCH_MODEL_DEFAULT)
    )
    _validate_build_agent1_js(agent1_js)
    _debug_bake_log(
        "agent1_baked",
        {
            "js_len": len(agent1_js),
            "orchestrator_lines": len(AGENT1_ORCHESTRATOR.splitlines()),
            "has_workbook_opener": AGENT1_ORCHESTRATOR.startswith("You are Agent 1"),
            "template_literal_ok": True,
        },
        "H1",
    )
    agent2_js = (
        BUILD_AGENT2_JS_TEMPLATE.replace("__AGENT2_SYSTEM__", _js_escape(AGENT2_SYSTEM))
        .replace("__OPENROUTER_ORCH_MODEL_DEFAULT__", OPENROUTER_ORCH_MODEL_DEFAULT)
    )

    for node in wf.get("nodes", []):
        name = node.get("name", "")
        if name == "Build Agent 1 request":
            ba1_cur = node["parameters"]["jsCode"]
            if ba1_cur != agent1_js or "openrouterChatExtras" not in ba1_cur:
                node["parameters"]["jsCode"] = agent1_js
                changed.append(name)
        elif name == "Parse Agent 1":
            js = node["parameters"]["jsCode"]
            if (
                "parseOpeningInventory" not in js
                or "buildOpeningInventoryBlock" not in js
                or "parseStorageConstraints" not in js
                or "buildStorageConstraintsBlock" not in js
                or "extractPromptBlock" not in js
                or "userRequestedStorage" not in js
                or "extractAgent1Content" not in js
            ):
                node["parameters"]["jsCode"] = PARSE_AGENT1_JS
                changed.append(name)
        elif name == "Agent 1 (Orchestrator)":
            opts = node["parameters"].setdefault("options", {})
            want = {"timeout": 120000, "retry": {"tryTimes": 2, "waitBetweenTries": 5000}}
            if opts.get("timeout") != want["timeout"] or opts.get("retry") != want["retry"]:
                opts.update(want)
                changed.append(name)
        elif name == "Build Gemini request":
            js = node["parameters"]["jsCode"]
            if (
                "OPENING_INVENTORY_BLOCK" not in js
                or "DOOR_CLEARANCE_BLOCK" not in js
                or "STORAGE_PLACEMENT_BLOCK" not in js
                or "PRIMARY_BRIEF_HEADER" not in js
                or "stripPrependedConstraintBlocks" not in js
            ):
                node["parameters"]["jsCode"] = BUILD_GEMINI_JS
                changed.append(name)
        elif name == "Build Agent 2 request":
            ba2_cur = node["parameters"]["jsCode"]
            if ba2_cur != agent2_js or "openrouterChatExtras" not in ba2_cur:
                node["parameters"]["jsCode"] = agent2_js
                changed.append(name)
        elif name == "Parse Agent 2":
            js = node["parameters"]["jsCode"]
            if "reference_count" not in js or "insufficient_distinct_picks" in js:
                node["parameters"]["jsCode"] = PARSE_AGENT2_JS
                changed.append(name)
        elif name == "Order fetch list":
            js = node["parameters"]["jsCode"]
            if "picked_ids_not_three_unique" in js:
                node["parameters"]["jsCode"] = ORDER_FETCH_LIST_JS
                changed.append(name)
        elif name == "Collect image parts":
            js = node["parameters"]["jsCode"]
            if "reference_count" not in js or "parts.length !== items.length" in js:
                node["parameters"]["jsCode"] = COLLECT_IMAGE_PARTS_JS
                changed.append(name)
        elif name == "Fetch candidate pool":
            params = node["parameters"]
            if params.get("method") != "POST":
                params.update(FETCH_POOL_RPC_PARAMS)
                changed.append(name)
        elif name == "Check pool":
            js = node["parameters"]["jsCode"]
            if (
                "filterPoolByOpenings" not in js
                or "filterPoolByStorage" not in js
                or "ctx.opening_inventory" not in js
            ):
                node["parameters"]["jsCode"] = CHECK_POOL_JS
                changed.append(name)

    if _ensure_photo_only_node(wf):
        changed.append("Photo-only path (new)")

    for node in wf.get("nodes", []):
        if node.get("name") != "Config":
            continue
        js = node["parameters"].get("jsCode", "")
        new_js = js
        for old in (
            "nvidia/nemotron-nano-12b-v2-vl:free",
            "google/gemini-2.0-flash",
        ):
            new_js = new_js.replace(
                f"orch_model:      '{old}'",
                f"orch_model:      '{OPENROUTER_ORCH_MODEL_DEFAULT}'",
            ).replace(
                f"retriever_model: '{old}'",
                f"retriever_model: '{OPENROUTER_ORCH_MODEL_DEFAULT}'",
            )
        if "retriever_model" not in new_js and "orch_model" in new_js:
            new_js = new_js.replace(
                f"orch_model:      '{OPENROUTER_ORCH_MODEL_DEFAULT}'",
                f"orch_model:      '{OPENROUTER_ORCH_MODEL_DEFAULT}',\n"
                f"      retriever_model: '{OPENROUTER_ORCH_MODEL_DEFAULT}'",
                1,
            )
        if new_js != js:
            node["parameters"]["jsCode"] = new_js
            changed.append("Config")

    WF_PATH.write_text(json.dumps(wf, indent=2) + "\n", encoding="utf-8")
    print("Patched:", ", ".join(changed) or "(already up to date)")
    print("Agent1 orchestrator lines:", len(AGENT1_ORCHESTRATOR.splitlines()))
    print("Agent3 mandate lines:", len(AGENT3_GENERATION_MANDATE.splitlines()))
    print("Architectural lock lines:", len(ARCHITECTURAL_LOCK.splitlines()))
    print("Design principles lines:", len(DESIGN_PRINCIPLES.splitlines()))
    print("Agent2 system lines:", len(AGENT2_SYSTEM.splitlines()))


if __name__ == "__main__":
    main()
