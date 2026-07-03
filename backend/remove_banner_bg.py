import sys
import glob
import os
try:
    from rembg import remove
    from PIL import Image
except ImportError:
    print("rembg or PIL not found. Install them first.")
    sys.exit(1)

files = glob.glob(r"c:\infinite gacha\tower-gacha\frontend\public\icons\banners\banner_tier*.png")
for f in files:
    print(f"Processing {f}...")
    img = Image.open(f)
    out = remove(img)
    out.save(f)
    print("Done.")
