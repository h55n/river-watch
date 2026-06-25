import json

with open('data/dashboard.json', 'r') as f:
    d = json.load(f)

for h in d['hotspots']:
    img = h.get('imagery', {})
    if img.get('before_s2_thumbnail_url'):
        old = h.get('data_source', 'unknown')
        h['data_source'] = 'gee_computed'
        print(f"Updated {h['id']}: {old} -> gee_computed")
    else:
        print(f"Skipping {h['id']}: no imagery URL")

with open('data/dashboard.json', 'w') as f:
    json.dump(d, f, indent=2)

print("Dashboard updated.")
