import json
from pathlib import Path

p = Path("data/wave2_queue.json")
queue = json.loads(p.read_text(encoding="utf-8"))
# Find posts for ep035 to ep046
# Each item in queue has 'post_no', 'title', 'body', 'comments', etc.
post_nos = {
    35: "72269", 36: "75174", 37: "72196", 38: "67419",
    39: "70711", 40: "104746", 41: "73199", 42: "87387",
    43: "91005", 44: "69245", 45: "92646", 46: "6229"
}

by_no = {str(item["post_no"]): item for item in queue}

for ep, pno in post_nos.items():
    item = by_no.get(pno)
    print("=" * 60)
    print(f"EP{ep:03d} (#{pno}): {item.get('title') if item else 'NOT FOUND'}")
    if item:
        print(f"Author: {item.get('author')}, Recommends: {item.get('recommends')}")
        print("BODY:")
        print(item.get("body"))
        print("COMMENTS:")
        for c in item.get("comments", [])[:5]:
            print(f"  - {c}")
