# Run Presidio NER on OCR text
# Filter by confidence threshold
# Keep only relevant PII entities
# Remove duplicate detections


from presidio_analyzer import AnalyzerEngine

# Initialize analyzer once
analyzer = AnalyzerEngine()

IMPORTANT_ENTITIES = {
    "PERSON",
    "PHONE_NUMBER",
    "EMAIL_ADDRESS",
    "DATE_TIME",
    "LOCATION"
}

def detect_pii_from_text(text):
    results = analyzer.analyze(
        text=text,
        language="en"
    )
    return results


def stage_text_pii(ocr_results):
    pii_targets = []

    for item in ocr_results:
        text = item["text"]
        if not text or text.strip() == "":
            continue
        bbox = item["bounding_box"]
        page = item["page_number"]

        results = detect_pii_from_text(text)
        
        for res in results:
            if res.score > 0.5 and res.entity_type in IMPORTANT_ENTITIES:
                pii_targets.append({
                    "label": res.entity_type,
                    "bounding_box": bbox,
                    "page_number": page,
                    "source": "text",
                    "confidence": float(res.score)
                })

        unique_targets = []
    seen = set()

    for item in pii_targets:
        key = (item["label"], item["bounding_box"], item["page_number"])
        if key not in seen:
            seen.add(key)
            unique_targets.append(item)

    return unique_targets    

    return pii_targets


# Test block
if __name__ == "__main__":
    test_ocr = [
        {"text": "Ryan Scott", "bounding_box": (100, 100, 200, 150), "page_number": 1},
        {"text": "642-650-2844", "bounding_box": (100, 200, 250, 250), "page_number": 1},
        {"text": "Welcome to company", "bounding_box": (100, 300, 300, 350), "page_number": 1}
    ]

    output = stage_text_pii(test_ocr)

    for o in output:
        print(o)