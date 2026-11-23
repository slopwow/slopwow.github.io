import json
from pathlib import Path

for i in range(11, 23):
    ep = f"ep{i:03d}"
    p = Path(f"data/episodes/{ep}/script.json")
    data = json.loads(p.read_text(encoding="utf-8"))
    print(f"\n==================== {ep}: {data['source_title']} ====================")
    print(f"subtitle: {data['subtitle']}")
    for cut in data["cuts"]:
        tip = cut.get("item_tooltip")
        tip_str = f" [TOOLTIP: {tip.get('item_name')}]" if tip else ""
        print(f"  Cut {cut['cut_index']}: chars={cut['characters']} speaker={cut.get('speaker')} wordless={cut.get('wordless')}{tip_str}")
        print(f"    dialogue: {cut.get('dialogue')!r}")
        print(f"    vp: {cut.get('visual_prompt')}")
