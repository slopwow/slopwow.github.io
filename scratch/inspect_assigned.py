import json
from pathlib import Path
from wow_sloptoon.writer import audit_script_quality
from wow_sloptoon.models import EpisodeScript

for ep_num in range(23, 35):
    ep = f"ep{ep_num:03d}"
    p = Path(f"data/episodes/{ep}/script.json")
    if p.exists():
        script = EpisodeScript.model_validate_json(p.read_text(encoding="utf-8"))
        res = audit_script_quality(script, strict_cinematic=True)
        print(f"{ep}: #{script.source_post_no} - {script.source_title}")
        print(f"  subtitle: {script.subtitle}")
        print(f"  audit passed: {res['passed']}, errors: {res['errors']}, metrics: {res['cinematic_metrics']}")
        for i, c in enumerate(script.cuts, 1):
            print(f"    c{i} ({c.layout_slot}, wordless={c.wordless}, chars={c.characters}): {c.dialogue.replace(chr(10), ' ') if c.dialogue else '[wordless]'}")
    else:
        print(f"{ep}: NOT FOUND")
