# Text-based PII detection for PrivaSeal.
#
# Three cooperating stages, all producing redaction targets in the shared schema
# { label, bounding_box, page_number, source, confidence }:
#
#   stage_text_pii  — Presidio NER run on page-level reconstructed text,
#                     with entity spans mapped back to the originating OCR
#                     word boxes (per-region fallback preserved).
#   stage_kv_pii    — sensitive form labels (e.g. "Full Name:") pair with
#                     the union of value words to their right on the same row;
#                     vertical fallback if no row match.
#   stage_regex_pii — custom regex patterns for ID numbers, SSNs, ZIPs,
#                     currency, dates, and phones that Presidio often skips.

import re

from presidio_analyzer import AnalyzerEngine

analyzer = AnalyzerEngine()

IMPORTANT_ENTITIES = {
    "PERSON",
    "PHONE_NUMBER",
    "EMAIL_ADDRESS",
    "DATE_TIME",
    "LOCATION",
}

_CONF_THRESHOLD = 0.5


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _union_bbox(boxes):
    """Return the axis-aligned union of a non-empty list of bboxes."""
    xs1, ys1, xs2, ys2 = zip(*boxes)
    return (min(xs1), min(ys1), max(xs2), max(ys2))


def _interpolate_bbox(bbox, full_text, sub_start, sub_end):
    """Linearly interpolate the X coordinates of a substring within a larger bounding box."""
    x1, y1, x2, y2 = bbox
    w = max(0, x2 - x1)
    length = max(1, len(full_text))
    char_w = w / length
    new_x1 = x1 + sub_start * char_w
    new_x2 = x1 + sub_end * char_w
    return (int(new_x1), y1, int(new_x2), y2)


def _group_by_page(ocr_results):
    by_page = {}
    for item in ocr_results:
        by_page.setdefault(item["page_number"], []).append(item)
    return by_page


def _reading_order(regions, line_h: int = 30):
    """Sort OCR regions top-to-bottom, left-to-right (row-bucketed)."""
    def key(r):
        x1, y1, x2, y2 = r["bounding_box"]
        return (round((y1 + y2) / 2 / line_h), x1)
    return sorted(regions, key=key)


# ---------------------------------------------------------------------------
# Stage: Presidio NER  (page-level + per-region fallback)
# ---------------------------------------------------------------------------

def detect_pii_from_text(text):
    return analyzer.analyze(text=text, language="en")


def _presidio_page_targets(regions):
    """Run Presidio on the reconstructed page text; map entity char spans to
    the OCR words they overlap and emit one target per entity (bbox-unioned)."""
    if not regions:
        return []

    ordered = _reading_order(regions)

    pieces = []
    spans = []  # parallel to ordered: (char_start, char_end)
    cursor = 0
    for r in ordered:
        t = r["text"] or ""
        if not t.strip():
            spans.append((cursor, cursor))
            continue
        start = cursor
        pieces.append(t)
        cursor += len(t)
        spans.append((start, cursor))
        pieces.append(" ")
        cursor += 1

    page_text = "".join(pieces)
    if not page_text.strip():
        return []

    targets = []
    for res in detect_pii_from_text(page_text):
        if res.score <= _CONF_THRESHOLD or res.entity_type not in IMPORTANT_ENTITIES:
            continue
        overlap_boxes = []
        for region, (s, e) in zip(ordered, spans):
            if s >= e:
                continue
            if s < res.end and e > res.start:
                local_start = max(0, res.start - s)
                local_end = min(e - s, res.end - s)
                region_text = region["text"] or ""
                local_end = min(local_end, len(region_text))
                if local_start < local_end:
                    interp_box = _interpolate_bbox(region["bounding_box"], region_text, local_start, local_end)
                    overlap_boxes.append(interp_box)
        if not overlap_boxes:
            continue
        targets.append({
            "label": res.entity_type,
            "bounding_box": _union_bbox(overlap_boxes),
            "page_number": ordered[0]["page_number"],
            "source": "text",
            "confidence": float(res.score),
        })
    return targets


def _presidio_per_region_targets(regions):
    """Original per-OCR-region detection, kept as a fallback so we never
    regress on items the page-level pass happens to miss."""
    targets = []
    for item in regions:
        text = (item.get("text") or "").strip()
        if not text:
            continue
        for res in detect_pii_from_text(text):
            if res.score <= _CONF_THRESHOLD or res.entity_type not in IMPORTANT_ENTITIES:
                continue
            interp_box = _interpolate_bbox(item["bounding_box"], text, res.start, res.end)
            targets.append({
                "label": res.entity_type,
                "bounding_box": interp_box,
                "page_number": item["page_number"],
                "source": "text",
                "confidence": float(res.score),
            })
    return targets


def _dedupe(targets):
    seen = set()
    out = []
    for t in targets:
        key = (t["label"], t["bounding_box"], t["page_number"])
        if key in seen:
            continue
        seen.add(key)
        out.append(t)
    return out


def stage_text_pii(ocr_results):
    merged = []
    for regions in _group_by_page(ocr_results).values():
        merged.extend(_presidio_page_targets(regions))
        merged.extend(_presidio_per_region_targets(regions))
    return _dedupe(merged)


# ---------------------------------------------------------------------------
# Stage: Key-Value PII  (sensitive label → value region to the right / below)
# ---------------------------------------------------------------------------

_SENSITIVE_LABELS = {
    # people / identifiers
    "full name", "name", "first name", "last name", "middle name", "preferred name",
    "patient name", "employee name",
    "date of birth", "dob", "birth date", "birthdate",
    # contact
    "phone", "phone number", "mobile", "cell phone", "telephone",
    "email", "email address", "e-mail",
    # address
    "address", "street address", "home address", "city", "state", "zip", "zip code",
    "city / state / zip",
    # SSN / govt IDs
    "ssn", "social security", "social security number", "last 4 of ssn",
    "id number", "member id", "mrn", "patient id", "insurance id",
    "policy number", "group number", "license number",
    "employee id", "eid", "employee number", "packet id",
    # banking
    "account number", "routing number", "account last 4", "routing last 4",
    "bank name", "bank", "financial institution",
    # HR / employment
    "insurance provider", "primary physician", "preferred pharmacy",
    "emergency contact", "emergency phone", "relationship",
    "employer", "job title", "department", "manager", "work email", "company email",
    "employment type", "pay type", "pay rate", "salary", "compensation",
    "benefits", "benefits package", "core benefits package",
    "work location", "location",
    "assigned equipment", "equipment",
    # dates
    "issue date", "expiration date", "start date", "issued", "expires",
    "issue", "exp", "exp date", "exp. date", "created",
    # signatures / ID card fields
    "signature", "patient signature", "employee signature",
    "sex", "height", "class",
    "document type", "review status",
}


def _is_sensitive_label(text: str) -> bool:
    return (text or "").strip().rstrip(":").strip().lower() in _SENSITIVE_LABELS


_LABEL_PREFIX_RE = re.compile(
    r"^\s*(?P<label>" + "|".join(sorted((re.escape(l) for l in _SENSITIVE_LABELS), key=len, reverse=True)) + r")\s*[:\-]?\s+\S",
    re.IGNORECASE,
)


def _contains_label_with_value(text: str) -> bool:
    """True if text starts with a sensitive label followed by more content —
    e.g. "Pay Type Salary", "Emergency Contact: Mary Hunt". Catches OCR lines
    that merged a form label with its value, which the exact-match path misses.
    """
    if not text:
        return False
    return _LABEL_PREFIX_RE.search(text) is not None


def _same_row(bbox1, bbox2) -> bool:
    c1 = (bbox1[1] + bbox1[3]) / 2
    c2 = (bbox2[1] + bbox2[3]) / 2
    height = bbox1[3] - bbox1[1]
    return abs(c1 - c2) < max(height * 0.8, 20)


def _x_overlap(bbox1, bbox2) -> int:
    return max(0, min(bbox1[2], bbox2[2]) - max(bbox1[0], bbox2[0]))


def stage_kv_pii(ocr_results):
    """For each sensitive label, redact the union of value words on the same
    row to its right. If no same-row value is found, look within 120 px below
    (requires x-overlap) and redact the nearest non-label region."""
    targets = []
    for page_num, regions in _group_by_page(ocr_results).items():
        for label_region in regions:
            if not _is_sensitive_label(label_region["text"]):
                continue
            lbox = label_region["bounding_box"]
            lx1, ly1, lx2, ly2 = lbox

            row_values = []
            for vr in regions:
                if vr is label_region:
                    continue
                if _is_sensitive_label(vr["text"]):
                    continue
                vbox = vr["bounding_box"]
                if vbox[0] < lx2 - 10:
                    continue
                if not _same_row(lbox, vbox):
                    continue
                row_values.append(vbox)

            if row_values:
                targets.append({
                    "label": "FIELD_VALUE",
                    "bounding_box": _union_bbox(row_values),
                    "page_number": page_num,
                    "source": "text",
                    "confidence": 1.0,
                })
                continue

            below = []
            for vr in regions:
                if vr is label_region or _is_sensitive_label(vr["text"]):
                    continue
                vbox = vr["bounding_box"]
                if vbox[1] <= ly2:
                    continue
                if vbox[1] - ly2 > 50:
                    continue
                if _x_overlap(lbox, vbox) <= 0:
                    continue
                below.append((vbox[1] - ly2, vbox))
            if below:
                below.sort()
                _, nearest = below[0]
                targets.append({
                    "label": "FIELD_VALUE",
                    "bounding_box": nearest,
                    "page_number": page_num,
                    "source": "text",
                    "confidence": 0.9,
                })

    seen = set()
    unique = []
    for t in targets:
        key = (t["bounding_box"], t["page_number"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(t)
    return unique


# ---------------------------------------------------------------------------
# Stage: regex patterns for IDs / SSNs / currency / dates / phones
# ---------------------------------------------------------------------------

_REGEX_PATTERNS = [
    ("CUSTOM_ID",  re.compile(r"\b[A-Z]{2,6}-?\d{4,10}\b")),
    ("SSN",        re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("ZIP",        re.compile(r"\b\d{5}(?:-\d{4})?\b")),
    ("CURRENCY",   re.compile(r"\$\s?\d{1,3}(?:,\d{3})+(?:\.\d{2})?\b")),
    ("DATE",       re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b")),
    ("PHONE",      re.compile(r"\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}(?:x\d+)?\b")),
]


def stage_merged_label_pii(ocr_results):
    targets =[]
    for item in ocr_results:
        text = item.get("text") or ""
        
        # FIX: Ignore massive text blocks so paragraphs aren't swallowed!
        if not text.strip() or len(text) > 60:
            continue
            
        if _is_sensitive_label(text):
            continue
            
        match = _LABEL_PREFIX_RE.search(text)
        if match:
            value_start = match.end()
            if value_start < len(text):
                interp_box = _interpolate_bbox(item["bounding_box"], text, value_start, len(text))
                targets.append({
                    "label": "LABELED_VALUE",
                    "bounding_box": interp_box,
                    "page_number": item["page_number"],
                    "source": "text",
                    "confidence": 0.95,
                })
    return _dedupe(targets)


def stage_regex_pii(ocr_results):
    targets = []
    for item in ocr_results:
        text = item.get("text") or ""
        # if not text.strip():
        #     continue
        for label, pat in _REGEX_PATTERNS:
            for match in pat.finditer(text):
                interp_box = _interpolate_bbox(item["bounding_box"], text, match.start(), match.end())
                targets.append({
                    "label": label,
                    "bounding_box": interp_box,
                    "page_number": item["page_number"],
                    "source": "text",
                    "confidence": 1.0,
                })
    return _dedupe(targets)


# ---------------------------------------------------------------------------
# Test block
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    test_ocr = [
        {"text": "Full Name",   "bounding_box": (100, 100, 260, 140), "page_number": 1},
        {"text": "Ryan Scott",  "bounding_box": (300, 100, 500, 140), "page_number": 1},
        {"text": "EMP-168341",  "bounding_box": (100, 180, 280, 220), "page_number": 1},
        {"text": "$92,316",     "bounding_box": (100, 260, 260, 300), "page_number": 1},
        {"text": "This memo summarizes onboarding materials prepared for Ryan Scott.",
         "bounding_box": (100, 340, 1200, 380), "page_number": 1},
    ]
    for t in stage_text_pii(test_ocr):
        print("NER ", t)
    for t in stage_kv_pii(test_ocr):
        print("KV  ", t)
    for t in stage_regex_pii(test_ocr):
        print("RGX ", t)
