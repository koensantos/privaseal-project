import os
import json
import cv2
import numpy as np
from pdf2image import convert_from_path
from ultralytics import YOLO

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
PDF_FILES = [
    "Generated_Files/employee_onboarding_packet.pdf",
    "Generated_Files/lease_application_packet.pdf",
    "Generated_Files/patient_intake_packet.pdf"
]

OUTPUT_DIR = "outputs"
POPPLER_PATH = r"C:\Users\Koen Santos\poppler\poppler-25.12.0\Library\bin"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# --------------------------------------------------
# LOAD MODEL
# --------------------------------------------------
model = YOLO("yolov8n.pt")

all_results = []

# --------------------------------------------------
# PROCESS EACH PDF
# --------------------------------------------------
for pdf_path in PDF_FILES:

    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    print(f"\nProcessing: {pdf_name}")

    pages = convert_from_path(
        pdf_path,
        dpi=200,
        poppler_path=POPPLER_PATH
    )

    total_pages = len(pages)
    pages_with_detections = 0
    doc_detection_count = 0

    for page_idx, page in enumerate(pages):

        # Convert PDF page directly to OpenCV image
        img = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)

        preds = model(img)

        page_has_detection = False

        for r in preds:
            for box in r.boxes:

                cls = int(box.cls[0])
                conf = float(box.conf[0])
                label = model.names[cls]

                x1, y1, x2, y2 = map(int, box.xyxy[0])

                page_has_detection = True
                doc_detection_count += 1

                all_results.append({
                    "document": pdf_name,
                    "page": page_idx,
                    "type": "visual_pii_candidate",
                    "label": label,
                    "confidence": round(conf, 3),
                    "bbox": [x1, y1, x2, y2]
                })

                # Draw bounding box
                cv2.rectangle(
                    img,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2
                )

                # Draw label
                cv2.putText(
                    img,
                    f"{label} {conf:.2f}",
                    (x1, max(y1 - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    2
                )

        # Save only pages with detections
        if page_has_detection:
            pages_with_detections += 1

            cv2.imwrite(
                f"{OUTPUT_DIR}/{pdf_name}_{page_idx}_detected.png",
                img
            )

    # Summary per PDF
    print(f"{pdf_name}:")
    print(f"  Total Pages: {total_pages}")
    print(f"  Pages With Detections: {pages_with_detections}")
    print(f"  Total Detections: {doc_detection_count}")

# --------------------------------------------------
# SAVE JSON OUTPUT
# --------------------------------------------------
with open(f"{OUTPUT_DIR}/detections.json", "w") as f:
    json.dump(all_results, f, indent=2)

print("\nDone processing all PDFs.")
