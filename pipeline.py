"""
PrivaSeal — main pipeline orchestrator.

Data flow:
  PDF/image → OCR → text PII detection → visual PII detection → redaction targets

Redaction target schema (shared contract between all stages):
  {
    "label":       str,   # e.g. "PERSON", "SSN", "FACE", "SIGNATURE"
    "bounding_box": (x1, y1, x2, y2),
    "page_number":  int,
    "source":       str,  # "text" | "visual"
    "confidence":   float,
  }
"""

import os
from ocr_engine import run_ocr_on_image, run_ocr_on_pdf


# ---------------------------------------------------------------------------
# Stage 1 — OCR
# ---------------------------------------------------------------------------

def stage_ocr(input_path: str) -> list[dict]:
    """
    Convert PDF or image to a list of OCR results.

    Returns:
        [{ text, bounding_box, confidence, page_number }, ...]
    """
    if input_path.lower().endswith(".pdf"):
        return run_ocr_on_pdf(input_path)
    else:
        from PIL import Image
        img = Image.open(input_path).convert("RGB")
        return run_ocr_on_image(img, page_number=1)


# ---------------------------------------------------------------------------
# Stage 2 — Text PII Detection  (TODO: Microsoft Presidio)
# ---------------------------------------------------------------------------

from text_pii import stage_text_pii as detect_text_pii

def stage_text_pii(ocr_results: list[dict]) -> list[dict]:
    return detect_text_pii(ocr_results)


# ---------------------------------------------------------------------------
# Stage 3 — Visual PII Detection  (TODO: YOLOv8)
# ---------------------------------------------------------------------------

def stage_visual_pii(input_path: str, num_pages: int) -> list[dict]:
    """
    Detect visual PII (faces, persons) directly from page images using YOLOv8.

    Args:
        input_path: path to the original PDF or image
        num_pages:  number of pages (1 for images)

    Returns:
        [{ label, bounding_box, page_number, source="visual", confidence }, ...]
    """
    from visual_pii import run_visual_pii
    if input_path.lower().endswith(".pdf"):
        return run_visual_pii(input_path)
    else:
        from PIL import Image
        import cv2
        import numpy as np
        from ultralytics import YOLO
        from visual_pii import _get_model
        model = _get_model()
        img = cv2.cvtColor(np.array(Image.open(input_path).convert("RGB")), cv2.COLOR_RGB2BGR)
        preds = model(img, verbose=False)
        targets = []
        for r in preds:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                targets.append({
                    "label": model.names[int(box.cls[0])].upper(),
                    "bounding_box": (x1, y1, x2, y2),
                    "page_number": 1,
                    "source": "visual",
                    "confidence": round(float(box.conf[0]), 3),
                })
        return targets


# ---------------------------------------------------------------------------
# Pipeline orchestrator
# ---------------------------------------------------------------------------

def run_pipeline(input_path: str) -> list[dict]:
    """
    Run the full PrivaSeal pipeline on a PDF or image.

    Returns a flat list of redaction targets across all pages:
        [{ label, bounding_box, page_number, source, confidence }, ...]
    """
    input_path = os.path.abspath(input_path)
    print(f"\n[Pipeline] Input: {input_path}")

    # Stage 1 — OCR
    print("[Pipeline] Stage 1: OCR")
    ocr_results = stage_ocr(input_path)
    print(f"  {len(ocr_results)} text regions extracted")

    # Stage 2 — Text PII
    print("[Pipeline] Stage 2: Text PII detection")
    text_targets = stage_text_pii(ocr_results)
    print(f"  {len(text_targets)} text PII regions flagged")

    # Stage 3 — Visual PII
    print("[Pipeline] Stage 3: Visual PII detection")
    num_pages = max((r["page_number"] for r in ocr_results), default=1)
    visual_targets = stage_visual_pii(input_path, num_pages)
    print(f"  {len(visual_targets)} visual PII regions flagged")

    # Merge
    all_targets = text_targets + visual_targets
    print(f"[Pipeline] Done — {len(all_targets)} total redaction targets\n")
    return all_targets


def run_pipeline_and_redact(input_path: str, output_path: str = None, dpi: int = 72) -> tuple[list[dict], str]:
    """
    End-to-end pipeline that converts each PDF page to an image ONCE and reuses
    those same images for OCR, visual detection, and redaction — guaranteeing
    that all bounding boxes are in the same coordinate space.

    Returns:
        (targets, output_path)
    """
    import sys
    import cv2
    import numpy as np
    from pdf2image import convert_from_path
    from PIL import ImageDraw
    from ocr_engine import run_ocr_on_image, _POPPLER_PATH
    from visual_pii import _get_model

    input_path = os.path.abspath(input_path)

    if output_path is None:
        base, _ = os.path.splitext(input_path)
        output_path = base + "_redacted.pdf"

    print(f"\n[Pipeline] Input: {input_path}")

    # Handle Windows paths with spaces
    pdf_path = input_path
    _tmp_path = None
    if sys.platform == "win32" and " " in pdf_path:
        _tmp_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_pipeline_tmp.pdf")
        with open(pdf_path, "rb") as _src, open(_tmp_path, "wb") as _dst:
            _dst.write(_src.read())
        pdf_path = _tmp_path

    # Convert all pages once — every stage shares these images
    pages = convert_from_path(pdf_path, dpi=dpi, poppler_path=_POPPLER_PATH)

    # Stage 1 — OCR
    print("[Pipeline] Stage 1: OCR")
    ocr_results = []
    for page_num, page_img in enumerate(pages, 1):
        page_ocr = run_ocr_on_image(page_img, page_number=page_num)
        ocr_results.extend(page_ocr)
        print(f"  Page {page_num}/{len(pages)}: {len(page_ocr)} text regions found")
    print(f"  {len(ocr_results)} text regions total")

    # Stage 2 — Text PII
    print("[Pipeline] Stage 2: Text PII detection")
    text_targets = stage_text_pii(ocr_results)
    print(f"  {len(text_targets)} Presidio regions flagged")
    from text_pii import stage_kv_pii, stage_regex_pii, stage_merged_label_pii
    kv_targets = stage_kv_pii(ocr_results)
    print(f"  {len(kv_targets)} key-value regions flagged")
    merged_targets = stage_merged_label_pii(ocr_results)
    print(f"  {len(merged_targets)} merged label+value regions flagged")
    regex_targets = stage_regex_pii(ocr_results)
    print(f"  {len(regex_targets)} regex-pattern regions flagged")
    text_targets = text_targets + kv_targets + merged_targets + regex_targets

    # Stage 3 — Visual PII on the same page images
    print("[Pipeline] Stage 3: Visual PII detection")
    model = _get_model()
    visual_targets = []
    for page_num, page_img in enumerate(pages, 1):
        img_cv = cv2.cvtColor(np.array(page_img), cv2.COLOR_RGB2BGR)
        for r in model(img_cv, verbose=False):
            for box in r.boxes:
                label = model.names[int(box.cls[0])]
                conf = round(float(box.conf[0]), 3)
                if label != "person" or conf < 0.45:
                    continue
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                visual_targets.append({
                    "label": "PERSON",
                    "bounding_box": (x1, y1, x2, y2),
                    "page_number": page_num,
                    "source": "visual",
                    "confidence": conf,
                })
    print(f"  {len(visual_targets)} visual PII regions flagged")

    # Stage 4 — ID card whole-region redaction
    from id_card_region import find_id_card_regions
    page_sizes = {i + 1: p.size for i, p in enumerate(pages)}
    id_card_targets = find_id_card_regions(ocr_results, visual_targets, page_sizes)
    print(f"[Pipeline] Stage 4: ID-card region detection")
    print(f"  {len(id_card_targets)} ID-card regions flagged")

    all_targets = text_targets + visual_targets + id_card_targets
    print(f"[Pipeline] Done — {len(all_targets)} total redaction targets")

    # Redact the same page images in-place
    by_page: dict[int, list] = {}
    for t in all_targets:
        by_page.setdefault(t["page_number"], []).append(t)

    pw, ph = pages[0].size
    PAD = max(8, pw // 160)  # ~30px at 4723px width, scales with actual page size
    for page_num, page_img in enumerate(pages, 1):
        draw = ImageDraw.Draw(page_img)
        for t in by_page.get(page_num, []):
            x1, y1, x2, y2 = t["bounding_box"]
            draw.rectangle([max(0, x1 - PAD), max(0, y1 - PAD), min(pw, x2 + PAD), min(ph, y2 + PAD)], fill="black")

    pages[0].save(
        output_path,
        save_all=True,
        append_images=pages[1:],
        format="PDF",
        resolution=float(dpi),
    )
    print(f"[Pipeline] Redacted PDF saved: {output_path}\n")

    if _tmp_path and os.path.exists(_tmp_path):
        os.remove(_tmp_path)

    return all_targets, output_path


def stage_redact(input_path: str, targets: list[dict], output_path: str = None) -> str:
    from redactor import redact_pdf
    return redact_pdf(input_path, targets, output_path)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python pipeline.py <path_to_pdf_or_image>")
        sys.exit(1)

    targets, out = run_pipeline_and_redact(sys.argv[1])

    print("Redaction targets:")
    for t in targets:
        print(f"  Page {t['page_number']} | {t['source']:6s} | {t['label']:20s} | conf={t['confidence']:.3f} | bbox={t['bounding_box']}")
