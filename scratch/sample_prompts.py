import json
from pathlib import Path

for ep in ['ep001', 'ep005', 'ep010']:
    p = Path(f'data/episodes/{ep}/script.json')
    if p.exists():
        d = json.loads(p.read_text(encoding='utf-8'))
        print(f'=== {ep} ===')
        for i, c in enumerate(d['cuts'][:3], 1):
            print(f"Cut {i} ({c.get('layout_slot')}): {c.get('visual_prompt')}\n")
