"""
Debug: shows OCR regions (blue) and what would be redacted (red) on each page.
Saves debug_pageN.png for each page.
Run: python debug_ocr.py "path/to/file.pdf"
"""
import sys
from PIL import Image, ImageDraw
from pdf2image import convert_from_path
from ocr_engine import run_ocr_on_image, _POPPLER_PATH
from text_pii import stage_text_pii, stage_kv_pii

path = sys.argv[1]
pages = convert_from_path(path, dpi=200, poppler_path=_POPPLER_PATH)
print(f"Pages: {len(pages)}, page size: {pages[0].size}")

all_ocr = []
for page_num, page in enumerate(pages, 1):
    ocr = run_ocr_on_image(page, page_number=page_num)
    all_ocr.extend(ocr)
    print(f"\n=== Page {page_num}: {len(ocr)} OCR regions ===")
    for r in ocr:
        print(f"  {r['bounding_box']}  '{r['text'][:70]}'")

text_targets = stage_text_pii(all_ocr)
kv_targets   = stage_kv_pii(all_ocr)
all_targets  = text_targets + kv_targets

print(f"\nPresidio flags: {len(text_targets)}, KV flags: {len(kv_targets)}")
for t in all_targets:
    print(f"  pg{t['page_number']} {t['source']:4s} {t['label']:20s} {t['bounding_box']}")

# Build per-page maps
ocr_by_page = {}
for r in all_ocr:
    ocr_by_page.setdefault(r["page_number"], []).append(r)
tgt_by_page = {}
for t in all_targets:
    tgt_by_page.setdefault(t["page_number"], []).append(t)

pw = pages[0].size[0]
PAD = max(8, pw // 160)
print(f"\nPAD = {PAD}px  (page width = {pw}px)")

for page_num, page in enumerate(pages, 1):
    debug = page.copy()
    draw  = ImageDraw.Draw(debug)

    for r in ocr_by_page.get(page_num, []):
        x1, y1, x2, y2 = r["bounding_box"]
        draw.rectangle([x1, y1, x2, y2], outline="blue", width=3)

    for t in tgt_by_page.get(page_num, []):
        x1, y1, x2, y2 = t["bounding_box"]
        draw.rectangle([max(0,x1-PAD), max(0,y1-PAD), min(pw,x2+PAD), min(page.size[1],y2+PAD)],
                       outline="red", width=6)

    out = f"debug_page{page_num}.png"
    debug.save(out)
    print(f"Saved {out}")
