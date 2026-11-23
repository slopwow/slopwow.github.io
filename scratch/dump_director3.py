import json
from pathlib import Path

for i in range(35, 47):
    ep = f"ep{i:03d}"
    p = Path(f"data/episodes/{ep}/script.json")
    data = json.loads(p.read_text(encoding="utf-8"))
    print(f"==================== {ep} ====================")
    print(f"Title: {data.get('source_title')}")
    print(f"Subtitle: {data.get('subtitle')}")
    print(f"Post No: {data.get('source_post_no')}, URL: {data.get('source_url')}")
    print(f"Item Tooltip: {data.get('item_tooltip')}")
    print("Cuts:")
    for c in data.get("cuts", []):
        chars = c.get("characters", [])
        print(f"  Cut {c.get('cut_index')} (slot={c.get('layout_slot')}, wordless={c.get('wordless')}):")
        print(f"    Chars: {chars}, Speaker: {c.get('speaker')}, Tail: {c.get('tail_target')}")
        print(f"    Dialogue: {repr(c.get('dialogue'))}")
        print(f"    Prompt: {c.get('visual_prompt')[:120]}...")
