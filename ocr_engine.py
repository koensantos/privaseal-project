import logging
import os
import sys

logging.disable(logging.CRITICAL)
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"

# Poppler path — Mac (homebrew) vs Windows
if sys.platform == "win32":
    _POPPLER_PATH = r"C:\Release-25.12.0-0\poppler-25.12.0\Library\bin"
else:
    _POPPLER_PATH = "/opt/homebrew/bin"

import os

# Disable problematic CPU optimizations on Windows
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["OMP_NUM_THREADS"] = "1"


from paddleocr import PaddleOCR
from pdf2image import convert_from_path
from PIL import Image
import numpy as np


# Initialize once at module level — loading the model is expensive (~3s),
# so we don't want to reload it on every function call.
_ocr = PaddleOCR(
    lang="en",
    use_angle_cls=False
)

def _polygon_to_bbox(polygon):
    """Convert PaddleOCR's 4-point polygon to a simple (x1, y1, x2, y2) bounding box."""
    xs = [pt[0] for pt in polygon]
    ys = [pt[1] for pt in polygon]
    return (int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys)))


def run_ocr_on_image(image, page_number=1):
    """
    Run OCR on a single PIL image.

    Returns a list of dicts:
      { text, bounding_box: (x1,y1,x2,y2), confidence, page_number }
    """
    # PaddleOCR hangs/crashes on very large images. Cap the long side at 2000px
    # — PaddleOCR's internal tiling kicks in above that anyway, so accuracy is unaffected.
    max_side = 2000
    w, h = image.size
    if max(w, h) > max_side:
        scale = max_side / max(w, h)
        image = image.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    img_array = np.array(image)
    results = []

    try:
        for page_result in _ocr.predict(img_array):
            polys   = page_result.get("dt_polys", [])
            texts   = page_result.get("rec_texts", [])
            scores  = page_result.get("rec_scores", [])

            # First call: print raw keys so we can verify the structure
            if page_number == 1 and not results:
                print(f"[DEBUG] Result keys: {list(page_result.keys())}")
                if polys:
                    print(f"[DEBUG] First polygon: {polys[0]}")
                    print(f"[DEBUG] First text: {texts[0] if texts else 'n/a'}")
                    print(f"[DEBUG] First score: {scores[0] if scores else 'n/a'}")

            for polygon, text, confidence in zip(polys, texts, scores):
                bbox = _polygon_to_bbox(polygon)
                results.append({
                    "text": text,
                    "bounding_box": bbox,
                    "confidence": round(float(confidence), 4),
                    "page_number": page_number,
                })
    finally:
        del img_array  # release numpy copy immediately after OCR

    return results


def run_ocr_on_pdf(pdf_path, dpi=200):
    """
    Convert each page of a PDF to an image, run OCR on each page.

    dpi=200 is a good balance: high enough for PaddleOCR to read clearly,
    not so high that it's slow. Each page becomes roughly 1650x2140 pixels.

    Pages are converted one at a time to avoid loading the entire PDF into
    RAM simultaneously — each page is freed before the next is loaded.

    Returns a flat list of dicts across all pages:
      { text, bounding_box: (x1,y1,x2,y2), confidence, page_number }
    """
    from pdf2image import pdfinfo_from_path

    pdf_path = os.path.abspath(pdf_path)
    info = pdfinfo_from_path(pdf_path, poppler_path=_POPPLER_PATH)
    num_pages = info["Pages"]

    all_results = []
    for page_num in range(1, num_pages + 1):
        pages = convert_from_path(
            pdf_path, dpi=dpi, poppler_path=_POPPLER_PATH,
            first_page=page_num, last_page=page_num,
        )
        page_image = pages[0]
        try:
            page_results = run_ocr_on_image(page_image, page_number=page_num)
        finally:
            page_image.close()
            del page_image, pages  # free the PIL image before next iteration

        all_results.extend(page_results)
        print(f"  Page {page_num}/{num_pages}: {len(page_results)} text regions found")

    return all_results


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python ocr_engine.py <path_to_pdf_or_image>")
        sys.exit(1)

    path = sys.argv[1]

    if path.lower().endswith(".pdf"):
        print(f"Running OCR on PDF: {path}")
        results = run_ocr_on_pdf(path)
    else:
        print(f"Running OCR on image: {path}")
        img = Image.open(path).convert("RGB")
        results = run_ocr_on_image(img)

    print(f"\nTotal text regions detected: {len(results)}")
    print("\nFirst 10 results:")
    for r in results[:10]:
        print(f"  Page {r['page_number']} | conf={r['confidence']} | bbox={r['bounding_box']} | text='{r['text']}'")
