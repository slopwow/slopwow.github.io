import json
from pathlib import Path

posts = {}
for qfile in ["data/wave1_queue.json", "data/wave2_queue.json"]:
    data = json.loads(Path(qfile).read_text(encoding="utf-8"))
    items = data if isinstance(data, list) else data.get("posts", data.get("queue", []))
    for item in items:
        pno = str(item.get("post_no") or item.get("no") or "")
        if pno:
            posts[pno] = item

for i in range(47, 59):
    ep = f"ep{i:03d}"
    s = json.loads(Path(f"data/episodes/{ep}/script.json").read_text(encoding="utf-8"))
    pno = str(s["source_post_no"])
    p = posts.get(pno)
    print(f"\n==================== {ep} : #{pno} ====================")
    print(f"Title: {s['source_title']}")
    img_dir = Path(f"data/post_images/{pno}")
    imgs = list(img_dir.glob("*")) if img_dir.exists() else []
    print(f"Images ({len(imgs)}): {[f.name for f in imgs]}")
    if p:
        print(f"Author: {p.get('author')}")
        body = p.get("body", "") or ""
        print(f"Body: {repr(body[:300])}")
        comments = p.get("comments", [])
        print(f"Comments ({len(comments)}):")
        for c in comments[:4]:
            print(f"  - {c}")
    else:
        print("Not found in wave queues")
