import json

for i in [17, 18, 19, 20, 21, 22]:
    ep = f"ep{i:03d}"
    with open(f"data/episodes/{ep}/script.json", "r", encoding="utf-8") as f:
        d = json.load(f)
    print(f"=== {ep}: {d['source_title']} ===")
    for c in d["cuts"]:
        print(f"Cut {c['cut_index']} [{c['layout_slot']} {c['aspect_ratio']}]: chars={c['characters']} speaker={c.get('speaker')} wordless={c.get('wordless')}")
        print(f"  dlg: {repr(c.get('dialogue'))}")
        print(f"  vp: {c.get('visual_prompt')[:100]}...")
