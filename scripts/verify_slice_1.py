import json
from pathlib import Path
from wow_sloptoon.models import EpisodeScript
from wow_sloptoon.writer import audit_script_quality

for i in range(11, 23):
    ep = f"ep{i:03d}"
    script = EpisodeScript.model_validate_json(Path(f"data/episodes/{ep}/script.json").read_text(encoding="utf-8"))
    res = audit_script_quality(script, strict_cinematic=True)
    assert res["passed"] is True, f"{ep} failed passed: {res['errors']}"
    assert res["errors"] == [], f"{ep} has errors: {res['errors']}"
    assert res["warnings"] == [], f"{ep} has warnings: {res['warnings']}"
    assert res["checks"]["cinematic_variety_ok"] is True, f"{ep} cinematic_variety_ok is False"
    print(f"{ep}: PASSED! tags={res['cinematic_metrics']['camera_tags']} dynamic={res['cinematic_metrics']['dynamic_cuts']} flat_2shot={res['cinematic_metrics']['flat_two_shot_cuts']}")
print("\nALL 12 EPISODES PERFECT!")
