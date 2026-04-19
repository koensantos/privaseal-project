from faker import Faker
from PIL import Image, ImageDraw, ImageFont
import random
import os

fake = Faker()


def get_script_dir():
    return os.path.dirname(os.path.abspath(__file__))


def get_font(size, bold=False):
    font_options = [
        "arialbd.ttf" if bold else "arial.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
    ]

    for font_name in font_options:
        try:
            return ImageFont.truetype(font_name, size)
        except Exception:
            continue

    return ImageFont.load_default()


def draw_wrapped_text(draw, text, font, x, y, max_width, line_spacing=8, fill="black"):
    paragraphs = text.split("\n")

    for paragraph in paragraphs:
        if not paragraph.strip():
            y += 18
            continue

        words = paragraph.split()
        current_line = ""

        for word in words:
            test_line = word if current_line == "" else current_line + " " + word
            bbox = draw.textbbox((0, 0), test_line, font=font)
            line_width = bbox[2] - bbox[0]

            if line_width <= max_width:
                current_line = test_line
            else:
                draw.text((x, y), current_line, font=font, fill=fill)
                line_bbox = draw.textbbox((x, y), current_line, font=font)
                line_height = line_bbox[3] - line_bbox[1]
                y += line_height + line_spacing
                current_line = word

        if current_line:
            draw.text((x, y), current_line, font=font, fill=fill)
            line_bbox = draw.textbbox((x, y), current_line, font=font)
            line_height = line_bbox[3] - line_bbox[1]
            y += line_height + line_spacing

    return y


def draw_boxed_section(draw, x1, y1, x2, y2, title, title_font, body_fill=(245, 250, 251), header_fill=(34, 108, 122)):
    draw.rounded_rectangle((x1, y1, x2, y2), radius=14, fill=body_fill, outline=(150, 170, 175), width=2)
    draw.rounded_rectangle((x1, y1, x2, y1 + 42), radius=14, fill=header_fill, outline=header_fill)
    draw.rectangle((x1, y1 + 21, x2, y1 + 42), fill=header_fill)
    draw.text((x1 + 14, y1 + 8), title, font=title_font, fill="white")


def draw_field_row(draw, label, value, x_label, x_value, y, label_font, value_font, label_fill=(70, 90, 95), value_fill="black"):
    draw.text((x_label, y), label, font=label_font, fill=label_fill)
    draw.text((x_value, y), value, font=value_font, fill=value_fill)
    return y + 30


def draw_checkbox_line(draw, x, y, text, font):
    draw.rectangle((x, y + 4, x + 18, y + 22), outline=(50, 70, 75), width=2)
    draw.text((x + 30, y), text, font=font, fill="black")
    return y + 34


def create_blank_page():
    page = Image.new("RGB", (1700, 2200), "white")
    draw = ImageDraw.Draw(page)
    return page, draw


def load_portrait_image(folder_name="faces"):
    folder = os.path.join(get_script_dir(), folder_name)

    if not os.path.exists(folder):
        raise FileNotFoundError(f"Folder '{folder}' not found")

    files = [
        f for f in os.listdir(folder)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ]

    if not files:
        raise ValueError(f"No images found in '{folder}'")

    chosen_file = random.choice(files)
    path = os.path.join(folder, chosen_file)
    return Image.open(path).convert("RGB")


def generate_fake_patient_data():
    first_name = fake.first_name()
    last_name = fake.last_name()
    full_name = f"{first_name} {last_name}"

    return {
        "packet_id": f"PT-{random.randint(100000, 999999)}",
        "date_received": fake.date_between(start_date="-90d", end_date="today").strftime("%m/%d/%Y"),
        "full_name": full_name,
        "dob": fake.date_of_birth(minimum_age=18, maximum_age=85).strftime("%m/%d/%Y"),
        "sex": random.choice(["M", "F"]),
        "phone": fake.phone_number(),
        "email": fake.email(),
        "street": fake.street_address(),
        "city": fake.city(),
        "state": fake.state_abbr(),
        "zip": fake.zipcode(),
        "patient_id": f"MRN-{random.randint(1000000, 9999999)}",
        "insurance_provider": random.choice([
            "Blue Cross Blue Shield",
            "Aetna",
            "UnitedHealthcare",
            "Cigna",
            "Humana"
        ]),
        "member_id": f"MEM-{random.randint(10000000, 99999999)}",
        "group_number": f"GRP-{random.randint(10000, 99999)}",
        "employer": fake.company(),
        "emergency_contact": fake.name(),
        "emergency_relationship": random.choice(["Parent", "Sibling", "Spouse", "Partner", "Friend"]),
        "emergency_phone": fake.phone_number(),
        "primary_physician": f"Dr. {fake.last_name()}",
        "preferred_pharmacy": random.choice([
            "CVS Pharmacy",
            "Walgreens",
            "Rite Aid",
            "Local Family Pharmacy",
            "CarePlus Pharmacy"
        ]),
        "appointment_type": random.choice([
            "New Patient Visit",
            "Annual Physical",
            "Follow-Up Consultation",
            "Specialist Referral Intake"
        ]),
        "allergies": random.choice([
            "No known drug allergies",
            "Penicillin",
            "Latex",
            "Peanuts",
            "Sulfa medications"
        ]),
        "current_medications": random.choice([
            "None reported",
            "Lisinopril 10mg daily",
            "Metformin 500mg twice daily",
            "Atorvastatin 20mg daily",
            "Albuterol inhaler as needed"
        ]),
        "license_number": str(random.randint(100000000, 999999999)),
        "issue_date": fake.date_between(start_date="-8y", end_date="-1y").strftime("%m/%d/%Y"),
        "exp_date": fake.date_between(start_date="+1y", end_date="+8y").strftime("%m/%d/%Y"),
        "height": random.choice(["5'-02\"", "5'-04\"", "5'-06\"", "5'-08\"", "5'-10\"", "6'-00\""]),
        "license_class": random.choice(["C", "D", "E"]),
    }


def create_synthetic_license(data, portrait_folder="faces", output_path="patient_license.png"):
    full_output_path = os.path.join(get_script_dir(), output_path)

    width, height = 1000, 630
    card = Image.new("RGB", (width, height), (243, 246, 248))
    draw = ImageDraw.Draw(card)

    title_font = get_font(40, bold=True)
    label_font = get_font(22, bold=False)
    value_font = get_font(28, bold=False)

    draw.rectangle((0, 0, width, 90), fill=(41, 97, 132))
    draw.text((30, 20), "STATE IDENTIFICATION CARD", fill="white", font=title_font)

    portrait = load_portrait_image(portrait_folder).resize((220, 280))
    card.paste(portrait, (50, 150))
    draw.rectangle((50, 150, 270, 430), outline=(85, 85, 85), width=2)

    x_label = 320
    x_value = 500
    y = 140
    spacing = 50

    city_state_zip = f"{data['city']}, {data['state']} {data['zip']}"

    fields = [
        ("ID NUMBER", data["license_number"]),
        ("NAME", data["full_name"]),
        ("DOB", data["dob"]),
        ("SEX", data["sex"]),
        ("HEIGHT", data["height"]),
        ("CLASS", data["license_class"]),
        ("ISSUED", data["issue_date"]),
        ("EXPIRES", data["exp_date"]),
        ("ADDRESS", data["street"]),
        ("", city_state_zip),
    ]

    for label, value in fields:
        if label:
            draw.text((x_label, y), label, fill=(92, 92, 92), font=label_font)
        draw.text((x_value, y), value, fill="black", font=value_font)
        y += spacing

    card.save(full_output_path)
    return full_output_path


def create_page_1_clinic_overview(output_dir):
    page, draw = create_blank_page()

    title_font = get_font(40, bold=True)
    subtitle_font = get_font(23, bold=False)
    section_font = get_font(24, bold=True)
    body_font = get_font(20, bold=False)
    small_font = get_font(17, bold=False)

    margin = 60

    # Distinct healthcare header
    draw.rectangle((0, 0, 1700, 150), fill=(24, 103, 118))
    draw.rectangle((0, 150, 1700, 165), fill=(193, 229, 233))
    draw.text((margin, 38), "North Valley Family Medicine", fill="white", font=title_font)
    draw.text((margin, 92), "Patient Information and Welcome Packet", fill=(228, 245, 247), font=subtitle_font)

    # Top-right clinic info card
    draw.rounded_rectangle((1120, 30, 1625, 128), radius=16, fill=(41, 121, 136), outline=(215, 240, 243), width=2)
    draw.text((1145, 48), "Clinic Information", fill="white", font=section_font)
    draw.text((1145, 84), "Mon-Fri 8:00 AM - 5:30 PM\nSat 8:00 AM - 12:00 PM", fill="white", font=small_font)

    # Section 1
    draw_boxed_section(draw, 60, 210, 1640, 760, "Clinic Overview", section_font, body_fill=(246, 251, 252), header_fill=(33, 111, 124))
    y = 275
    intro_text = (
        "Welcome to North Valley Family Medicine. Our clinic is committed to providing accessible, coordinated, and "
        "patient-centered outpatient care for individuals and families across a broad range of primary care needs. "
        "Services may include wellness visits, preventive screenings, routine follow-up care, chronic condition "
        "management, medication review, referral coordination, and ongoing support for continuity of care.\n\n"
        "Our care team includes physicians, nurses, medical assistants, and administrative staff who work together to "
        "support registration, scheduling, intake processing, clinical documentation, and follow-up communication. "
        "Patients may be asked to arrive early for appointments when completing first-time registration materials or "
        "updating demographic and insurance information.\n\n"
        "This packet provides general information about clinic services, office expectations, payment procedures, "
        "privacy-related notices, and registration workflows. It is intentionally designed to include a substantial "
        "amount of ordinary administrative text so that document-processing systems can distinguish standard business "
        "content from the personally identifiable information included elsewhere in the packet."
    )
    draw_wrapped_text(draw, intro_text, body_font, 90, y, 1520, line_spacing=8)

    # Section 2
    draw_boxed_section(draw, 60, 790, 790, 1320, "Services Offered", section_font, body_fill=(244, 249, 250), header_fill=(58, 130, 142))
    y = 855
    services = [
        "Annual physical examinations and wellness visits",
        "New patient registration and first-visit intake",
        "Follow-up consultations and medication checks",
        "Preventive screenings and immunization review",
        "Chronic disease monitoring and referral support",
        "Basic coordination for laboratory and specialty care",
        "Pharmacy updates and prescription follow-up",
        "Routine administrative support for patient records"
    ]
    for item in services:
        y = draw_checkbox_line(draw, 95, y, item, body_font)

    # Section 3
    draw_boxed_section(draw, 850, 790, 1640, 1320, "General Office Policies", section_font, body_fill=(244, 249, 250), header_fill=(58, 130, 142))
    y = 855
    policy_text = (
        "Patients should bring all requested documentation to their appointment, including photo identification, "
        "insurance information, and any updated medication or referral materials when applicable.\n\n"
        "Copayments, deductibles, and other patient-responsible balances may be collected at the time of service "
        "based on active benefit information and visit type.\n\n"
        "Clinic policy may require follow-up if forms are incomplete, identification is unreadable, or insurance "
        "coverage cannot be confirmed before the appointment date."
    )
    draw_wrapped_text(draw, policy_text, body_font, 880, y, 710, line_spacing=8)

    # Section 4
    draw_boxed_section(draw, 60, 1360, 1640, 1930, "Privacy, Billing, and Administrative Guidance", section_font, body_fill=(247, 251, 252), header_fill=(33, 111, 124))
    y = 1425
    footer_text = (
        "The clinic maintains internal procedures intended to support appropriate information handling, administrative "
        "processing, care coordination, and communication efficiency. Patients may be asked to review consent language, "
        "authorization notices, and appointment-related policies, including cancellation expectations, missed-visit "
        "guidelines, and documentation requirements.\n\n"
        "General informational sections such as this page are expected to remain visible after redaction because they do "
        "not contain patient-specific identifiers. Their inclusion helps test whether a redaction workflow preserves "
        "useful contextual content while isolating protected data that appears elsewhere in the packet.\n\n"
        "If demographic, insurance, or pharmacy details change before the date of service, patients are encouraged to "
        "notify the office in advance so that records can be updated before check-in."
    )
    draw_wrapped_text(draw, footer_text, body_font, 90, y, 1520, line_spacing=8)

    output_path = os.path.join(output_dir, "page_1.png")
    page.save(output_path)
    return output_path


def create_page_2_registration_summary(data, output_dir):
    page, draw = create_blank_page()

    title_font = get_font(38, bold=True)
    subtitle_font = get_font(22, bold=False)
    section_font = get_font(24, bold=True)
    body_font = get_font(20, bold=False)
    label_font = get_font(18, bold=True)
    small_font = get_font(17, bold=False)

    margin = 60

    # Different header layout than apartment packet
    draw.rectangle((0, 0, 1700, 145), fill=(33, 120, 130))
    draw.text((margin, 34), "Patient Registration Summary", fill="white", font=title_font)
    draw.text((margin, 86), "Administrative review, intake guidance, and limited patient details", fill=(226, 245, 246), font=subtitle_font)

    draw.rounded_rectangle((1180, 28, 1625, 118), radius=14, fill=(57, 143, 152), outline=(211, 239, 241), width=2)
    draw.text((1205, 46), f"Packet ID: {data['packet_id']}", fill="white", font=label_font)
    draw.text((1205, 78), f"Date Received: {data['date_received']}", fill="white", font=small_font)

    # Left main narrative box
    draw_boxed_section(draw, 60, 190, 1030, 1210, "Registration Overview", section_font, body_fill=(247, 251, 252), header_fill=(32, 108, 122))
    y = 255
    summary_text = (
        f"This summary reflects the preliminary registration materials submitted for {data['full_name']}. "
        f"The patient is currently being scheduled for a {data['appointment_type']} and has provided initial "
        "demographic and contact information to support chart creation, scheduling workflow, and administrative review. "
        "This page is intentionally structured to contain a large amount of ordinary intake language with only a limited "
        "number of identifiers embedded throughout the content.\n\n"
        f"For communication purposes, the current phone number on file is {data['phone']} and the current email address "
        f"is {data['email']}. These details may be used by scheduling staff if additional forms, insurance clarification, "
        "or pre-visit documents are needed before the appointment date. The surrounding descriptive text should remain "
        "visible after redaction where no protected information is present.\n\n"
        f"The patient has indicated a preferred pharmacy of {data['preferred_pharmacy']} and listed {data['primary_physician']} "
        "as the current primary or referring provider. These details may support medication reconciliation, records "
        "coordination, referral routing, and visit preparation. Administrative staff may also use this page to track "
        "whether identity documentation, insurance images, and registration acknowledgments have been received.\n\n"
        "Standard intake processing may include confirmation of demographic data, insurance validation, review of allergy "
        "and medication information, emergency contact verification, and collection of signed acknowledgments where "
        "required by clinic policy. If submitted materials are incomplete or unclear, staff may follow up before the "
        "appointment date to reduce delays at check-in and improve provider readiness."
    )
    draw_wrapped_text(draw, summary_text, body_font, 90, y, 900, line_spacing=8)

    # Right stacked cards
    draw_boxed_section(draw, 1070, 190, 1640, 610, "Quick Patient Snapshot", section_font, body_fill=(244, 249, 250), header_fill=(58, 130, 142))
    y = 255
    snapshot_rows = [
        ("Patient Name", data["full_name"]),
        ("Appointment Type", data["appointment_type"]),
        ("MRN", data["patient_id"]),
        ("Insurance", data["insurance_provider"]),
        ("Pharmacy", data["preferred_pharmacy"]),
        ("Primary Physician", data["primary_physician"]),
    ]
    for label, value in snapshot_rows:
        y = draw_field_row(draw, f"{label}:", value, 1095, 1285, y, label_font, body_font)

    draw_boxed_section(draw, 1070, 640, 1640, 1210, "Administrative Review Notes", section_font, body_fill=(244, 249, 250), header_fill=(58, 130, 142))
    y = 705
    notes = [
        "Confirm appointment type and ensure intake documents are complete.",
        "Verify insurance card details and request updates if unreadable.",
        "Check allergy and medication sections before provider review.",
        "Retain general policy text after redaction where no identifiers exist.",
        "Escalate conflicting demographic details for manual review.",
        "Confirm emergency contact and preferred pharmacy during outreach.",
        "Ensure government ID image is readable for verification workflow.",
    ]
    for note in notes:
        y = draw_checkbox_line(draw, 1095, y, note, small_font)

    # Bottom wide note box
    draw_boxed_section(draw, 60, 1260, 1640, 1880, "Workflow Guidance and Records Handling", section_font, body_fill=(247, 251, 252), header_fill=(32, 108, 122))
    y = 1325
    workflow_text = (
        "Clinic staff may use this page for internal routing before the patient is fully checked in. Records may be "
        "reviewed for legibility, consistency, completeness, and scheduling readiness. General descriptive sections "
        "such as this one are intended to remain visible after redaction so that testing can confirm whether non-sensitive "
        "administrative content is preserved while limited patient identifiers are isolated.\n\n"
        "Patients may be asked to present a government-issued photo identification document at check-in, especially for "
        "new patient registration, first-time insurance setup, or records verification. If documentation is missing or "
        "incomplete, the clinic may contact the patient before the appointment to request updated materials and reduce "
        "processing delays.\n\n"
        "This packet structure is also intended to simulate realistic intake paperwork where contextual instructions, "
        "policy language, and narrative office guidance are intermixed with smaller amounts of personally identifiable "
        "information."
    )
    draw_wrapped_text(draw, workflow_text, body_font, 90, y, 1520, line_spacing=8)

    output_path = os.path.join(output_dir, "page_2.png")
    page.save(output_path)
    return output_path


def create_page_3_patient_intake(data, license_image_path, output_dir):
    page, draw = create_blank_page()

    title_font = get_font(38, bold=True)
    section_font = get_font(23, bold=True)
    body_font = get_font(18, bold=False)
    label_font = get_font(17, bold=True)
    small_font = get_font(15, bold=False)

    margin = 50

    # More form-like page header
    draw.rectangle((0, 0, 1700, 120), fill=(28, 112, 124))
    draw.text((margin, 32), "Patient Intake and Registration Form", fill="white", font=title_font)

    draw.rounded_rectangle((1150, 18, 1630, 100), radius=12, fill=(58, 143, 152), outline=(212, 241, 243), width=2)
    draw.text((1172, 35), f"Packet ID: {data['packet_id']}", fill="white", font=label_font)
    draw.text((1172, 63), f"Date Received: {data['date_received']}", fill="white", font=small_font)

    y = 145

    # Personal info box
    draw_boxed_section(draw, 50, y, 820, y + 260, "Patient Demographics", section_font, body_fill=(247, 251, 252), header_fill=(33, 111, 124))
    left_y = y + 62
    left_rows = [
        ("Full Name:", data["full_name"]),
        ("Date of Birth:", data["dob"]),
        ("Sex:", data["sex"]),
        ("Phone Number:", data["phone"]),
        ("Email Address:", data["email"]),
        ("MRN:", data["patient_id"]),
    ]
    for label, value in left_rows:
        left_y = draw_field_row(draw, label, value, 72, 255, left_y, label_font, body_font)

    # Address / visit box
    draw_boxed_section(draw, 850, y, 1640, y + 260, "Address and Visit Details", section_font, body_fill=(247, 251, 252), header_fill=(33, 111, 124))
    right_y = y + 62
    right_rows = [
        ("Street Address:", data["street"]),
        ("City / State / ZIP:", f"{data['city']}, {data['state']} {data['zip']}"),
        ("Appointment Type:", data["appointment_type"]),
        ("Preferred Pharmacy:", data["preferred_pharmacy"]),
        ("Primary Physician:", data["primary_physician"]),
    ]
    for label, value in right_rows:
        right_y = draw_field_row(draw, label, value, 872, 1095, right_y, label_font, body_font)

    y += 290

    # Insurance box
    draw_boxed_section(draw, 50, y, 1640, y + 180, "Insurance and Coverage Information", section_font, body_fill=(244, 249, 250), header_fill=(58, 130, 142))
    ins_y = y + 62
    insurance_left = [
        ("Insurance Provider:", data["insurance_provider"]),
        ("Member ID:", data["member_id"]),
    ]
    insurance_right = [
        ("Group Number:", data["group_number"]),
        ("Employer on File:", data["employer"]),
    ]
    temp_y = ins_y
    for label, value in insurance_left:
        temp_y = draw_field_row(draw, label, value, 72, 310, temp_y, label_font, body_font)

    temp_y2 = ins_y
    for label, value in insurance_right:
        temp_y2 = draw_field_row(draw, label, value, 860, 1095, temp_y2, label_font, body_font)

    y += 210

    # Clinical info box
    draw_boxed_section(draw, 50, y, 1640, y + 220, "Clinical and Emergency Contact Information", section_font, body_fill=(247, 251, 252), header_fill=(33, 111, 124))
    clin_y = y + 62
    left_text = (
        f"Known Allergies: {data['allergies']}\n"
        f"Current Medications: {data['current_medications']}"
    )
    draw_wrapped_text(draw, left_text, body_font, 72, clin_y, 700, line_spacing=6)

    right_rows = [
        ("Emergency Contact:", data["emergency_contact"]),
        ("Relationship:", data["emergency_relationship"]),
        ("Emergency Phone:", data["emergency_phone"]),
    ]
    temp_y = clin_y
    for label, value in right_rows:
        temp_y = draw_field_row(draw, label, value, 860, 1110, temp_y, label_font, body_font)

    y += 250

    # Acknowledgment box
    draw_boxed_section(draw, 50, y, 1640, y + 260, "Patient Acknowledgments and Authorizations", section_font, body_fill=(244, 249, 250), header_fill=(58, 130, 142))
    ack_y = y + 62
    auth_text = (
        "I certify that the information provided in this intake packet is complete and accurate to the best of my "
        "knowledge. I understand that this information may be used for appointment scheduling, registration, care "
        "coordination, billing support, and administrative processing. I acknowledge that additional documentation may "
        "be requested if submitted information is incomplete, inconsistent, or unclear.\n\n"
        "I understand that presentation of identification and insurance information may be required as part of the "
        "registration and verification process. I further acknowledge that clinic policy, consent, and records-handling "
        "procedures may apply to this visit and future communications."
    )
    draw_wrapped_text(draw, auth_text, body_font, 72, ack_y, 1520, line_spacing=6)

    y += 290

    # ID section - distinct layout
    draw_boxed_section(draw, 50, y, 1640, y + 560, "Attached Identification and Verification Review", section_font, body_fill=(247, 251, 252), header_fill=(33, 111, 124))

    license_img = Image.open(license_image_path).convert("RGB")
    license_img = license_img.resize((720, 455))
    image_x = 75
    image_y = y + 62
    page.paste(license_img, (image_x, image_y))
    draw.rectangle((image_x - 2, image_y - 2, image_x + 722, image_y + 457), outline=(70, 70, 70), width=2)

    draw.rounded_rectangle((840, y + 62, 1605, y + 455), radius=12, fill=(239, 246, 247), outline=(165, 184, 188), width=2)
    draw.text((865, y + 82), "Verification Summary", font=section_font, fill=(22, 90, 100))

    summary_y = y + 130
    verification_rows = [
        ("Document Type:", "State Identification Card"),
        ("ID Number:", data["license_number"]),
        ("Issue Date:", data["issue_date"]),
        ("Expiration Date:", data["exp_date"]),
        ("Sex:", data["sex"]),
        ("Height:", data["height"]),
        ("License Class:", data["license_class"]),
    ]
    for label, value in verification_rows:
        summary_y = draw_field_row(draw, label, value, 870, 1115, summary_y, label_font, body_font)

    summary_y += 10
    verification_note = (
        "Attached identification is included as part of the registration packet for identity verification and "
        "document-processing evaluation. This section intentionally combines structured fields with embedded image content."
    )
    draw_wrapped_text(draw, verification_note, body_font, 870, summary_y, 690, line_spacing=6)

    footer_y = y + 510
    draw.line((80, footer_y, 390, footer_y), fill="black", width=2)
    draw.text((80, footer_y + 8), "Patient Signature", font=small_font, fill="black")

    draw.line((470, footer_y, 730, footer_y), fill="black", width=2)
    draw.text((470, footer_y + 8), "Date", font=small_font, fill="black")

    output_path = os.path.join(output_dir, "page_3.png")
    page.save(output_path)
    return output_path


def create_patient_packet(data, license_image_path):
    output_dir = os.path.join(get_script_dir(), "patient_packet")
    os.makedirs(output_dir, exist_ok=True)

    page_1 = create_page_1_clinic_overview(output_dir)
    page_2 = create_page_2_registration_summary(data, output_dir)
    page_3 = create_page_3_patient_intake(data, license_image_path, output_dir)

    return [page_1, page_2, page_3]


def combine_pages_to_pdf(image_paths, output_pdf="patient_intake_packet.pdf"):
    output_path = os.path.join(get_script_dir(), output_pdf)

    images = [Image.open(p).convert("RGB") for p in image_paths]

    if not images:
        raise ValueError("No images were provided for PDF creation")

    images[0].save(
        output_path,
        save_all=True,
        append_images=images[1:],
        format="PDF"
    )

    return output_path


if __name__ == "__main__":
    try:
        print("Generating fake patient data...")
        data = generate_fake_patient_data()

        print("Creating synthetic ID image...")
        license_path = create_synthetic_license(
            data=data,
            portrait_folder="faces",
            output_path="patient_license.png"
        )

        print("Creating reformatted 3-page patient packet...")
        pages = create_patient_packet(data, license_path)

        print("Combining pages into PDF...")
        pdf_path = combine_pages_to_pdf(pages, output_pdf="patient_intake_packet.pdf")

        print("\nCreated files:")
        print("License:", license_path)
        for page in pages:
            print("Page:", page)
        print("PDF:", pdf_path)

    except Exception as e:
        print("Error:", e)