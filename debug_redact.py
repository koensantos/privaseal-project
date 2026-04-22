"""
Runs the full pipeline and saves pages 2 and 3 as PNGs after redaction.
Run: python debug_redact.py "Generated_Files/employee_onboarding_packet.pdf"
"""
import sys
import cv2
import numpy as np
from pdf2image import convert_from_path
from PIL import ImageDraw
from ocr_engine import run_ocr_on_image, _POPPLER_PATH
from text_pii import stage_text_pii, stage_kv_pii
from visual_pii import _get_model

path = sys.argv[1]
_tmp = None
if sys.platform == "win32" and " " in path:
    _tmp = "_debug_tmp.pdf"
    with open(path, "rb") as _s, open(_tmp, "wb") as _d:
        _d.write(_s.read())
    path = _tmp
pages = convert_from_path(path, dpi=200, poppler_path=_POPPLER_PATH)
print(f"Pages: {len(pages)}, size: {pages[0].size}")

# OCR all pages
all_ocr = []
for page_num, page in enumerate(pages, 1):
    ocr = run_ocr_on_image(page, page_number=page_num)
    all_ocr.extend(ocr)
    print(f"Page {page_num}: {len(ocr)} OCR regions")

# Text PII
text_targets = stage_text_pii(all_ocr)
kv_targets   = stage_kv_pii(all_ocr)
all_targets  = text_targets + kv_targets
print(f"Text PII: {len(text_targets)}, KV: {len(kv_targets)}")

# Visual PII
model = _get_model()
for page_num, page in enumerate(pages, 1):
    img_cv = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)
    for r in model(img_cv, verbose=False):
        for box in r.boxes:
            label = model.names[int(box.cls[0])]
            conf  = round(float(box.conf[0]), 3)
            if label != "person" or conf < 0.3:
                continue
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            all_targets.append({"label": "PERSON", "bounding_box": (x1, y1, x2, y2),
                                 "page_number": page_num, "source": "visual", "confidence": conf})

print(f"Total targets: {len(all_targets)}")

# Build per-page target map
by_page = {}
for t in all_targets:
    by_page.setdefault(t["page_number"], []).append(t)

# Redact and save pages 2 and 3 as PNG
pw, ph = pages[0].size
PAD = max(8, pw // 160)
print(f"PAD = {PAD}px")

for page_num in [2, 3]:
    if page_num > len(pages):
        continue
    page = pages[page_num - 1]
    draw = ImageDraw.Draw(page)
    targets = by_page.get(page_num, [])
    for t in targets:
        x1, y1, x2, y2 = t["bounding_box"]
        draw.rectangle([max(0, x1-PAD), max(0, y1-PAD), min(pw, x2+PAD), min(ph, y2+PAD)], fill="black")
    out = f"redacted_page{page_num}.png"
    page.save(out)
    print(f"Saved {out}  ({len(targets)} targets on this page)")
