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


def draw_table_row(draw, x1, y1, x2, y2, label, value, label_font, value_font,
                   line_fill=(180, 186, 194), label_fill=(70, 76, 86), value_fill="black"):
    draw.rectangle((x1, y1, x2, y2), outline=line_fill, width=1)
    mid = x1 + 240
    draw.line((mid, y1, mid, y2), fill=line_fill, width=1)
    draw.text((x1 + 12, y1 + 8), label, font=label_font, fill=label_fill)
    draw.text((mid + 12, y1 + 8), value, font=value_font, fill=value_fill)


def draw_checkbox_line(draw, x, y, text, font, outline=(75, 82, 94)):
    draw.rectangle((x, y + 3, x + 16, y + 19), outline=outline, width=2)
    draw.text((x + 28, y), text, font=font, fill="black")
    return y + 32


def draw_sidebar_page_shell(draw, page_title, subtitle, accent=(47, 79, 124), sidebar_width=250):
    # left sidebar
    draw.rectangle((0, 0, sidebar_width, 2200), fill=accent)
    draw.rectangle((0, 0, 1700, 32), fill=(235, 237, 240))
    draw.text((30, 70), "ExampleCorp", font=get_font(34, True), fill="white")
    draw.text((30, 128), "Human Resources", font=get_font(18, False), fill=(224, 229, 237))
    draw.text((30, 175), "Onboarding Packet", font=get_font(18, False), fill=(224, 229, 237))

    # page title
    draw.text((300, 70), page_title, font=get_font(38, True), fill=(35, 41, 52))
    draw.text((300, 122), subtitle, font=get_font(20, False), fill=(95, 103, 115))

    # accent rule
    draw.rectangle((300, 162, 1620, 168), fill=accent)


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


def generate_fake_employee_data():
    first_name = fake.first_name()
    last_name = fake.last_name()
    full_name = f"{first_name} {last_name}"

    department = random.choice([
        "Operations",
        "Finance",
        "Human Resources",
        "Business Analytics",
        "Marketing",
        "Information Technology"
    ])

    job_title = random.choice([
        "Operations Analyst",
        "Project Coordinator",
        "HR Specialist",
        "Business Analyst",
        "Marketing Associate",
        "Systems Administrator"
    ])

    manager = fake.name()
    location = random.choice([
        "New York Office",
        "Jersey City Office",
        "Hybrid",
        "Remote",
        "Boston Office"
    ])

    start_date = fake.date_between(start_date="+7d", end_date="+60d").strftime("%m/%d/%Y")

    return {
        "packet_id": f"EMP-{random.randint(100000, 999999)}",
        "date_created": fake.date_between(start_date="-30d", end_date="today").strftime("%m/%d/%Y"),
        "full_name": full_name,
        "preferred_name": first_name,
        "dob": fake.date_of_birth(minimum_age=21, maximum_age=65).strftime("%m/%d/%Y"),
        "phone": fake.phone_number(),
        "email": fake.email(),
        "street": fake.street_address(),
        "city": fake.city(),
        "state": fake.state_abbr(),
        "zip": fake.zipcode(),
        "employee_id": f"EID-{random.randint(100000, 999999)}",
        "department": department,
        "job_title": job_title,
        "manager": manager,
        "location": location,
        "start_date": start_date,
        "employment_type": random.choice(["Full-Time", "Part-Time"]),
        "pay_type": random.choice(["Salary", "Hourly"]),
        "salary": f"${random.randint(55000, 135000):,}",
        "emergency_contact": fake.name(),
        "emergency_relationship": random.choice(["Parent", "Sibling", "Spouse", "Partner", "Friend"]),
        "emergency_phone": fake.phone_number(),
        "bank_name": random.choice([
            "First National Bank",
            "Summit Credit Union",
            "Riverbend Bank",
            "Community Trust Bank"
        ]),
        "routing_last4": str(random.randint(1000, 9999)),
        "account_last4": str(random.randint(1000, 9999)),
        "ssn_last4": str(random.randint(1000, 9999)),
        "work_email": f"{first_name.lower()}.{last_name.lower()}@examplecorp.com",
        "equipment": random.choice([
            "Laptop, Dock, Monitor",
            "Laptop, Phone, Headset",
            "Laptop, Badge, Monitor, Keyboard",
            "Laptop, Phone, Badge"
        ]),
        "benefits_plan": random.choice([
            "Standard Medical / Dental / Vision",
            "Premium Medical / Dental / Vision",
            "Core Benefits Package"
        ]),
        "license_number": str(random.randint(100000000, 999999999)),
        "issue_date": fake.date_between(start_date="-8y", end_date="-1y").strftime("%m/%d/%Y"),
        "exp_date": fake.date_between(start_date="+1y", end_date="+8y").strftime("%m/%d/%Y"),
        "sex": random.choice(["M", "F"]),
        "height": random.choice(["5'-02\"", "5'-04\"", "5'-06\"", "5'-08\"", "5'-10\"", "6'-00\""]),
        "license_class": random.choice(["C", "D", "E"]),
    }


def create_synthetic_license(data, portrait_folder="faces", output_path="employee_license.png"):
    full_output_path = os.path.join(get_script_dir(), output_path)

    width, height = 1000, 630
    card = Image.new("RGB", (width, height), (243, 245, 248))
    draw = ImageDraw.Draw(card)

    title_font = get_font(40, bold=True)
    label_font = get_font(22, bold=False)
    value_font = get_font(28, bold=False)

    draw.rectangle((0, 0, width, 90), fill=(41, 71, 118))
    draw.text((30, 20), "STATE IDENTIFICATION CARD", fill="white", font=title_font)

    portrait = load_portrait_image(portrait_folder).resize((220, 280))
    card.paste(portrait, (50, 150))
    draw.rectangle((50, 150, 270, 430), outline=(80, 80, 80), width=2)

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


def create_page_1_company_overview(output_dir):
    page, draw = create_blank_page()
    accent = (61, 82, 122)

    draw_sidebar_page_shell(
        draw,
        "New Hire Orientation Overview",
        "Company context, onboarding expectations, and administrative guidance",
        accent=accent
    )

    section_font = get_font(22, True)
    body_font = get_font(18, False)
    small_font = get_font(16, False)

    # right-side meta block
    draw.rectangle((1320, 190, 1620, 320), fill=(245, 247, 250), outline=(170, 176, 185), width=2)
    draw.text((1345, 215), "Prepared By", font=section_font, fill=(55, 62, 74))
    draw.text((1345, 255), "Human Resources", font=body_font, fill="black")
    draw.text((1345, 285), "Employee Services Team", font=small_font, fill=(85, 91, 100))

    # intro section
    draw.text((300, 210), "Company Overview", font=section_font, fill=(47, 53, 65))
    draw.line((300, 246, 1280, 246), fill=(120, 128, 140), width=2)

    y = 270
    intro_text = (
        "Welcome to ExampleCorp. This onboarding packet is intended to provide general information about company "
        "operations, new hire expectations, administrative setup, and early employment processes. The material on this "
        "page is intentionally broad and non-personal so that document-processing workflows can distinguish general "
        "business language from employee-specific content that appears elsewhere in the packet.\n\n"
        "ExampleCorp maintains a collaborative work environment centered on professionalism, accountability, and clear "
        "communication. Depending on role and department, onboarding may include policy review, systems-access setup, "
        "equipment assignment, payroll processing, benefits enrollment, manager introductions, and role-specific training. "
        "Some activities may take place before the employee's first day, while others may continue during the initial "
        "weeks of employment.\n\n"
        "Employees may receive guidance related to conduct, confidentiality, acceptable use of company systems, attendance, "
        "security awareness, manager communication, records handling, and administrative reporting expectations. General "
        "policy language such as this should remain visible after redaction because it does not contain employee-specific identifiers."
    )
    y = draw_wrapped_text(draw, intro_text, body_font, 300, y, 980, line_spacing=8)

    # three-column style blocks
    top = 760
    col_w = 400

    draw.rectangle((300, top, 300 + col_w, top + 420), fill=(248, 249, 251), outline=(175, 180, 188), width=2)
    draw.text((320, top + 24), "Onboarding Milestones", font=section_font, fill=(47, 53, 65))
    y1 = top + 70
    milestones = [
        "Complete required new hire forms",
        "Confirm payroll and direct deposit setup",
        "Review benefits and enrollment deadlines",
        "Receive equipment and access instructions",
        "Attend manager orientation meeting",
        "Review confidentiality and security policies"
    ]
    for item in milestones:
        y1 = draw_checkbox_line(draw, 322, y1, item, small_font)

    draw.rectangle((730, top, 730 + col_w, top + 420), fill=(248, 249, 251), outline=(175, 180, 188), width=2)
    draw.text((750, top + 24), "Administrative Expectations", font=section_font, fill=(47, 53, 65))
    admin_text = (
        "Employees should review assigned onboarding tasks carefully and complete any requested documentation within the "
        "timelines provided by Human Resources. Role, location, and employment type may affect which forms and setup "
        "steps apply."
    )
    draw_wrapped_text(draw, admin_text, small_font, 750, top + 72, 350, line_spacing=7)

    draw.rectangle((1160, top, 1160 + col_w, top + 420), fill=(248, 249, 251), outline=(175, 180, 188), width=2)
    draw.text((1180, top + 24), "Records Handling Notes", font=section_font, fill=(47, 53, 65))
    records_text = (
        "General informational content on this page is intended to remain visible after redaction. Its purpose is to "
        "simulate realistic handbook and HR packet language that should not be removed when employee-specific identifiers "
        "are processed elsewhere in the document set."
    )
    draw_wrapped_text(draw, records_text, small_font, 1180, top + 72, 350, line_spacing=7)

    # bottom wide text
    draw.text((300, 1260), "General Corporate Guidance", font=section_font, fill=(47, 53, 65))
    draw.line((300, 1295, 1620, 1295), fill=(120, 128, 140), width=2)

    bottom_text = (
        "This onboarding packet may include general company policy and process information related to employment setup, "
        "equipment provisioning, payroll timing, benefits activation, and internal systems access. Employees may also be "
        "asked to provide government-issued identification, tax-related materials, emergency contact information, and "
        "payroll details as part of standard new hire processing.\n\n"
        "Completion of administrative paperwork does not replace role-specific instruction or manager-led onboarding. "
        "Employees should follow all deadlines and communication instructions provided by Human Resources and departmental "
        "leadership.\n\n"
        "Large blocks of non-sensitive text are intentionally included here to create a realistic corporate packet where "
        "most content should remain readable after redaction."
    )
    draw_wrapped_text(draw, bottom_text, body_font, 300, 1325, 1320, line_spacing=8)

    output_path = os.path.join(output_dir, "page_1.png")
    page.save(output_path)
    return output_path


def create_page_2_employee_summary(data, output_dir):
    page, draw = create_blank_page()
    accent = (82, 73, 120)

    draw_sidebar_page_shell(
        draw,
        "Employee Summary Memo",
        "Internal HR routing summary with limited employee identifiers",
        accent=accent
    )

    section_font = get_font(22, True)
    body_font = get_font(18, False)
    label_font = get_font(17, True)
    small_font = get_font(16, False)

    # memo style heading
    draw.text((300, 210), "Internal Summary", font=section_font, fill=(52, 48, 72))
    draw.line((300, 246, 1620, 246), fill=(132, 126, 158), width=2)

    # memo metadata block
    meta_x1, meta_y1, meta_x2, meta_y2 = 300, 280, 1620, 430
    draw.rectangle((meta_x1, meta_y1, meta_x2, meta_y2), outline=(170, 176, 188), width=2)
    draw.line((300, 330, 1620, 330), fill=(170, 176, 188), width=1)
    draw.line((620, 280, 620, 430), fill=(170, 176, 188), width=1)
    draw.line((980, 280, 980, 430), fill=(170, 176, 188), width=1)
    draw.line((1300, 280, 1300, 430), fill=(170, 176, 188), width=1)

    draw.text((320, 295), "To", font=label_font, fill=(75, 80, 90))
    draw.text((320, 350), "From", font=label_font, fill=(75, 80, 90))
    draw.text((640, 295), "Employee", font=label_font, fill=(75, 80, 90))
    draw.text((640, 350), "Packet ID", font=label_font, fill=(75, 80, 90))
    draw.text((1000, 295), "Department", font=label_font, fill=(75, 80, 90))
    draw.text((1000, 350), "Start Date", font=label_font, fill=(75, 80, 90))
    draw.text((1320, 295), "Prepared By", font=label_font, fill=(75, 80, 90))
    draw.text((1320, 350), "Date", font=label_font, fill=(75, 80, 90))

    draw.text((360, 295), "Onboarding Team", font=body_font, fill="black")
    draw.text((360, 350), "Human Resources", font=body_font, fill="black")
    draw.text((735, 295), data["full_name"], font=body_font, fill="black")
    draw.text((735, 350), data["packet_id"], font=body_font, fill="black")
    draw.text((1090, 295), data["department"], font=body_font, fill="black")
    draw.text((1090, 350), data["start_date"], font=body_font, fill="black")
    draw.text((1415, 295), "HR Services", font=body_font, fill="black")
    draw.text((1415, 350), data["date_created"], font=body_font, fill="black")

    # memo body
    draw.text((300, 485), "Summary Narrative", font=section_font, fill=(52, 48, 72))
    draw.line((300, 520, 1620, 520), fill=(132, 126, 158), width=2)

    narrative = (
        f"This memo summarizes onboarding materials prepared for {data['full_name']}, who is expected to join the "
        f"{data['department']} department as a {data['job_title']}. The employee's anticipated start date is "
        f"{data['start_date']}, and the current work location on file is {data['location']}. The purpose of this page "
        "is to provide an internal overview that blends ordinary HR process language with a smaller amount of employee "
        "information.\n\n"
        f"The personal contact details currently on file include phone number {data['phone']} and email address "
        f"{data['email']}. A company email account may be assigned as {data['work_email']} during systems setup. "
        f"{data['preferred_name']} is expected to report to {data['manager']} and may receive onboarding tasks related "
        "to payroll, direct deposit, benefits enrollment, equipment issue, internal systems access, and policy acknowledgment.\n\n"
        "If documentation is incomplete or unclear, Human Resources may request clarification before the employee's start "
        "date. Narrative content such as this should remain readable after redaction where no employee-specific identifiers appear."
    )
    y = draw_wrapped_text(draw, narrative, body_font, 300, 545, 1320, line_spacing=8)

    # two-column notes / snapshot
    left_x1, left_y1, left_x2, left_y2 = 300, y + 30, 930, y + 500
    right_x1, right_y1, right_x2, right_y2 = 990, y + 30, 1620, y + 500

    draw.rectangle((left_x1, left_y1, left_x2, left_y2), outline=(170, 176, 188), width=2)
    draw.text((left_x1 + 18, left_y1 + 16), "HR Workflow Notes", font=section_font, fill=(52, 48, 72))

    notes_y = left_y1 + 62
    notes = [
        "Confirm onboarding forms are complete and legible",
        "Verify payroll and direct deposit information",
        "Validate emergency contact details",
        "Coordinate equipment and systems access setup",
        "Retain non-sensitive business text after redaction",
        "Escalate unreadable ID or conflicting details",
        "Confirm benefits enrollment timeline"
    ]
    for note in notes:
        notes_y = draw_checkbox_line(draw, left_x1 + 20, notes_y, note, small_font, outline=(97, 103, 118))

    draw.rectangle((right_x1, right_y1, right_x2, right_y2), outline=(170, 176, 188), width=2)
    draw.text((right_x1 + 18, right_y1 + 16), "Quick Snapshot", font=section_font, fill=(52, 48, 72))

    snap_y = right_y1 + 62
    snapshot_rows = [
        ("Employee ID", data["employee_id"]),
        ("Department", data["department"]),
        ("Job Title", data["job_title"]),
        ("Manager", data["manager"]),
        ("Employment Type", data["employment_type"]),
        ("Pay Type", data["pay_type"]),
        ("Benefits", data["benefits_plan"]),
    ]
    row_h = 44
    for label, value in snapshot_rows:
        draw_table_row(draw, right_x1 + 18, snap_y, right_x2 - 18, snap_y + row_h, label, value, label_font, small_font)
        snap_y += row_h

    output_path = os.path.join(output_dir, "page_2.png")
    page.save(output_path)
    return output_path


def create_page_3_onboarding_form(data, license_image_path, output_dir):
    page, draw = create_blank_page()
    accent = (90, 61, 98)

    draw_sidebar_page_shell(
        draw,
        "Employee Onboarding Worksheet",
        "Structured administrative form with dense employee information",
        accent=accent
    )

    section_font = get_font(21, True)
    body_font = get_font(17, False)
    label_font = get_font(16, True)
    small_font = get_font(15, False)

    # worksheet header box
    draw.rectangle((300, 205, 1620, 300), outline=(165, 171, 181), width=2)
    draw.text((325, 225), "ONBOARDING RECORD", font=section_font, fill=(72, 48, 80))
    draw.text((325, 258), f"Packet ID: {data['packet_id']}", font=small_font, fill="black")
    draw.text((610, 258), f"Employee ID: {data['employee_id']}", font=small_font, fill="black")
    draw.text((900, 258), f"Created: {data['date_created']}", font=small_font, fill="black")
    draw.text((1180, 258), f"Start Date: {data['start_date']}", font=small_font, fill="black")

    y = 340

    # Section titles without colored boxes
    draw.text((300, y), "Employee Information", font=section_font, fill=(72, 48, 80))
    draw.line((300, y + 30, 1620, y + 30), fill=(160, 146, 170), width=2)
    y += 48

    row_h = 42
    left_rows = [
        ("Full Name", data["full_name"]),
        ("Preferred Name", data["preferred_name"]),
        ("Date of Birth", data["dob"]),
        ("Phone Number", data["phone"]),
        ("Email Address", data["email"]),
        ("Last 4 of SSN", data["ssn_last4"]),
    ]
    right_rows = [
        ("Street Address", data["street"]),
        ("City / State / ZIP", f"{data['city']}, {data['state']} {data['zip']}"),
        ("Department", data["department"]),
        ("Job Title", data["job_title"]),
        ("Manager", data["manager"]),
        ("Location", data["location"]),
    ]

    left_y = y
    for label, value in left_rows:
        draw_table_row(draw, 300, left_y, 930, left_y + row_h, label, value, label_font, body_font)
        left_y += row_h

    right_y = y
    for label, value in right_rows:
        draw_table_row(draw, 990, right_y, 1620, right_y + row_h, label, value, label_font, body_font)
        right_y += row_h

    y = max(left_y, right_y) + 28

    draw.text((300, y), "Employment, Payroll, and Benefits", font=section_font, fill=(72, 48, 80))
    draw.line((300, y + 30, 1620, y + 30), fill=(160, 146, 170), width=2)
    y += 48

    mid_rows = [
        ("Employment Type", data["employment_type"]),
        ("Pay Type", data["pay_type"]),
        ("Compensation", data["salary"]),
        ("Benefits Package", data["benefits_plan"]),
        ("Bank Name", data["bank_name"]),
        ("Routing Last 4", data["routing_last4"]),
        ("Account Last 4", data["account_last4"]),
    ]
    current_y = y
    for label, value in mid_rows:
        draw_table_row(draw, 300, current_y, 1620, current_y + row_h, label, value, label_font, body_font)
        current_y += row_h

    y = current_y + 28

    draw.text((300, y), "Emergency Contact and Assigned Equipment", font=section_font, fill=(72, 48, 80))
    draw.line((300, y + 30, 1620, y + 30), fill=(160, 146, 170), width=2)
    y += 48

    left_rows = [
        ("Emergency Contact", data["emergency_contact"]),
        ("Relationship", data["emergency_relationship"]),
        ("Emergency Phone", data["emergency_phone"]),
    ]
    right_rows = [
        ("Company Email", data["work_email"]),
        ("Assigned Equipment", data["equipment"]),
    ]

    left_y = y
    for label, value in left_rows:
        draw_table_row(draw, 300, left_y, 930, left_y + row_h, label, value, label_font, body_font)
        left_y += row_h

    right_y = y
    for label, value in right_rows:
        draw_table_row(draw, 990, right_y, 1620, right_y + row_h, label, value, label_font, body_font)
        right_y += row_h

    y = max(left_y, right_y) + 28

    draw.text((300, y), "Employee Certification", font=section_font, fill=(72, 48, 80))
    draw.line((300, y + 30, 1620, y + 30), fill=(160, 146, 170), width=2)
    y += 48

    cert_text = (
        "I certify that the information provided in this onboarding worksheet is complete and accurate to the best of my "
        "knowledge. I understand that this information may be used for employment setup, payroll administration, benefits "
        "processing, emergency contact records, and internal human-resources documentation. I acknowledge that additional "
        "documentation may be requested if submitted information is incomplete, inconsistent, or unclear."
    )
    y = draw_wrapped_text(draw, cert_text, body_font, 300, y, 1320, line_spacing=7)

    # signature lines
    y += 18
    draw.line((300, y + 35, 620, y + 35), fill="black", width=2)
    draw.text((300, y + 45), "Employee Signature", font=small_font, fill="black")
    draw.line((720, y + 35, 960, y + 35), fill="black", width=2)
    draw.text((720, y + 45), "Date", font=small_font, fill="black")

    # bottom identification review section
    box_top = 1520
    draw.text((300, box_top), "Identification Review", font=section_font, fill=(72, 48, 80))
    draw.line((300, box_top + 30, 1620, box_top + 30), fill=(160, 146, 170), width=2)

    license_img = Image.open(license_image_path).convert("RGB")
    license_img = license_img.resize((700, 440))
    image_x = 300
    image_y = box_top + 55
    page.paste(license_img, (image_x, image_y))
    draw.rectangle((image_x - 2, image_y - 2, image_x + 702, image_y + 442), outline=(92, 92, 92), width=2)

    # right summary table
    summary_x1 = 1040
    summary_y = image_y
    summary_rows = [
        ("Document Type", "State Identification Card"),
        ("ID Number", data["license_number"]),
        ("Issue Date", data["issue_date"]),
        ("Expiration Date", data["exp_date"]),
        ("Review Status", "Received"),
    ]
    for label, value in summary_rows:
        draw_table_row(draw, summary_x1, summary_y, 1620, summary_y + 42, label, value, label_font, small_font)
        summary_y += 42

    note = (
        "Attached identification is included as part of the onboarding packet for administrative verification and "
        "document-processing evaluation. This section is intended to combine structured employee data with embedded image content."
    )
    draw_wrapped_text(draw, note, small_font, 1040, summary_y + 18, 580, line_spacing=6)

    output_path = os.path.join(output_dir, "page_3.png")
    page.save(output_path)
    return output_path


def create_employee_packet(data, license_image_path):
    output_dir = os.path.join(get_script_dir(), "employee_packet")
    os.makedirs(output_dir, exist_ok=True)

    page_1 = create_page_1_company_overview(output_dir)
    page_2 = create_page_2_employee_summary(data, output_dir)
    page_3 = create_page_3_onboarding_form(data, license_image_path, output_dir)

    return [page_1, page_2, page_3]


def combine_pages_to_pdf(image_paths, output_pdf="employee_onboarding_packet.pdf"):
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
        print("Generating fake employee data...")
        data = generate_fake_employee_data()

        print("Creating synthetic ID image...")
        license_path = create_synthetic_license(
            data=data,
            portrait_folder="faces",
            output_path="employee_license.png"
        )

        print("Creating reformatted 3-page employee packet...")
        pages = create_employee_packet(data, license_path)

        print("Combining pages into PDF...")
        pdf_path = combine_pages_to_pdf(pages, output_pdf="employee_onboarding_packet.pdf")

        print("\nCreated files:")
        print("License:", license_path)
        for page in pages:
            print("Page:", page)
        print("PDF:", pdf_path)

    except Exception as e:
        print("Error:", e)