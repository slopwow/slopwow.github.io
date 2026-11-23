import json
from pathlib import Path
from wow_sloptoon.models import EpisodeScript
from wow_sloptoon.writer import audit_script_quality

for i in range(35, 47):
    ep = f"ep{i:03d}"
    p = Path(f"data/episodes/{ep}/script.json")
    if not p.exists():
        print(f"{ep}: NOT FOUND")
        continue
    data = json.loads(p.read_text(encoding="utf-8"))
    script = EpisodeScript.model_validate(data)
    audit = audit_script_quality(script, strict_cinematic=True)
    passed = audit["passed"]
    errs = audit["errors"]
    warns = audit["warnings"]
    metrics = audit.get("cinematic_metrics", {})
    print(f"=== {ep} === #{script.source_post_no} | {script.source_title}")
    print(f"  Passed: {passed}, Errors: {len(errs)}, Warnings: {len(warns)}, Metrics: {metrics}")
    for e in errs:
        print(f"    ERR: {e}")
    for w in warns:
        print(f"    WARN: {w}")
