
import json
with open('n8n/workflows/retrieve_references.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    
for node in data.get('nodes', []):
    if node.get('name') == 'RPC retrieve_references':
        node['parameters']['jsonBody'] = '={{ JSON.stringify({ q: .embedding_literal ? String(.embedding_literal) : null, room_type: .room_type || null, style_tag: .style_tag || null, k: parseInt(String(.k || 5), 10), prompt: .prompt || null }) }}'
        break

with open('n8n/workflows/retrieve_references.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)
print('Done!')

