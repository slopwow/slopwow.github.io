import json
for i in range(11, 23):
    ep = f"ep{i:03d}"
    with open(f"data/episodes/{ep}/script.json", "r", encoding="utf-8") as f:
        d = json.load(f)
    print(f"*** {ep}: {d['source_title']} ***")
    print(f"Subtitle: {d['subtitle']}")
    for c in d["cuts"]:
        tip = f" (TOOLTIP: {c['item_tooltip']['item_name']})" if c.get("item_tooltip") else ""
        print(f"  Cut {c['cut_index']}: {c['characters']} | speaker={c.get('speaker')} | wordless={c.get('wordless')}{tip}")
        print(f"    Dlg: {repr(c.get('dialogue'))}")
