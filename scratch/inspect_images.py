from pathlib import Path
from PIL import Image

post_dirs = ['108570', '94651', '23641', '20810', '102815', '23184']
for pno in post_dirs:
    p = Path(f"data/post_images/{pno}")
    print(f"\n--- Post #{pno} ---")
    for img in sorted(p.glob("*.jpg")):
        im = Image.open(img)
        print(f"  {img.name}: size={im.size}, format={im.format}")
