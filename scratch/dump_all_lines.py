import json
from pathlib import Path

for i in range(35, 47):
    ep = f"ep{i:03d}"
    p = Path(f"data/episodes/{ep}/script.json")
    data = json.loads(p.read_text(encoding="utf-8"))
    print(f"=== {ep} === #{data['source_post_no']} | {data['source_title']}")
    print(f"  Subtitle: {data['subtitle']}")
    for c in data["cuts"]:
        print(f"  Cut {c['cut_index']} ({c['layout_slot']}, wordless={c.get('wordless')}): chars={c['characters']}, spk={c.get('speaker')}")
        print(f"    Line: {repr(c.get('dialogue'))}")
