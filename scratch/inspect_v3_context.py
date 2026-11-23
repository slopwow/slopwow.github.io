import json
from pathlib import Path

posts = {}
for qfile in ['data/wave1_queue.json', 'data/wave2_queue.json', 'data/scout_curated.json']:
    p = Path(qfile)
    if p.exists():
        data = json.loads(p.read_text(encoding='utf-8'))
        items = data if isinstance(data, list) else data.get('posts', data.get('queue', []))
        for item in items:
            pno = str(item.get('post_no') or item.get('no'))
            posts[pno] = item

our_eps = [
    (23, "19080"), (24, "108570"), (25, "94651"), (26, "23641"),
    (27, "19829"), (28, "20810"), (29, "98610"), (30, "102815"),
    (31, "23097"), (32, "20595"), (33, "23184"), (34, "20899")
]

for ep_num, pno in our_eps:
    print(f"\n==================== EP{ep_num:03d} : #{pno} ====================")
    img_dir = Path(f"data/post_images/{pno}")
    imgs = list(img_dir.glob("*")) if img_dir.exists() else []
    print(f"Images ({len(imgs)}): {[f.name for f in imgs]}")
    post = posts.get(pno)
    if post:
        print(f"Title: {post.get('title')}")
        body = post.get('body', '') or ''
        print(f"Body: {repr(body[:200])}")
        comments = post.get('comments', [])
        print(f"Comments ({len(comments)}): {comments[:2]}")
    else:
        print("Not found in queue files, checking script.json:")
        s_path = Path(f"data/episodes/ep{ep_num:03d}/script.json")
        if s_path.exists():
            s_data = json.loads(s_path.read_text(encoding='utf-8'))
            print(f"Script title: {s_data.get('source_title')}")
            print(f"Script subtitle: {s_data.get('subtitle')}")
