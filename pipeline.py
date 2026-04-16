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

def stage_text_pii(ocr_results: list[dict]) -> list[dict]:
    """
    Classify OCR results and return only those containing PII.

    Args:
        ocr_results: output of stage_ocr()

    Returns:
        [{ label, bounding_box, page_number, source="text", confidence }, ...]

    TODO: implement using Microsoft Presidio.
          For each item in ocr_results, run Presidio NER on item["text"].
          If a PII entity is found, emit a redaction target using item["bounding_box"].
          entity_type values to detect: PERSON, SSN, PHONE_NUMBER, EMAIL_ADDRESS,
          US_DRIVER_LICENSE, CREDIT_CARD, DATE_TIME, LOCATION, US_PASSPORT.
    """
    return []


# ---------------------------------------------------------------------------
# Stage 3 — Visual PII Detection  (TODO: YOLOv8)
# ---------------------------------------------------------------------------

def stage_visual_pii(input_path: str, num_pages: int) -> list[dict]:
    """
    Detect faces and handwritten signatures directly from page images.

    Args:
        input_path: path to the original PDF or image
        num_pages:  number of pages (1 for images)

    Returns:
        [{ label, bounding_box, page_number, source="visual", confidence }, ...]

    TODO: implement using YOLOv8.
          Convert each page to an image (reuse pdf2image like ocr_engine does).
          Run YOLOv8 inference. Labels to detect: FACE, SIGNATURE.
          Return bounding boxes in (x1, y1, x2, y2) pixel coordinates.
    """
    return []


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


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python pipeline.py <path_to_pdf_or_image>")
        sys.exit(1)

    targets = run_pipeline(sys.argv[1])

    if targets:
        print("Redaction targets:")
        for t in targets:
            print(f"  Page {t['page_number']} | {t['source']:6s} | {t['label']:20s} | conf={t['confidence']:.3f} | bbox={t['bounding_box']}")
    else:
        print("No redaction targets found (text/visual PII stages are stubs — not yet implemented).")
