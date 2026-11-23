import json
from pathlib import Path

posts_map = {}
for p_path in ["data/curated_batch_a.json", "data/curated_batch_b.json"]:
    data = json.loads(Path(p_path).read_text(encoding="utf-8"))
    items = data.get("selected", [])
    for item in items:
        p_no = str(item.get("post_no"))
        posts_map[p_no] = item

for i in range(47, 59):
    ep = f"ep{i:03d}"
    s = json.loads(Path("data/episodes", ep, "script.json").read_text(encoding="utf-8"))
    p_no = str(s["source_post_no"])
    post = posts_map.get(p_no)
    print(f"=== {ep} (Post #{p_no}) ===")
    print("Title:", s["source_title"])
    if post:
        print("Author:", post.get("author"))
        print("Body:\n", post.get("body"))
        print("Comments:\n", post.get("comments")[:5])
    else:
        print("Post not found in curated batches")
    print("-" * 50)
