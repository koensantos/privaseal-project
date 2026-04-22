import logging
import os
import sys

logging.disable(logging.CRITICAL)
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"

# Poppler path — checks known Windows install locations, falls back to PATH
if sys.platform == "win32":
    _WIN_POPPLER_CANDIDATES = [
        r"C:\poppler-25.12.0\Library\bin",
        r"C:\Release-25.12.0-0\poppler-25.12.0\Library\bin",
        r"C:\Users\Koen Santos\poppler\poppler-25.12.0\Library\bin",
    ]
    _POPPLER_PATH = next((p for p in _WIN_POPPLER_CANDIDATES if os.path.isdir(p)), None)
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

import cv2
import numpy as np

def run_ocr_on_image(image, page_number=1):
    """
    Run OCR on a single PIL image.
    Uses the top-level .ocr() method to ensure coordinates are mapped 
    perfectly back to the original image, even if it crops out sidebars.
    """
    # 1. Convert to BGR format
    img_array = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    results =[]

    try:
        # 2. Use the official .ocr() method. This natively handles all 
        # inverse-scaling and unwarping coordinate mapping!
        ocr_output = _ocr.ocr(img_array)
        
        if not ocr_output:
            return[]

        # PaddleOCR returns a list of pages. We take the first page since we process 1 by 1.
        for page_data in ocr_output:
            if not page_data:
                continue
            
            # 3. Safely handle the newer PaddleX format (List of Dictionaries)
            if isinstance(page_data, dict):
                polys  = page_data.get("dt_polys",[])
                texts  = page_data.get("rec_texts", [])
                scores = page_data.get("rec_scores",[])
                
                for p, t, c in zip(polys, texts, scores):
                    results.append({
                        "text": t,
                        "bounding_box": _polygon_to_bbox(p),
                        "confidence": round(float(c), 4),
                        "page_number": page_number,
                    })
            
            # 4. Safely handle the traditional PaddleOCR format (Nested Lists)
            elif isinstance(page_data, list):
                for line in page_data:
                    if not line or len(line) < 2:
                        continue
                    
                    polygon = line[0]
                    text = ""
                    confidence = 0.99
                    
                    # Extract text and confidence safely to prevent IndexError
                    if isinstance(line[1], (tuple, list)) and len(line[1]) >= 2:
                        text = line[1][0]
                        confidence = line[1][1]
                    elif isinstance(line[1], str):
                        text = line[1]

                    results.append({
                        "text": text,
                        "bounding_box": _polygon_to_bbox(polygon),
                        "confidence": round(float(confidence), 4),
                        "page_number": page_number,
                    })

    except Exception as e:
        print(f"OCR Parsing Error on page {page_number}: {e}")

    return results

def run_ocr_on_pdf(pdf_path, dpi=72):
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

    # pdfinfo on Windows can't handle spaces in paths — copy to a temp file in the
    # project directory (which has no spaces) and clean up after
    _tmp_path = None
    if sys.platform == "win32" and " " in pdf_path:
        _tmp_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_ocr_tmp.pdf")
        with open(pdf_path, "rb") as _src, open(_tmp_path, "wb") as _dst:
            _dst.write(_src.read())
        pdf_path = _tmp_path

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

    if _tmp_path and os.path.exists(_tmp_path):
        os.remove(_tmp_path)

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
