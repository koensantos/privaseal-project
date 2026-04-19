from faker import Faker
from PIL import Image, ImageDraw, ImageFont
import random
import os
import textwrap

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


def draw_wrapped_text(draw, text, font, x, y, max_width, line_spacing=10, fill="black"):
    paragraphs = text.split("\n")
    for paragraph in paragraphs:
        if not paragraph.strip():
            y += 20
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


def draw_checkbox_line(draw, x, y, text, font):
    draw.rectangle((x, y + 4, x + 18, y + 22), outline="black", width=2)
    draw.text((x + 30, y), text, font=font, fill="black")
    return y + 36


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


def generate_fake_applicant_data():
    return {
        "submission_id": f"APP-{random.randint(100000, 999999)}",
        "date_received": fake.date_between(start_date="-120d", end_date="today").strftime("%m/%d/%Y"),
        "full_name": fake.name(),
        "dob": fake.date_of_birth(minimum_age=21, maximum_age=75).strftime("%m/%d/%Y"),
        "ssn_last4": str(random.randint(1000, 9999)),
        "phone": fake.phone_number(),
        "email": fake.email(),
        "street": fake.street_address(),
        "city": fake.city(),
        "state": fake.state_abbr(),
        "zip": fake.zipcode(),
        "current_address": fake.address().replace("\n", ", "),
        "previous_address": fake.address().replace("\n", ", "),
        "license_number": str(random.randint(100000000, 999999999)),
        "issue_date": fake.date_between(start_date="-8y", end_date="-1y").strftime("%m/%d/%Y"),
        "exp_date": fake.date_between(start_date="+1y", end_date="+8y").strftime("%m/%d/%Y"),
        "sex": random.choice(["M", "F"]),
        "height": random.choice(["5'-02\"", "5'-04\"", "5'-06\"", "5'-08\"", "5'-10\"", "6'-00\""]),
        "license_class": random.choice(["C", "D", "E"]),
        "unit_preference": random.choice(["Studio", "1 Bedroom", "2 Bedroom"]),
        "move_in_date": fake.date_between(start_date="+7d", end_date="+90d").strftime("%m/%d/%Y"),
        "lease_term": random.choice(["12 Months", "15 Months", "18 Months"]),
        "monthly_rent": f"${random.randint(1600, 3400):,}",
        "employer": fake.company(),
        "job_title": fake.job(),
        "annual_income": f"${random.randint(52000, 145000):,}",
        "work_phone": fake.phone_number(),
        "work_address": fake.address().replace("\n", ", "),
        "occupants": random.choice(["1", "2", "3"]),
        "pets": random.choice(["None", "1 Cat", "1 Dog", "2 Cats", "1 Dog / 1 Cat"]),
        "vehicle_make": random.choice(["Honda", "Toyota", "Ford", "Tesla", "Hyundai", "Chevrolet"]),
        "vehicle_model": random.choice(["Civic", "Camry", "F-150", "Model 3", "Elantra", "Equinox"]),
        "vehicle_plate": fake.license_plate(),
        "emergency_contact": fake.name(),
        "emergency_phone": fake.phone_number(),
        "emergency_relationship": random.choice(["Sibling", "Parent", "Friend", "Spouse", "Partner"]),
        "bank_name": random.choice(["First National Bank", "Summit Credit Union", "Riverbend Bank"]),
        "reference_1_name": fake.name(),
        "reference_1_phone": fake.phone_number(),
        "reference_2_name": fake.name(),
        "reference_2_phone": fake.phone_number(),
        "monthly_income_numeric": random.randint(52000, 145000),
    }


def create_synthetic_license(data, portrait_folder="faces", output_path="license.png"):
    full_output_path = os.path.join(get_script_dir(), output_path)

    width, height = 1000, 630
    card = Image.new("RGB", (width, height), (242, 244, 247))
    draw = ImageDraw.Draw(card)

    title_font = get_font(40, bold=True)
    label_font = get_font(22, bold=False)
    value_font = get_font(28, bold=False)

    draw.rectangle((0, 0, width, 90), fill=(35, 76, 140))
    draw.text((30, 20), "STATE IDENTIFICATION CARD", fill="white", font=title_font)

    portrait = load_portrait_image(portrait_folder).resize((220, 280))
    card.paste(portrait, (50, 150))
    draw.rectangle((50, 150, 270, 430), outline=(70, 70, 70), width=2)

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
            draw.text((x_label, y), label, fill=(90, 90, 90), font=label_font)
        draw.text((x_value, y), value, fill="black", font=value_font)
        y += spacing

    card.save(full_output_path)
    return full_output_path


def create_page_1_community_info(output_dir):
    page, draw = create_blank_page()

    title_font = get_font(42, bold=True)
    heading_font = get_font(28, bold=True)
    body_font = get_font(21, bold=False)
    small_font = get_font(19, bold=False)

    margin = 80
    max_width = 1540
    y = 0

    draw.rectangle((0, 0, 1700, 125), fill=(34, 76, 140))
    draw.text((margin, 34), "Evergreen Heights Apartments", fill="white", font=title_font)

    y = 165
    draw.text((margin, y), "Community Overview", fill="black", font=heading_font)
    y += 55

    overview_text = (
        "Evergreen Heights Apartments is a professionally managed residential community designed to provide a modern, "
        "comfortable, and service-oriented living experience. The property is centrally located near public "
        "transportation, shopping centers, neighborhood restaurants, grocery stores, and several major commuting routes. "
        "This location provides convenient access for residents who value both accessibility and everyday convenience.\n\n"
        "The community offers a wide range of shared amenities intended to support comfort, flexibility, and daily "
        "routine. Residents have access to a fully equipped fitness center, rooftop lounge, business center, package "
        "locker system, reservable co-working rooms, on-site parking garage, landscaped courtyard, and resident club "
        "space for gatherings and events. Additional services include controlled building access, online rent payment, "
        "digital maintenance request submission, and professional on-site support staff.\n\n"
        "Apartment homes are available in multiple layouts, including studio, one-bedroom, and two-bedroom options. "
        "Floor plans may vary by square footage, view, storage availability, and renovation package. Community "
        "standards are intended to promote a clean, quiet, and respectful residential environment for all occupants. "
        "Prospective residents are encouraged to review all application materials, pricing terms, and building policies "
        "before making a final leasing decision."
    )
    y = draw_wrapped_text(draw, overview_text, body_font, margin, y, max_width, line_spacing=8)

    y += 20
    draw.text((margin, y), "Featured Amenities and Services", fill="black", font=heading_font)
    y += 55

    amenities = [
        "24-hour fitness center with cardio equipment and free weights",
        "Resident rooftop lounge with Wi-Fi, seating, and shared social space",
        "Controlled building access and monitored package locker area",
        "Business center and reservable co-working rooms",
        "Covered parking garage and bicycle storage room",
        "Pet-friendly lease options with community pet area",
        "Outdoor landscaped courtyard with grills and seating",
        "Online resident portal for rent payments and maintenance requests",
        "Seasonal resident events and community engagement programming",
    ]

    for item in amenities:
        draw.text((margin + 20, y), f"• {item}", fill="black", font=body_font)
        y += 36

    y += 20
    draw.text((margin, y), "Leasing Policies and General Information", fill="black", font=heading_font)
    y += 55

    policy_text = (
        "Lease pricing, concession offers, and availability are subject to change based on inventory, move-in timing, "
        "and current market conditions. Applicants should confirm all applicable fees, including administrative fees, "
        "security deposits, pet-related charges, parking fees, and utility responsibilities with the leasing office "
        "prior to signing a lease. Amenity access may be subject to building rules, scheduled maintenance, or temporary "
        "closure. Submission of an application does not guarantee approval, and all applicants may be subject to "
        "identity verification, income review, occupancy review, and other standard screening requirements."
    )
    y = draw_wrapped_text(draw, policy_text, body_font, margin, y, max_width, line_spacing=8)

    y += 25
    draw.text((margin, y), "Neighborhood Highlights", fill="black", font=heading_font)
    y += 55

    neighborhood_text = (
        "The surrounding neighborhood includes grocery stores, coffee shops, public parks, pharmacies, and retail "
        "services within a short distance of the property. Residents also benefit from nearby bus and rail access, "
        "fitness and wellness services, and access to major employment corridors. The community is designed to appeal "
        "to applicants seeking a balance of convenience, comfort, and professionally managed apartment living."
    )
    draw_wrapped_text(draw, neighborhood_text, body_font, margin, y, max_width, line_spacing=8)

    output_path = os.path.join(output_dir, "page_1.png")
    page.save(output_path)
    return output_path


def create_page_2_process_and_summary(data, output_dir):
    page, draw = create_blank_page()

    title_font = get_font(40, bold=True)
    heading_font = get_font(28, bold=True)
    body_font = get_font(21, bold=False)
    small_font = get_font(18, bold=False)

    margin = 80
    max_width = 1540

    draw.rectangle((0, 0, 1700, 125), fill=(55, 92, 146))
    draw.text((margin, 36), "Applicant Review Summary and Leasing Process", fill="white", font=title_font)

    y = 170
    draw.text((margin, y), "Applicant Interest Summary", fill="black", font=heading_font)
    y += 55

    summary_text = (
        f"This summary reflects the preliminary leasing interest submitted by {data['full_name']}. "
        f"The applicant has indicated interest in a {data['unit_preference']} apartment home and a proposed move-in "
        f"date of {data['move_in_date']}. The leasing office may use this summary page for early routing, "
        "communication tracking, and review of next-step documentation needs before the full application is finalized.\n\n"
        f"For initial outreach and scheduling purposes, the applicant may be contacted using the information currently "
        f"provided on file. Primary phone contact is listed as {data['phone']}, and primary email contact is listed "
        f"as {data['email']}. At this stage, the summary is intended to blend ordinary administrative narrative with "
        "limited personal identifiers so that document-processing workflows can evaluate whether sensitive information "
        "is distinguished from surrounding non-sensitive business text.\n\n"
        f"{data['full_name']} has also requested more information regarding lease term options, current pricing, "
        "parking availability, pet policies, package management procedures, and the timing of application review. "
        "All interactions related to the applicant's inquiry should be documented in accordance with leasing office "
        "standards and retained within the applicant record where appropriate."
    )
    y = draw_wrapped_text(draw, summary_text, body_font, margin, y, max_width, line_spacing=8)

    y += 18
    draw.text((margin, y), "Application and Screening Process", fill="black", font=heading_font)
    y += 55

    process_text = (
        "The standard leasing process generally includes submission of a completed application, verification of "
        "identity, review of income and employment information, and confirmation of occupancy-related details. "
        "Applicants may also be asked to provide additional supporting documents, including a government-issued photo "
        "identification document, recent pay documentation, proof of current address, or other materials deemed "
        "necessary by the property's screening procedures.\n\n"
        "Once an application packet is complete, the leasing team may review information for legibility, consistency, "
        "and completeness before sending the file to the next step of the approval workflow. Incomplete or unclear "
        "submissions may require follow-up communication. General descriptive sections such as this one are designed "
        "to remain visible after redaction, since they do not contain inherently protected personal information."
    )
    y = draw_wrapped_text(draw, process_text, body_font, margin, y, max_width, line_spacing=8)

    y += 18
    draw.text((margin, y), "Office Notes and Internal Guidance", fill="black", font=heading_font)
    y += 55

    guidance_items = [
        "Confirm current pricing and concession availability before final application review.",
        "Verify desired move-in timing and preferred floor plan if inventory changes.",
        "Provide applicant with parking terms, pet fee schedule, and utility responsibility summary.",
        "Ensure that identity documentation and supporting materials are received in readable format.",
        "Retain informational sections of packet after redaction where no personal information is present.",
        "Escalate any conflicting or incomplete application details for manual review by leasing staff."
    ]

    for item in guidance_items:
        draw.text((margin + 20, y), f"• {item}", fill="black", font=body_font)
        y += 34

    y += 18
    draw.text((margin, y), "Quick Applicant Snapshot", fill="black", font=heading_font)
    y += 55

    snapshot_text = (
        f"Applicant Name: {data['full_name']}\n"
        f"Requested Unit Type: {data['unit_preference']}\n"
        f"Requested Lease Term: {data['lease_term']}\n"
        f"Proposed Move-In Date: {data['move_in_date']}\n"
        f"Household Size Indicated: {data['occupants']}\n"
        f"Estimated Monthly Rent Range: {data['monthly_rent']}"
    )
    draw_wrapped_text(draw, snapshot_text, body_font, margin, y, max_width, line_spacing=8)

    output_path = os.path.join(output_dir, "page_2.png")
    page.save(output_path)
    return output_path


def create_page_3_application(data, license_image_path, output_dir):
    page, draw = create_blank_page()

    title_font = get_font(40, bold=True)
    heading_font = get_font(26, bold=True)
    body_font = get_font(19, bold=False)
    small_font = get_font(16, bold=False)

    margin = 60
    y = 0

    draw.rectangle((0, 0, 1700, 115), fill=(42, 84, 136))
    draw.text((margin, 34), "Residential Lease Application", fill="white", font=title_font)

    y = 145
    draw.text((margin, y), f"Application ID: {data['submission_id']}", font=body_font, fill="black")
    draw.text((1100, y), f"Date Received: {data['date_received']}", font=body_font, fill="black")

    # Section 1
    y += 50
    draw.rectangle((margin, y, 1640, y + 34), fill=(229, 236, 247))
    draw.text((margin + 10, y + 5), "1. Applicant Information", font=heading_font, fill="black")
    y += 48

    left_x = margin + 10
    right_x = 860
    line_gap = 30

    left_fields = [
        f"Full Legal Name: {data['full_name']}",
        f"Date of Birth: {data['dob']}",
        f"Phone Number: {data['phone']}",
        f"Email Address: {data['email']}",
        f"Last 4 of SSN: {data['ssn_last4']}",
    ]

    right_fields = [
        f"Current Street Address: {data['street']}",
        f"City / State / ZIP: {data['city']}, {data['state']} {data['zip']}",
        f"Preferred Unit Type: {data['unit_preference']}",
        f"Requested Lease Term: {data['lease_term']}",
        f"Proposed Move-In Date: {data['move_in_date']}",
    ]

    left_y = y
    for field in left_fields:
        draw.text((left_x, left_y), field, font=body_font, fill="black")
        left_y += line_gap

    right_y = y
    for field in right_fields:
        draw.text((right_x, right_y), field, font=body_font, fill="black")
        right_y += line_gap

    y = max(left_y, right_y) + 12

    # Section 2
    draw.rectangle((margin, y, 1640, y + 34), fill=(229, 236, 247))
    draw.text((margin + 10, y + 5), "2. Residence History", font=heading_font, fill="black")
    y += 48

    draw.text((left_x, y), f"Current Address on File: {data['current_address']}", font=body_font, fill="black")
    y += line_gap
    draw.text((left_x, y), f"Previous Address: {data['previous_address']}", font=body_font, fill="black")
    y += line_gap
    draw.text((left_x, y), "Length of Current Residence: 2 Years 8 Months", font=body_font, fill="black")
    y += line_gap
    draw.text((left_x, y), "Current Housing Status: Renting", font=body_font, fill="black")
    y += 40

    # Section 3
    draw.rectangle((margin, y, 1640, y + 34), fill=(229, 236, 247))
    draw.text((margin + 10, y + 5), "3. Employment and Income Information", font=heading_font, fill="black")
    y += 48

    income_monthly = int(data["monthly_income_numeric"] / 12)

    employment_fields = [
        f"Employer: {data['employer']}",
        f"Job Title / Position: {data['job_title']}",
        f"Work Phone: {data['work_phone']}",
        f"Annual Income: {data['annual_income']}",
        f"Approximate Monthly Income: ${income_monthly:,}",
        f"Employer Address: {data['work_address']}",
    ]

    for field in employment_fields:
        y = draw_wrapped_text(draw, field, body_font, left_x, y, 1520, line_spacing=6)

    y += 10

    # Section 4
    draw.rectangle((margin, y, 1640, y + 34), fill=(229, 236, 247))
    draw.text((margin + 10, y + 5), "4. Household and Additional Information", font=heading_font, fill="black")
    y += 48

    household_left = [
        f"Number of Intended Occupants: {data['occupants']}",
        f"Pets Declared: {data['pets']}",
        f"Emergency Contact: {data['emergency_contact']}",
        f"Emergency Relationship: {data['emergency_relationship']}",
        f"Emergency Phone: {data['emergency_phone']}",
    ]

    household_right = [
        f"Vehicle Make: {data['vehicle_make']}",
        f"Vehicle Model: {data['vehicle_model']}",
        f"Vehicle Plate: {data['vehicle_plate']}",
        f"Primary Banking Institution: {data['bank_name']}",
        "Parking Request: Yes",
    ]

    left_temp_y = y
    for field in household_left:
        draw.text((left_x, left_temp_y), field, font=body_font, fill="black")
        left_temp_y += line_gap

    right_temp_y = y
    for field in household_right:
        draw.text((right_x, right_temp_y), field, font=body_font, fill="black")
        right_temp_y += line_gap

    y = max(left_temp_y, right_temp_y) + 10

    # Section 5
    draw.rectangle((margin, y, 1640, y + 34), fill=(229, 236, 247))
    draw.text((margin + 10, y + 5), "5. Personal References", font=heading_font, fill="black")
    y += 48

    draw.text((left_x, y), f"Reference 1 Name: {data['reference_1_name']}", font=body_font, fill="black")
    draw.text((right_x, y), f"Reference 1 Phone: {data['reference_1_phone']}", font=body_font, fill="black")
    y += line_gap
    draw.text((left_x, y), f"Reference 2 Name: {data['reference_2_name']}", font=body_font, fill="black")
    draw.text((right_x, y), f"Reference 2 Phone: {data['reference_2_phone']}", font=body_font, fill="black")
    y += 40

    # Section 6
    draw.rectangle((margin, y, 1640, y + 34), fill=(229, 236, 247))
    draw.text((margin + 10, y + 5), "6. Applicant Certifications and Authorizations", font=heading_font, fill="black")
    y += 48

    cert_text = (
        "I certify that the information contained in this application is true, complete, and accurate to the best of my "
        "knowledge. I understand that submission of this application does not guarantee approval for tenancy and that "
        "additional documentation may be requested in support of this application. I authorize the leasing office and its "
        "agents to review the information provided for the purpose of evaluating this application, confirming identity, "
        "verifying employment and income, and administering the community's standard screening procedures.\n\n"
        "I understand that incomplete, inconsistent, or misleading information may delay the review process or result in "
        "denial of the application. I further acknowledge that fees, lease terms, and availability are subject to change "
        "prior to final lease execution."
    )
    y = draw_wrapped_text(draw, cert_text, body_font, left_x, y, 1520, line_spacing=6)
    y += 10

    # Section 7
    draw.rectangle((margin, y, 1640, y + 34), fill=(229, 236, 247))
    draw.text((margin + 10, y + 5), "7. Attached Government Identification", font=heading_font, fill="black")
    y += 48

    license_img = Image.open(license_image_path).convert("RGB")
    license_img = license_img.resize((760, 480))
    page.paste(license_img, (left_x, y))
    draw.rectangle((left_x - 3, y - 3, left_x + 763, y + 483), outline="black", width=2)

    notes_x = 900
    draw.text((notes_x, y), "ID Review Summary", font=heading_font, fill="black")
    y_notes = y + 40

    notes_text = (
        f"Document Type: State Identification Card\n"
        f"ID Number: {data['license_number']}\n"
        f"Issue Date: {data['issue_date']}\n"
        f"Expiration Date: {data['exp_date']}\n"
        f"Sex: {data['sex']}\n"
        f"Height: {data['height']}\n"
        f"License Class: {data['license_class']}\n\n"
        "Attached identification is provided as part of the application package for identity verification and "
        "document-processing evaluation."
    )
    draw_wrapped_text(draw, notes_text, body_font, notes_x, y_notes, 650, line_spacing=6)

    footer_y = y + 520
    draw.line((left_x, footer_y, 640, footer_y), fill="black", width=2)
    draw.text((left_x, footer_y + 8), "Applicant Signature", font=small_font, fill="black")

    draw.line((900, footer_y, 1350, footer_y), fill="black", width=2)
    draw.text((900, footer_y + 8), "Date", font=small_font, fill="black")

    output_path = os.path.join(output_dir, "page_3.png")
    page.save(output_path)
    return output_path


def create_lease_packet(data, license_image_path):
    output_dir = os.path.join(get_script_dir(), "lease_packet")
    os.makedirs(output_dir, exist_ok=True)

    page_1 = create_page_1_community_info(output_dir)
    page_2 = create_page_2_process_and_summary(data, output_dir)
    page_3 = create_page_3_application(data, license_image_path, output_dir)

    return [page_1, page_2, page_3]


def combine_pages_to_pdf(image_paths, output_pdf="lease_application_packet.pdf"):
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
        print("Generating fake applicant data...")
        data = generate_fake_applicant_data()

        print("Creating synthetic license image...")
        license_path = create_synthetic_license(
            data=data,
            portrait_folder="faces",
            output_path="license.png"
        )

        print("Creating detailed 3-page lease packet...")
        pages = create_lease_packet(data, license_path)

        print("Combining pages into PDF...")
        pdf_path = combine_pages_to_pdf(pages, output_pdf="lease_application_packet.pdf")

        print("\nCreated files:")
        print("License:", license_path)
        for page in pages:
            print("Page:", page)
        print("PDF:", pdf_path)

    except Exception as e:
        print("Error:", e)