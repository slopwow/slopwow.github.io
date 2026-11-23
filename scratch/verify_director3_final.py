# -*- coding: utf-8 -*-
import json
from pathlib import Path
from wow_sloptoon.models import EpisodeScript
from wow_sloptoon.writer import audit_script_quality

queue_data = json.loads(Path("data/wave2_queue.json").read_text(encoding="utf-8"))
queue_by_no = {str(item["post_no"]): item for item in queue_data}

print("=== FINAL VERIFICATION OF DIRECTOR-3 SLICE (ep035-ep046) ===")
all_good = True

for ep_num in range(35, 47):
    ep = f"ep{ep_num:03d}"
    script_p = Path(f"data/episodes/{ep}/script.json")
    assert script_p.exists(), f"{script_p} does not exist"

    raw_text = script_p.read_text(encoding="utf-8")
    script = EpisodeScript.model_validate_json(raw_text)

    # 1. Verbatim title check
    q_item = queue_by_no.get(str(script.source_post_no))
    if q_item:
        expected_title = q_item["title"].strip()
        assert script.source_title == expected_title, (
            f"Title mismatch in {ep}: '{script.source_title}' != '{expected_title}'"
        )

    # 2. Strict quality audit
    audit = audit_script_quality(script, strict_cinematic=True)
    assert audit["passed"], f"Audit failed for {ep}: {audit['errors']}"
    assert len(audit["errors"]) == 0, f"Errors in {ep}: {audit['errors']}"
    assert len(audit["warnings"]) == 0, f"Warnings in {ep}: {audit['warnings']}"
    metrics = audit.get("cinematic_metrics", {})
    assert metrics.get("flat_two_shot_cuts", 0) <= 1, f"Flat 2-shots in {ep}: {metrics}"
    assert metrics.get("dynamic_cuts", 0) >= 3, f"Dynamic cuts too low in {ep}: {metrics}"
    assert len(metrics.get("camera_tags", [])) >= 3, f"Camera tags too low in {ep}: {metrics}"

    # 3. Raw prompt pack check
    prompts_p = Path(f"data/raw_cuts/{ep}/prompts.json")
    assert prompts_p.exists(), f"{prompts_p} does not exist"
    p_data = json.loads(prompts_p.read_text(encoding="utf-8"))
    assert len(p_data) == 6, f"Expected 6 prompts in {prompts_p}, got {len(p_data)}"
    for item in p_data:
        assert item.get("prompt"), f"Empty prompt in {prompts_p}"
        assert item.get("target_path"), f"Missing target_path in {prompts_p}"

    # 4. Check tooltips
    cut_tooltips = [c.item_tooltip.item_name for c in script.cuts if c.item_tooltip]
    print(f"[{ep}] #{script.source_post_no} '{script.source_title}'")
    print(f"       Tags: {metrics.get('camera_tags')}")
    print(f"       Dynamic cuts: {metrics.get('dynamic_cuts')}/6, Flat 2-shots: {metrics.get('flat_two_shot_cuts')}")
    print(f"       Tooltips: {cut_tooltips if cut_tooltips else 'None'}")

print("\n>>> ALL 12 EPISODES FULLY VALIDATED AND PASSED! <<<")
