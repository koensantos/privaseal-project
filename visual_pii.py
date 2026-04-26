import os
import sys
import cv2
import numpy as np
from pdf2image import convert_from_path
from ultralytics import YOLO

if sys.platform == "win32":
    _WIN_POPPLER_CANDIDATES = [
        r"C:\poppler-25.12.0\Library\bin",
        r"C:\Release-25.12.0-0\poppler-25.12.0\Library\bin",
        r"C:\Users\Koen Santos\poppler\poppler-25.12.0\Library\bin",
    ]
    _POPPLER_PATH = next((p for p in _WIN_POPPLER_CANDIDATES if os.path.isdir(p)), None)
else:
    _POPPLER_PATH = "/opt/homebrew/bin"

_model = None

def _get_model():
    global _model
    if _model is None:
        _model = YOLO("yolov8n.pt")
    return _model


def run_visual_pii(pdf_path, dpi=300):
    """
    Detect visual PII (faces, persons, etc.) in a PDF using YOLOv8.

    Returns:
        [{ label, bounding_box: (x1,y1,x2,y2), page_number, source="visual", confidence }, ...]
    """
    pdf_path = os.path.abspath(pdf_path)
    model = _get_model()
    targets = []

    pages = convert_from_path(pdf_path, dpi=dpi, poppler_path=_POPPLER_PATH)

    for page_idx, page in enumerate(pages):
        img = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)
        preds = model(img, verbose=False)

        for r in preds:
            for box in r.boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                label = model.names[cls]

                # Only flag person detections with sufficient confidence —
                # yolov8n is a general COCO model and will misclassify document
                # layouts as laptops, books, etc. at low confidence
                print(f"  [YOLO] label={label} conf={round(conf,3)} bbox={list(map(int, box.xyxy[0]))}")  # ADD THIS

                if label != "person" or conf < 0.30:
                    continue

                x1, y1, x2, y2 = map(int, box.xyxy[0])
                targets.append({
                    "label": "PERSON",
                    "bounding_box": (x1, y1, x2, y2),
                    "page_number": page_idx + 1,
                    "source": "visual",
                    "confidence": round(conf, 3),
                })

    return targets
