#!/usr/bin/env python3
"""
patch_caption_spatial.py
Extend caption_generate.json to produce both CAPTION and SPATIAL JSON blocks.
"""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).parent.parent
PATH = ROOT / "n8n" / "workflows" / "caption_generate.json"

BUILD_REQUEST_CODE = (
    "const ctx      = $input.item.json;\n"
    "const dataUri  = `data:${ctx.image_mime};base64,${ctx.image_b64}`;\n"
    "const style    = ctx.style_tag;\n"
    "const room     = ctx.room_type;\n"
    "\n"
    "const SYSTEM = `You are a precision interior-design captioner. Your captions are used as semantic retrieval documents.\n"
    "\n"
    "You will receive:\n"
    "- A photograph of an interior design scene\n"
    "- Declared room type: ${room}\n"
    "- Declared design style: ${style}\n"
    "\n"
    "IMPORTANT: You MUST use both the declared room type and declared style in your output. Do not ignore them.\n"
    "\n"
    "Write a single flowing caption of 6-10 sentences. Every sentence must pull its weight. Cover ALL of the following - weave them together naturally, do not use bullet points. The declared style (${style}) and room type (${room}) MUST be named at least once in the prose caption.\n"
    "\n"
    "1. SPATIAL GEOMETRY: room shape, proportions, walls visible, ceiling height/treatment, window/door openings (which wall, size, count), natural light direction and intensity, flooring material, spatial connections.\n"
    "2. FURNITURE & FIXTURES: every piece, placement relative to walls, orientation, scale, built-ins.\n"
    "3. OBJECTS & ACCESSORIES: decorative objects, plants, artwork, soft furnishings, lifestyle props, lighting fixtures.\n"
    "4. MATERIALS & TEXTURES: every surface finish by name (e.g. white-washed oak, honed Carrara marble, brushed brass, limewash plaster, boucle, raw linen).\n"
    "5. COLOUR PALETTE: dominant background tones, accent colours, highlight colours, warm/cool balance.\n"
    "6. ARTIFICIAL LIGHTING: fixture types, positions, colour temperature, whether ambient/task/accent.\n"
    "7. STYLE EXPRESSION (${style}): specific vocabulary, materials, cultural/period references that signal this style.\n"
    "8. MOOD & ATMOSPHERE: emotional register, perceived time of day, lived-in vs staged.\n"
    "\n"
    "Output BOTH blocks in this exact order, no preamble:\n"
    "\n"
    "===CAPTION===\n"
    "<prose caption - MUST name '${style}' and '${room}' at least once each>\n"
    "===END===\n"
    "===SPATIAL===\n"
    "{\n"
    "  \\\"declared_style\\\": \\\"${style}\\\",\n"
    "  \\\"declared_room_type\\\": \\\"${room}\\\",\n"
    "  \\\"style_signals_observed\\\": [\\\"<visible element supporting the declared style>\\\"],\n"
    "  \\\"room_shape\\\": \\\"rectangular|square|L-shaped|irregular\\\",\n"
    "  \\\"perceived_proportions\\\": {\\\"width_to_depth\\\": \\\"wider|deeper|equal\\\"},\n"
    "  \\\"ceiling\\\": {\\\"height\\\": \\\"low|standard|high|vaulted\\\", \\\"treatment\\\": \\\"<string or null>\\\"},\n"
    "  \\\"walls_visible\\\": [\\\"left\\\", \\\"rear\\\"],\n"
    "  \\\"openings\\\": [{\\\"wall\\\": \\\"rear\\\", \\\"type\\\": \\\"window\\\", \\\"approx_count\\\": 1}],\n"
    "  \\\"natural_light\\\": {\\\"direction\\\": \\\"front-left\\\", \\\"intensity\\\": \\\"medium\\\"},\n"
    "  \\\"flooring\\\": {\\\"material\\\": \\\"<string>\\\", \\\"coverage\\\": \\\"<string>\\\"},\n"
    "  \\\"furniture\\\": [{\\\"type\\\": \\\"<string>\\\", \\\"wall_relation\\\": \\\"<string>\\\"}],\n"
    "  \\\"fixed_features\\\": []\n"
    "}\n"
    "===END_SPATIAL===\n"
    "\n"
    "Rules for the SPATIAL block:\n"
    "- 'declared_style' MUST be exactly '${style}' — copy it verbatim.\n"
    "- 'declared_room_type' MUST be exactly '${room}' — copy it verbatim.\n"
    "- 'style_signals_observed': only list elements visible in the image that justify the style. Empty array if none — do NOT fabricate.\n"
    "- All other fields must be based on what is literally visible.\`;\n"
    "\n"
    "const openrouter_body = {\n"
    "  model: 'qwen/qwen3-vl-8b-instruct',\n"
    "  messages: [\n"
    "    { role: 'system', content: SYSTEM },\n"
    "    {\n"
    "      role: 'user',\n"
    "      content: [\n"
    "        { type: 'text', text: `Declared room type: ${room}\\nDeclared design style: ${style}\\n\\nAnalyse this interior design image and produce both the CAPTION and SPATIAL blocks.` },\n"
    "        { type: 'image_url', image_url: { url: dataUri } }\n"
    "      ]\n"
    "    }\n"
    "  ],\n"
    "  temperature: 0.3,\n"
    "  max_tokens: 1800\n"
    "};\n"
    "\n"
    "return [{ json: { ...ctx, openrouter_body } }];"
)

PARSE_RESPONSE_CODE = (
    "const ctx     = $('Build caption request').item.json;\n"
    "const content = ($json.choices && $json.choices[0] && $json.choices[0].message && $json.choices[0].message.content) || '';\n"
    "\n"
    "if (!content) {\n"
    "  return [{ json: { _error: { status: 502, body: { error: 'empty_response', code: 'upstream_error' } } } }];\n"
    "}\n"
    "\n"
    "function extractBlock(text, startRe, endRe) {\n"
    "  const s = text.search(startRe);\n"
    "  if (s < 0) return null;\n"
    "  const after = text.slice(s).replace(startRe, '');\n"
    "  const e = after.search(endRe);\n"
    "  return (e < 0 ? after : after.slice(0, e)).trim();\n"
    "}\n"
    "\n"
    "// Parse CAPTION block\n"
    "const captionStartRe = /={3,}\\s*CAPTION\\s*={3,}/i;\n"
    "const captionEndRe   = /={3,}\\s*END\\s*={3,}/i;\n"
    "const caption = extractBlock(content, captionStartRe, captionEndRe);\n"
    "if (!caption) {\n"
    "  return [{ json: { _error: { status: 502, body: { error: 'missing_caption_block', code: 'parse_error', raw: content.slice(0, 400) } } } }];\n"
    "}\n"
    "\n"
    "// Parse SPATIAL block\n"
    "const spatialStartRe = /={3,}\\s*SPATIAL\\s*={3,}/i;\n"
    "const spatialEndRe   = /={3,}\\s*END_SPATIAL\\s*={3,}/i;\n"
    "const spatialRaw = extractBlock(content, spatialStartRe, spatialEndRe);\n"
    "if (!spatialRaw) {\n"
    "  return [{ json: { _error: { status: 502, body: { error: 'missing_spatial_block', code: 'spatial_parse_error', raw: content.slice(0, 400) } } } }];\n"
    "}\n"
    "\n"
    "let spatial;\n"
    "try {\n"
    "  spatial = JSON.parse(spatialRaw);\n"
    "} catch (e) {\n"
    "  return [{ json: { _error: { status: 502, body: { error: 'spatial_json_invalid', code: 'spatial_parse_error', raw: spatialRaw.slice(0, 400) } } } }];\n"
    "}\n"
    "\n"
    "// Hard validation: declared_style and declared_room_type must match inputs exactly\n"
    "if (spatial.declared_style !== ctx.style_tag) {\n"
    "  return [{ json: { _error: { status: 502, body: { error: 'tag_mismatch', code: 'spatial_parse_error', field: 'declared_style', expected: ctx.style_tag, got: spatial.declared_style } } } }];\n"
    "}\n"
    "if (spatial.declared_room_type !== ctx.room_type) {\n"
    "  return [{ json: { _error: { status: 502, body: { error: 'tag_mismatch', code: 'spatial_parse_error', field: 'declared_room_type', expected: ctx.room_type, got: spatial.declared_room_type } } } }];\n"
    "}\n"
    "\n"
    "// Soft warning: caption should mention style and room (log only, not a hard fail)\n"
    "const lc = caption.toLowerCase();\n"
    "const style_mentioned = lc.includes(ctx.style_tag.toLowerCase());\n"
    "const room_mentioned  = lc.includes(ctx.room_type.toLowerCase());\n"
    "\n"
    "const latency_ms = Date.now() - ctx.started_at_ms;\n"
    "return [{ json: {\n"
    "  caption,\n"
    "  spatial_signature: spatial,\n"
    "  style_tag: ctx.style_tag,\n"
    "  room_type: ctx.room_type,\n"
    "  latency_ms,\n"
    "  caption_mentions_style: style_mentioned,\n"
    "  caption_mentions_room: room_mentioned\n"
    "} }];"
)

RESPOND_200_BODY = (
    "={{ JSON.stringify({ "
    "caption: $json.caption, "
    "spatial_signature: $json.spatial_signature, "
    "style_tag: $json.style_tag, "
    "room_type: $json.room_type, "
    "latency_ms: $json.latency_ms, "
    "caption_mentions_style: $json.caption_mentions_style, "
    "caption_mentions_room: $json.caption_mentions_room "
    "}) }}"
)

def main():
    dry_run = "--check" in sys.argv
    apply   = "--apply" in sys.argv
    if not dry_run and not apply:
        print(__doc__)
        sys.exit(1)

    wf = json.loads(PATH.read_text(encoding="utf-8"))
    nodes_by_id = {n["id"]: n for n in wf["nodes"]}

    patches = [
        ("build_request", "parameters.jsCode",  BUILD_REQUEST_CODE,  "Build caption request -> CAPTION+SPATIAL prompt"),
        ("parse",         "parameters.jsCode",  PARSE_RESPONSE_CODE, "Parse response -> CAPTION+SPATIAL parser with hard tag validation"),
        ("respond_200",   "parameters.responseBody", RESPOND_200_BODY, "Respond 200 -> include spatial_signature"),
    ]

    for node_id, field, new_val, desc in patches:
        node = nodes_by_id.get(node_id)
        if not node:
            print(f"  MISSING node {node_id}")
            continue
        parts = field.split(".")
        obj = node
        for p in parts[:-1]:
            obj = obj[p]
        old = obj[parts[-1]]
        if old == new_val:
            print(f"  ALREADY DONE: {desc}")
        elif dry_run:
            print(f"  would patch: {desc}")
        else:
            obj[parts[-1]] = new_val
            print(f"  patched: {desc}")

    if apply:
        PATH.write_text(json.dumps(wf, indent=2, ensure_ascii=False), encoding="utf-8")
        print("  -> written")
    elif dry_run:
        print("Dry run complete.")

if __name__ == "__main__":
    main()
