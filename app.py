"""
PrivaSeal Streamlit dashboard.

Run with:  streamlit run app.py
"""

import io
import tempfile
from pathlib import Path

import streamlit as st
from PIL import Image
from pdf2image import convert_from_bytes

from pipeline import run_pipeline_and_redact
from ocr_engine import _POPPLER_PATH


ALLOWED_TYPES = ["pdf", "png", "jpg", "jpeg"]
IMAGE_EXTS = {".png", ".jpg", ".jpeg"}
PREVIEW_DPI = 100


@st.dialog("Confirm download")
def confirm_download():
    st.write(f"Save **{st.session_state['out_name']}** to your computer?")
    if st.download_button(
        "Download redacted PDF",
        data=st.session_state["out_bytes"],
        file_name=st.session_state["out_name"],
        mime="application/pdf",
        type="primary",
    ):
        st.rerun()


def _process(uploaded_file) -> None:
    original_name = Path(uploaded_file.name).stem
    suffix = Path(uploaded_file.name).suffix.lower()

    repo_dir = Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory(dir=str(repo_dir)) as tmp:
        tmp = Path(tmp)
        in_pdf = tmp / "input.pdf"

        if suffix == ".pdf":
            in_pdf.write_bytes(uploaded_file.getvalue())
        elif suffix in IMAGE_EXTS:
            img = Image.open(uploaded_file).convert("RGB")
            img.save(in_pdf, "PDF")
        else:
            st.error(f"Unsupported file type: {suffix}")
            return

        out_pdf = tmp / "output.pdf"
        progress_bar = st.progress(0.0, text="Starting…")

        def cb(frac: float, msg: str) -> None:
            progress_bar.progress(min(max(frac, 0.0), 1.0), text=msg)

        run_pipeline_and_redact(
            input_path=str(in_pdf),
            output_path=str(out_pdf),
            progress_callback=cb,
        )

        out_bytes = out_pdf.read_bytes()

    progress_bar.empty()

    preview_pages = convert_from_bytes(
        out_bytes, dpi=PREVIEW_DPI, poppler_path=_POPPLER_PATH
    )
    preview_png = []
    for page in preview_pages:
        buf = io.BytesIO()
        page.save(buf, format="PNG")
        preview_png.append(buf.getvalue())

    st.session_state["out_bytes"] = out_bytes
    st.session_state["out_name"] = f"{original_name}_redacted.pdf"
    st.session_state["preview_png"] = preview_png
    st.session_state["source_id"] = uploaded_file.file_id


st.set_page_config(page_title="PrivaSeal", page_icon="🔒")
st.title("PrivaSeal")
st.caption("Local PII redaction for PDFs and images. Nothing leaves your machine.")

uploaded = st.file_uploader(
    "Upload a PDF or image",
    type=ALLOWED_TYPES,
    accept_multiple_files=False,
)

if uploaded is not None and st.session_state.get("source_id") != uploaded.file_id:
    for k in ("out_bytes", "out_name", "preview_png", "source_id"):
        st.session_state.pop(k, None)

if st.button("Redact", type="primary", disabled=uploaded is None):
    try:
        _process(uploaded)
    except Exception as e:
        st.error(f"Pipeline failed: {e}")

if "preview_png" in st.session_state:
    st.subheader("Preview")
    st.caption(f"{len(st.session_state['preview_png'])} page(s) — scroll to review before downloading.")

    if st.button("Download redacted PDF", type="primary"):
        confirm_download()

    with st.container(height=600, border=True):
        for i, png in enumerate(st.session_state["preview_png"], 1):
            st.image(png, caption=f"Page {i}", use_container_width=True)
