# PrivaSeal

A privacy-first, fully local PII redaction pipeline for scanned documents and images. No cloud — everything runs on your machine.

## Pipeline

1. **OCR** (PaddleOCR) — extract text + bounding boxes from PDF/image
2. **Text PII Detection** (Microsoft Presidio) — classify names, SSNs, phone numbers, addresses, etc.
3. **Visual PII Detection** (YOLOv8) — detect faces and handwritten signatures
4. **Streamlit Dashboard** — review, toggle, and download redacted PDF

---

## Setup

### Prerequisites

**Poppler** is required to convert PDF pages to images.

**Mac:**
```bash
brew install poppler
```

**Windows:**
1. Download the latest release from https://github.com/oschwartz10612/poppler-windows/releases
2. Extract it (e.g. to `C:\poppler-25.12.0\`)
3. Add `C:\poppler-25.12.0\Library\bin` to your `Path` environment variable
4. Open a new terminal to apply the change

---

### 1. Create and activate a virtual environment

**Mac/Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

**Windows:**
```powershell
python -m venv venv
venv\Scripts\activate
```

Your terminal prompt should now show `(venv)`.

---

### 2. Install PaddlePaddle

This must be installed before `requirements.txt` because the package index differs by platform.

**Mac (CPU only):**
```bash
pip install paddlepaddle==3.3.1
```

**Windows — check your CUDA version first:**
```powershell
nvidia-smi
```

Then install the matching build:

```powershell
# CUDA 11.x:
pip install paddlepaddle-gpu==3.3.1 -i https://www.paddlepaddle.org.cn/packages/stable/cu118/

# CUDA 12.x:
pip install paddlepaddle-gpu==3.3.1 -i https://www.paddlepaddle.org.cn/packages/stable/cu118/
```

> If you don't have an NVIDIA GPU, use the CPU build:
> ```powershell
> pip install paddlepaddle==3.3.1
> ```

---

### 3. Install all other dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Download the spaCy language model

Presidio requires this for named entity recognition:

```bash
python -m spacy download en_core_web_lg
```

---

## Running the pipeline

```bash
python pipeline.py "Generated Files/employee_onboarding_packet.pdf"
```

## Running OCR only

```bash
python ocr_engine.py "Generated Files/employee_onboarding_packet.pdf"
```

## Generating synthetic test PDFs

```bash
python "HR Onboarding Packet.py"
python "Multipage application with ID.py"
python "Patient Intake Multipage packet.py"
```

Output goes to `Generated Files/`.
