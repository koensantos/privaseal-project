# ID-card region detection.
#
# Per the project's high-recall principle, whenever we can identify that a
# page contains a State ID / Driver's License / Identification Card, we
# black out the WHOLE card region rather than trying to redact each field
# individually (the card's narrow vertical label/value layout and embedded
# photo make per-field KV unreliable).
#
# Trigger: an OCR phrase from `_ID_HEADERS` within 1500 px of a YOLOv8
# `person` detection on the same page. The emitted redaction rectangle is
# the axis-aligned union of:
#   - the person box,
#   - the header text box,
#   - every OCR word whose center lies inside a padded "card neighborhood"
#     around the person box.

_ID_HEADERS = (
    "state identification card",
    "driver's license",
    "drivers license",
    "identification card",
    "id card",
)

_HEADER_MAX_DISTANCE = 500


def _bbox_center(b):
    x1, y1, x2, y2 = b
    return ((x1 + x2) / 2, (y1 + y2) / 2)


def _dist(b1, b2):
    c1 = _bbox_center(b1)
    c2 = _bbox_center(b2)
    return ((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2) ** 0.5


def _union(boxes):
    xs1, ys1, xs2, ys2 = zip(*boxes)
    return (min(xs1), min(ys1), max(xs2), max(ys2))


def _pad_box(b, page_w, page_h, wx=1.5, hy=1.2):
    x1, y1, x2, y2 = b
    w = x2 - x1
    h = y2 - y1
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2
    pw = w * wx
    ph = h * hy
    return (
        max(0, int(cx - pw / 2)),
        max(0, int(cy - ph / 2)),
        min(page_w, int(cx + pw / 2)),
        min(page_h, int(cy + ph / 2)),
    )


def _find_header_boxes(regions):
    """Return OCR bboxes whose text (lower-cased) contains an ID-card header."""
    hits = []
    for r in regions:
        t = (r.get("text") or "").strip().lower()
        if not t:
            continue
        for h in _ID_HEADERS:
            if h in t:
                hits.append(r["bounding_box"])
                break
    return hits


def _grow_region(seed, regions, page_w, page_h, margin=250, max_iters=8):
    """Iteratively absorb any OCR word whose center lies inside a margin-padded
    expansion of the current region. Stops when a pass adds nothing new or the
    iteration cap is hit — both of which are necessary so that an unrelated
    text block on the far side of the page does not chain us across."""
    region = seed
    included = set()
    for _ in range(max_iters):
        rx1, ry1, rx2, ry2 = region
        ex1 = max(0, rx1 - margin)
        ey1 = max(0, ry1 - margin)
        ex2 = min(page_w, rx2 + margin)
        ey2 = min(page_h, ry2 + margin)

        added = False
        for r in regions:
            key = r["bounding_box"]
            if key in included:
                continue
            bx1, by1, bx2, by2 = key
            cx = (bx1 + bx2) / 2
            cy = (by1 + by2) / 2
            if ex1 <= cx <= ex2 and ey1 <= cy <= ey2:
                region = _union([region, key])
                included.add(key)
                added = True
        if not added:
            break
    return region


def find_id_card_regions(ocr_results, visual_targets, page_sizes):
    """
    Args:
        ocr_results:    list of OCR dicts { text, bounding_box, page_number }
        visual_targets: list of YOLO dicts; uses only items with label=="PERSON"
        page_sizes:     dict { page_number: (width, height) } in pixels

    Returns:
        list of redaction target dicts, one per identified ID card region.
    """
    ocr_by_page = {}
    for r in ocr_results:
        ocr_by_page.setdefault(r["page_number"], []).append(r)

    persons_by_page = {}
    for t in visual_targets:
        if t.get("label") != "PERSON":
            continue
        persons_by_page.setdefault(t["page_number"], []).append(t["bounding_box"])

    targets = []
    for page_num, persons in persons_by_page.items():
        regions = ocr_by_page.get(page_num, [])
        headers = _find_header_boxes(regions)
        if not headers:
            continue

        pw, ph = page_sizes.get(page_num, (4723, 6112))

        for person_box in persons:
            near = [h for h in headers if _dist(person_box, h) <= _HEADER_MAX_DISTANCE]
            if not near:
                continue

            # Seed with the person + header boxes, then flood-grow across
            # adjacent OCR words so we capture every field printed on the card
            # (narrow vertical label/value columns, multi-line address, etc.).
            seed = _union([person_box] + near)
            region_box = _grow_region(seed, regions, pw, ph, margin=80, max_iters=8)

            # Pad for character ascenders/descenders and generator border art
            x1, y1, x2, y2 = region_box
            pad = max(20, pw // 120)
            region_box = (
                max(0, x1 - pad),
                max(0, y1 - pad),
                min(pw, x2 + pad),
                min(ph, y2 + pad),
            )

            targets.append({
                "label": "ID_CARD_REGION",
                "bounding_box": region_box,
                "page_number": page_num,
                "source": "visual",
                "confidence": 1.0,
            })

    return targets
