import json
from pathlib import Path

for i in range(35, 47):
    ep = f"ep{i:03d}"
    p = Path(f"data/episodes/{ep}/script.json")
    data = json.loads(p.read_text(encoding="utf-8"))
    print("=" * 60)
    print(f"EPISODE: {ep} (#{data['source_post_no']})")
    print(f"TITLE: {data['source_title']}")
    print(f"SUBTITLE: {data['subtitle']}")
    print(f"TOOLTIP: {data.get('item_tooltip')}")
    print("-" * 60)
    for c in data["cuts"]:
        print(f"Cut {c['cut_index']} [{c['layout_slot']}, wordless={c.get('wordless')}]:")
        print(f"  Chars: {c['characters']}, Spk: {c.get('speaker')}, Tail: {c.get('tail_target')}")
        print(f"  Dialogue: {repr(c.get('dialogue'))}")
        print(f"  Prompt: {c.get('visual_prompt')}")
        if c.get('item_tooltip'):
            print(f"  Cut Tooltip: {c.get('item_tooltip')}")
        print()
