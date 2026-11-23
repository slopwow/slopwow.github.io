import json
from pathlib import Path

for ep in ["ep001", "ep005", "ep011", "ep012"]:
    p = Path(f"data/episodes/{ep}/script.json")
    if p.exists():
        data = json.loads(p.read_text(encoding="utf-8"))
        print(f"=== {ep} ===")
        for c in data["cuts"]:
            print(f"Cut {c['cut_index']} (wordless={c.get('wordless')}): {c['visual_prompt']}")
            print(f"  dialogue: [{c.get('speaker')}]: {c.get('dialogue')}")
