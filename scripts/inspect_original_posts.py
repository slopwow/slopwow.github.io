import json

post_nos = {
    "ep011": "110173",
    "ep012": "109482",
    "ep013": "23385",
    "ep014": "109167",
    "ep015": "109555",
    "ep016": "97410",
    "ep017": "108678",
    "ep018": "7793",
    "ep019": "96439",
    "ep020": "110883",
    "ep021": "109397",
    "ep022": "107884",
}

with open("data/all_3month_recommend_posts.json", "r", encoding="utf-8") as f:
    all_posts = {p["post_no"]: p for p in json.load(f)}

for ep, pno in post_nos.items():
    post = all_posts.get(pno)
    if not post:
        print(f"=== {ep} [post #{pno}]: NOT FOUND ===")
        continue
    print(f"\n==================== {ep} [post #{pno}] ====================")
    print(f"TITLE: {post['title']}")
    print(f"BODY:\n{post['body']}")
    print(f"COMMENTS: {post['comments'][:5]}")
