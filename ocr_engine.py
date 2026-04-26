import os
import sys
import cv2
import numpy as np
from pdf2image import convert_from_path
from PIL import Image

if sys.platform == "win32":
    _WIN_POPPLER_CANDIDATES = [
        r"C:\poppler-25.12.0\Library\bin",
        r"C:\Release-25.12.0-0\poppler-25.12.0\Library\bin",
        r"C:\Users\Koen Santos\poppler\poppler-25.12.0\Library\bin",
    ]
    _POPPLER_PATH = next((p for p in _WIN_POPPLER_CANDIDATES if os.path.isdir(p)), None)
else:
    _POPPLER_PATH = "/opt/homebrew/bin"

import easyocr
_reader = easyocr.Reader(["en"], gpu=False, verbose=False)


def run_ocr_on_image(image, page_number=1):
    img_array = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    results = []
    try:
        ocr_output = _reader.readtext(img_array)
        for (polygon, text, confidence) in ocr_output:
            xs = [pt[0] for pt in polygon]
            ys = [pt[1] for pt in polygon]
            bbox = (int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys)))
            results.append({
                "text": text,
                "bounding_box": bbox,
                "confidence": round(float(confidence), 4),
                "page_number": page_number,
            })
    except Exception as e:
        print(f"OCR Parsing Error on page {page_number}: {e}")
    return results


def run_ocr_on_pdf(pdf_path, dpi=300):
    from pdf2image import pdfinfo_from_path

    pdf_path = os.path.abspath(pdf_path)

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
            del page_image, pages

        all_results.extend(page_results)
        print(f"  Page {page_num}/{num_pages}: {len(page_results)} text regions found")

    if _tmp_path and os.path.exists(_tmp_path):
        os.remove(_tmp_path)

    return all_results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ocr_engine.py <path_to_pdf_or_image>")
        sys.exit(1)

    path = sys.argv[1]
    if path.lower().endswith(".pdf"):
        results = run_ocr_on_pdf(path)
    else:
        img = Image.open(path).convert("RGB")
        results = run_ocr_on_image(img)

    print(f"\nTotal text regions detected: {len(results)}")
    for r in results[:10]:
        print(f"  Page {r['page_number']} | conf={r['confidence']} | bbox={r['bounding_box']} | text='{r['text']}'")