from pathlib import Path
from PIL import Image

for ep, pno in [
    ("ep011", "110173"),
    ("ep012", "109482"),
    ("ep013", "23385"),
    ("ep014", "109167"),
    ("ep015", "109555"),
    ("ep016", "97410"),
    ("ep017", "108678"),
    ("ep018", "7793"),
    ("ep019", "96439"),
    ("ep020", "110883"),
    ("ep021", "109397"),
    ("ep022", "107884"),
]:
    img_dir = Path(f"data/post_images/{pno}")
    if not img_dir.exists():
        print(f"{ep} [post #{pno}]: NO DIR")
        continue
    imgs = sorted(list(img_dir.glob("*.jpg")))
    print(f"\n{ep} [post #{pno}]: {len(imgs)} images")
    for img in imgs:
        with Image.open(img) as im:
            print(f"  {img.name}: format={im.format}, size={im.size}, mode={im.mode}")
