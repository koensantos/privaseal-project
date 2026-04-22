import os
import sys
from pdf2image import convert_from_path
from PIL import ImageDraw

if sys.platform == "win32":
    _WIN_POPPLER_CANDIDATES = [
        r"C:\poppler-25.12.0\Library\bin",
        r"C:\Release-25.12.0-0\poppler-25.12.0\Library\bin",
        r"C:\Users\Koen Santos\poppler\poppler-25.12.0\Library\bin",
    ]
    _POPPLER_PATH = next((p for p in _WIN_POPPLER_CANDIDATES if os.path.isdir(p)), None)
else:
    _POPPLER_PATH = "/opt/homebrew/bin"


def redact_pdf(input_path: str, targets: list[dict], output_path: str = None, dpi: int = 72) -> str:
    """
    Draw black boxes over all redaction targets and save as a new PDF.

    Bounding boxes must be in pixel coordinates at the same DPI used during OCR/visual
    detection (default 200) — they will be misaligned if DPI differs.

    Args:
        input_path:  path to the original PDF
        targets:     redaction targets from run_pipeline()
        output_path: where to save the redacted PDF (default: <name>_redacted.pdf)
        dpi:         must match the DPI used in OCR and visual detection

    Returns:
        output_path: absolute path to the saved redacted PDF
    """
    input_path = os.path.abspath(input_path)

    if output_path is None:
        base, _ = os.path.splitext(input_path)
        output_path = base + "_redacted.pdf"

    # Handle Windows paths with spaces (same workaround as ocr_engine.py)
    pdf_path = input_path
    _tmp_path = None
    if sys.platform == "win32" and " " in pdf_path:
        _tmp_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_redact_tmp.pdf")
        with open(pdf_path, "rb") as _src, open(_tmp_path, "wb") as _dst:
            _dst.write(_src.read())
        pdf_path = _tmp_path

    # Group targets by page number
    by_page: dict[int, list] = {}
    for t in targets:
        by_page.setdefault(t["page_number"], []).append(t)

    pages = convert_from_path(pdf_path, dpi=dpi, poppler_path=_POPPLER_PATH)

    first_page = pages[0] if pages else None
    pw, ph = first_page.size if first_page else (1700, 2200)
    PAD = max(8, pw // 160)
    redacted = []
    for page_num, page_img in enumerate(pages, start=1):
        draw = ImageDraw.Draw(page_img)
        for t in by_page.get(page_num, []):
            x1, y1, x2, y2 = t["bounding_box"]
            draw.rectangle([max(0, x1 - PAD), max(0, y1 - PAD), min(pw, x2 + PAD), min(ph, y2 + PAD)], fill="black")
        redacted.append(page_img)

    if redacted:
        redacted[0].save(
            output_path,
            save_all=True,
            append_images=redacted[1:],
            format="PDF",
            resolution=float(dpi),
        )

    if _tmp_path and os.path.exists(_tmp_path):
        os.remove(_tmp_path)

    return output_path
