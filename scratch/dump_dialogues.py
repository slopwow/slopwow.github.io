import json
from pathlib import Path

for ep_num in range(23, 35):
    ep = f"ep{ep_num:03d}"
    p = Path(f"data/episodes/{ep}/script.json")
    data = json.loads(p.read_text(encoding="utf-8"))
    print(f"\n==================== {ep} : #{data['source_post_no']} {data['source_title']} ====================")
    print(f"Subtitle: {data['subtitle']}")
    for i, cut in enumerate(data['cuts'], 1):
        print(f"Cut {i} ({cut['layout_slot']}, wordless={cut['wordless']}, chars={cut['characters']}, speaker={cut['speaker']}):")
        print(f"  Dialogue: {repr(cut['dialogue'])}")
