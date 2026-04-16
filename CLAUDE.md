# PrivaSeal — Claude Context

## Project Overview
PrivaSeal is a privacy-first, fully local (no cloud) end-to-end PII redaction pipeline for scanned documents and images. Built for BIA 678 (Professor Zhang) by Nishvi Patel, Kush Parmar, Connor Marano, and Koen Mitchel Santos.

The core idea: existing redaction tools are cloud-based, which means you have to send private data to process it — defeating the purpose. PrivaSeal runs everything locally.

## Pipeline Stages
1. **OCR Engine** (PaddleOCR) — convert PDF/image → text + bounding boxes — **CURRENT FOCUS**
2. **Text PII Detection** (Microsoft Presidio) — classify entities: names, SSNs, phone numbers, addresses
3. **Visual PII Detection** (YOLOv8) — detect faces and handwritten signatures
4. **Streamlit Dashboard** — human-in-the-loop: upload, review/toggle redactions, download burned-in PDF

## What's Already Built
- `HR Onboarding Packet.py` — generates synthetic 3-page HR onboarding PDFs (fake employee data + synthetic ID card with face photo)
- `Multipage application with ID.py` — generates synthetic 3-page lease application PDFs
- `Patient Intake Multipage packet.py` — generates synthetic 3-page patient intake/medical PDFs
- `Generated Files/` — pre-generated sample PDFs from the above scripts
- `funsd-dataset/` — FUNSD dataset for form layout/spatial analysis
- `wider-face-dataset/` — WIDER FACE dataset for face detection validation

All three generator scripts use Faker for synthetic PII and PIL for image rendering. They produce realistic multi-page PDFs with embedded face photos (loaded from a `faces/` folder).

## What's Built — OCR Engine (`ocr_engine.py`)
The OCR engine is complete and working. Key implementation details:
- `PaddleOCR(use_textline_orientation=False, lang="en")` — orientation classifier disabled; unnecessary for upright docs and caused hangs
- Images are capped at 2000px on the long side before OCR to prevent memory blowout on high-res scans
- PDF pages are converted one at a time (`first_page`/`last_page`) — never all at once — to keep RAM flat
- Result key from PaddleOCR v3.x is `dt_polys` (not `det_polys`)
- Tested on Mac with CPU only — runs but is slow (~30–45s/image including model load). **Recommend running on a machine with a GPU for real throughput.**

## Pipeline Skeleton (`pipeline.py`)
`pipeline.py` is the main orchestrator. It defines the shared data contract and wires all stages together.

**Redaction target schema** (the currency passed between stages):
```python
{ "label": str, "bounding_box": (x1, y1, x2, y2), "page_number": int, "source": str, "confidence": float }
```

**Stage ownership:**
- `stage_ocr()` — **Kush Parmar** — complete, calls `ocr_engine.py`
- `stage_text_pii()` — **Nishvi Patel** — stub, implement with Microsoft Presidio
- `stage_visual_pii()` — **Connor Marano / Koen Santos** — stub, implement with YOLOv8
- Streamlit dashboard (`app.py`) — not started

**To run the pipeline end-to-end:**
```bash
python pipeline.py "Generated Files/employee_onboarding_packet.pdf"
```

## What's NOT Built Yet
Text PII detection (Presidio), visual PII detection (YOLO), and the Streamlit dashboard have not been started.

## OCR Engine — Design Goals
The OCR module needs to:
1. Accept a PDF path or image path as input
2. Convert PDF pages to images (PDFs aren't directly readable by OCR)
3. Run PaddleOCR on each page image
4. Return structured output: a list of `{text, bounding_box, confidence, page_number}` per detected text region

Output format matters — the bounding boxes are what allow downstream stages (Presidio, YOLO) to know *where* on the page to draw redaction boxes.

## OCR Engine — Installation

### Mac (CPU only)
```bash
brew install poppler
pip install paddlepaddle==3.3.1
pip install -r requirements.txt
```

### Windows (GPU — recommended)
```powershell
# 1. Install Poppler for Windows: https://github.com/oschwartz10612/poppler-windows/releases
#    Extract and add the bin/ folder to your PATH

# 2. Install the GPU build of PaddlePaddle (check your CUDA version first: nvcc --version)
# CUDA 11.8:
pip install paddlepaddle-gpu==3.3.1 -i https://www.paddlepaddle.org.cn/packages/stable/cu118/
# CUDA 12.3:
pip install paddlepaddle-gpu==3.3.1 -i https://www.paddlepaddle.org.cn/packages/stable/cu123/

# 3. Install everything else
pip install -r requirements.txt
```

- `paddlepaddle` — deep learning framework PaddleOCR runs on
- `paddleocr` — OCR library, runs fully locally
- `pdf2image` + `poppler` — converts PDF pages to images before OCR
- PaddleOCR model weights (~100MB) are downloaded automatically on first run

## Key Design Decisions
- **High recall over precision** — it's better to over-redact normal words than to miss PII leaking out
- **Processing target** — under 10 seconds per page on standard hardware
- **No cloud calls** — everything runs locally, privacy is the whole point

## Working Style
Kush wants to understand what he's building, not just have code handed to him. Explain the "why" alongside the "what". He's comfortable with Python and understands the high-level concepts (bounding boxes, confidence scores, etc.).
