import json
from pathlib import Path

for i in range(11, 23):
    ep = f"ep{i:03d}"
    p = Path(f"data/episodes/{ep}/script.json")
    d = json.loads(p.read_text(encoding="utf-8"))
    pno = d.get("source_post_no")
    img_dir = Path(f"data/post_images/{pno}")
    imgs = list(img_dir.glob("*")) if img_dir.exists() else []
    print(f"{ep} [post #{pno}]: {d.get('source_title')} -> {len(imgs)} images: {[x.name for x in imgs]}")
