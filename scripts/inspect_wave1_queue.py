import json
from pathlib import Path

with open("data/wave1_queue.json", "r", encoding="utf-8") as f:
    queue = json.load(f)

q_by_ep = {item.get("episode_number"): item for item in queue if "episode_number" in item}

for ep_num in range(11, 23):
    item = q_by_ep.get(ep_num)
    if not item:
        print(f"EP.{ep_num}: NOT IN WAVE1_QUEUE")
        continue
    print(f"\n==================== EP.{ep_num} [post #{item['post_no']}]: {item['title']} ====================")
    print(f"body: {item.get('body')}")
    print(f"comic_pitch: {item.get('comic_pitch')}")
    print(f"comments: {item.get('comments')}")
    img_dir = Path(f"data/post_images/{item['post_no']}")
    if img_dir.exists():
        imgs = list(img_dir.glob("*"))
        print(f"images ({len(imgs)}): {[x.name for x in imgs]}")
