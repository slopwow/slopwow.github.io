import json
from pathlib import Path
from wow_sloptoon.models import EpisodeScript
from wow_sloptoon.writer import audit_script_quality

for i in range(11, 23):
    ep = f"ep{i:03d}"
    p = Path(f"data/episodes/{ep}/script.json")
    if not p.exists():
        print(f"{ep}: MISSING")
        continue
    script = EpisodeScript.model_validate_json(p.read_text(encoding="utf-8"))
    audit = audit_script_quality(script, strict_cinematic=True)
    print(f"=== {ep}: {script.source_title} ===")
    print(f"  subtitle: {script.subtitle}")
    print(f"  audit passed={audit['passed']}, errors={len(audit['errors'])}, cinematic_variety_ok={audit.get('cinematic_variety_ok')}")
    if audit["errors"]:
        for e in audit["errors"]:
            print(f"    ERROR: {e}")
    for cut in script.cuts:
        chars = ",".join(cut.characters)
        print(f"    Cut {cut.cut_index} [{cut.layout_slot} {cut.aspect_ratio}] chars=({chars}) wordless={cut.wordless}")
        print(f"      speaker={cut.speaker}, dlg={cut.dialogue!r}")
        print(f"      vp={cut.visual_prompt[:120]}...")
