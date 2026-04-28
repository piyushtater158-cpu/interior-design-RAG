#!/usr/bin/env python3
"""
Fix retrieve_references workflow:
  1. RPC node: specifyBody string -> json  (PostgREST 404 fix)
  2. Aggregate for response: reshape output to include input style_tag, prompt,
     and all fields needed downstream for generation.
"""
import json, urllib.request

N8N_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    ".eyJzdWIiOiJmMGYzMzNlNi1jNTM0LTQxMDYtYWE0ZS1lZDdkMTIzNDE5YWMiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiZDk3MGQzOTMtMjMzYi00YTMxLWIzODUtMzA4Nzg3ODk4NGE2IiwiaWF0IjoxNzc3MDAzMTQyLCJleHAiOjE3Nzk1MDg4MDB9"
    ".7BxoC8bG6LIKExWd_Jnuuct4y50xfNTiLoVFZe8dcfY"
)
WF_ID = "Ai8JckgkEwez7D8D"

# ── New Aggregate for response code ──────────────────────────────────────────
# Pulls style_tag + prompt from the Validate body context, maps each reference
# to a clean output shape with the input style_tag (singular) instead of the
# DB's style_tags array.
AGGREGATE_CODE = r"""
const ctx  = $('Validate body').first().json;
const refs = $input.all().map(i => i.json);

const shaped = refs.map(r => ({
  id:         r.id,
  url:        r.url,
  style_tag:  ctx.style_tag || null,
  room_type:  r.room_type || ctx.room_type || null,
  caption:    r.caption || null,
  prompt:     ctx.prompt || null,
  similarity: r.similarity || null
}));

return [{ json: shaped }];
""".strip()


def api(method, path, body=None):
    url = "http://localhost:5678/api/v1" + path
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method,
        headers={"X-N8N-API-KEY": N8N_KEY, "Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


# 1. Deactivate
print("Step 1: Deactivating ...")
try:
    api("POST", f"/workflows/{WF_ID}/deactivate")
    print("  Done.")
except Exception as e:
    print("  Warning:", e)

# 2. Fetch
print("Step 2: Fetching workflow ...")
wf = api("GET", f"/workflows/{WF_ID}")

# 3. Fix RPC node (specifyBody string -> json)
print("Step 3: Fixing RPC node body type ...")
for node in wf["nodes"]:
    if node["name"] == "RPC retrieve_references":
        p = node["parameters"]
        if p.get("specifyBody") == "string":
            old_body = p.get("body", "")
            p["specifyBody"] = "json"
            p["jsonBody"] = old_body
            if "body" in p:
                del p["body"]
            print("  specifyBody: string -> json")
        else:
            print("  Already json, skipping.")
        break

# 4. Fix Aggregate for response (add style_tag + prompt to output)
print("Step 4: Fixing Aggregate for response ...")
for node in wf["nodes"]:
    if node["name"] == "Aggregate for response":
        node["parameters"]["jsCode"] = AGGREGATE_CODE
        print("  Updated output shape: id, url, style_tag, room_type, caption, prompt, similarity")
        break

# 5. Push
print("Step 5: Pushing update ...")
payload = {
    "name": wf["name"],
    "nodes": wf["nodes"],
    "connections": wf["connections"],
    "settings": wf.get("settings", {}),
}
result = api("PUT", f"/workflows/{WF_ID}", payload)
print("  Updated at:", result.get("updatedAt", "?"))

# 6. Activate
print("Step 6: Activating ...")
api("POST", f"/workflows/{WF_ID}/activate")
print("  Active!")

# 7. Verify
print("\nStep 7: Verifying ...")
wf2 = api("GET", f"/workflows/{WF_ID}")
print("  Active:", wf2["active"])
for n in wf2["nodes"]:
    if n["name"] == "RPC retrieve_references":
        p = n["parameters"]
        print("  RPC specifyBody:", p.get("specifyBody"))
    if n["name"] == "Aggregate for response":
        code = n["parameters"].get("jsCode", "")
        has_prompt = "prompt" in code
        has_style_tag = "style_tag" in code and "style_tags" not in code.split("style_tag")[0]
        print("  Aggregate has prompt:", has_prompt)
        print("  Aggregate uses input style_tag:", has_style_tag)

print("\nDone! Output schema is now: { references: [{ id, url, style_tag, room_type, caption, prompt, similarity }] }")
