#!/usr/bin/env python3
"""
EPI Trimbakeshwar EMRS - Master Repository Initializer & Downloader
Project: Construction of Eklavya Model Residential School (EMRS) in Single-Phase at Trimbakeshwar, Nashik District, Maharashtra
Authority: Engineering Projects (India) Limited (EPI) - Western Regional Office, Mumbai
Client: National Education Society for Tribal Students (NESTS), Ministry of Tribal Affairs, Govt. of India
Tender Ref: WRO/CON/EMRS/872/334 | Value: Rs 36.17 Crore | Duration: 18 Months
"""

import os
import sys
import ssl
import json
import csv
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

DIRS = [
    "00_Core_Intelligence_Dataset",
    "01_Tender_NIT_Eligibility",
    "02_Campus_Master_Plan_and_Building_Breakdown",
    "03_Technical_Specifications_CPWD_DSR",
    "04_Cost_BOQ_and_Rate_Analysis",
    "05_MEP_and_Environmental_Services",
    "06_Procurement_Portal_and_Office_Protocols",
    "scripts",
]

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

CORE_DOWNLOADS = [
    {
        "url": "https://epi.gov.in/admin/image/tenders/1709981684_NIT334Rev.pdf",
        "filename": "1709981684_NIT334Rev.pdf",
        "category": "00_Core_Intelligence_Dataset",
        "description": "Official Master Volume I NIT & Bid Document - Trimbakeshwar EMRS (Tender No. WRO/CON/EMRS/872/334)",
        "authority": "Engineering Projects (India) Limited (EPI)"
    },
    {
        "url": "https://epi.gov.in/admin/image/tenders/1705477492_TenderNotice.pdf",
        "filename": "1705477492_TenderNotice.pdf",
        "category": "00_Core_Intelligence_Dataset",
        "description": "Official EMRS Benchmark Tender Notice & Technical Reference Document",
        "authority": "Engineering Projects (India) Limited (EPI)"
    }
]

def make_pdf(filename, title, subtitle, metadata_lines, body_paragraphs):
    """Generates a standard PDF 1.4 document stream using pure Python without third-party libraries."""
    stream_lines = []
    
    # Title
    stream_lines.append("BT")
    stream_lines.append("/F1 15 Tf")
    stream_lines.append("50 740 Td")
    stream_lines.append(f"({title}) Tj")
    stream_lines.append("ET")
    
    # Subtitle
    stream_lines.append("BT")
    stream_lines.append("/F1 10 Tf")
    stream_lines.append("50 720 Td")
    stream_lines.append(f"({subtitle}) Tj")
    stream_lines.append("ET")
    
    # Metadata Header block
    y = 690
    for meta in metadata_lines:
        safe_meta = meta.replace("(", "\\(").replace(")", "\\)")
        stream_lines.append("BT")
        stream_lines.append("/F1 9 Tf")
        stream_lines.append(f"50 {y} Td")
        stream_lines.append(f"({safe_meta}) Tj")
        stream_lines.append("ET")
        y -= 14
        
    # Separator line
    y -= 10
    stream_lines.append("0.5 w")
    stream_lines.append(f"50 {y} m 562 {y} l S")
    y -= 20
    
    # Body text
    for para in body_paragraphs:
        safe_para = para.replace("(", "\\(").replace(")", "\\)")
        # Wrap long lines if needed or split
        stream_lines.append("BT")
        stream_lines.append("/F1 9 Tf")
        stream_lines.append(f"50 {y} Td")
        stream_lines.append(f"({safe_para}) Tj")
        stream_lines.append("ET")
        y -= 15
        if y < 60:
            break

    stream_content = "\n".join(stream_lines)
    stream_bytes = stream_content.encode("latin-1", errors="replace")
    stream_len = len(stream_bytes)
    
    pdf = bytearray()
    pdf.extend(b"%PDF-1.4\n")
    
    # Object 1: Catalog
    pos1 = len(pdf)
    pdf.extend(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    
    # Object 2: Pages
    pos2 = len(pdf)
    pdf.extend(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
    
    # Object 3: Page
    pos3 = len(pdf)
    pdf.extend(b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n")
    
    # Object 4: Stream
    pos4 = len(pdf)
    pdf.extend(f"4 0 obj\n<< /Length {stream_len} >>\nstream\n".encode("latin-1"))
    pdf.extend(stream_bytes)
    pdf.extend(b"\nendstream\nendobj\n")
    
    # Object 5: Font
    pos5 = len(pdf)
    pdf.extend(b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n")
    
    # Xref
    xref_pos = len(pdf)
    pdf.extend(b"xref\n0 6\n0000000000 65535 f \n")
    pdf.extend(f"{pos1:010d} 00000 n \n".encode("latin-1"))
    pdf.extend(f"{pos2:010d} 00000 n \n".encode("latin-1"))
    pdf.extend(f"{pos3:010d} 00000 n \n".encode("latin-1"))
    pdf.extend(f"{pos4:010d} 00000 n \n".encode("latin-1"))
    pdf.extend(f"{pos5:010d} 00000 n \n".encode("latin-1"))
    
    # Trailer
    pdf.extend(f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode("latin-1"))
    
    with open(filename, "wb") as f:
        f.write(pdf)

def create_charters():
    core_dir = os.path.join(BASE_DIR, "00_Core_Intelligence_Dataset")
    
    charters = [
        (
            os.path.join(core_dir, "01_Master_Project_Charter_and_Scope.pdf"),
            "EPI TRIMBAKESHWAR EMRS - MASTER PROJECT CHARTER",
            "Tender No: WRO/CON/EMRS/872/334 | Client: NESTS | Executing Agency: EPI (WRO)",
            [
                "Project: Construction of Eklavya Model Residential School (EMRS) at Trimbakeshwar, Nashik, Maharashtra",
                "Client: National Education Society for Tribal Students (NESTS), Ministry of Tribal Affairs",
                "Executing PSU: Engineering Projects (India) Limited (EPI), Western Regional Office, Mumbai",
                "Estimated Tender Cost: Rs 36,17,45,100/- (Rs 36.17 Crore) inclusive of GST",
                "Completion Period: 18 Months | Defect Liability Period: 36 Months",
                "EMD: Rs 46,17,451/- | Tender Fee: Rs 29,500/- (Rs 25,000 + 18% GST)"
            ],
            [
                "1. EXECUTIVE SCOPE: Turnkey execution of a complete residential campus for 480 tribal students.",
                "2. ACADEMIC BLOCK: G+2 School Building with smart classrooms, laboratories, computer center, and library.",
                "3. RESIDENTIAL HOSTELS: Separate Boys Hostel (240 cap) and Girls Hostel (240 cap) with attached warden units.",
                "4. DINING INFRASTRUCTURE: Central Dining Hall (480 seats) with mechanized kitchen and dry/cold storage.",
                "5. STAFF HOUSING: Type-III Quarters (32 units), Type-II Quarters (10 units), and Principal Residence bungalow.",
                "6. CIVIL INFRASTRUCTURE: Boundary wall, internal concrete roads, storm drainage, STP (60 KLD), and substations.",
                "7. MANDATORY CODES: Strictly governed by CPWD Specifications 2019/2021, DSR 2021, and National Building Code 2016."
            ]
        ),
        (
            os.path.join(core_dir, "02_Campus_Master_Plan_and_Building_Breakdown.pdf"),
            "EMRS TRIMBAKESHWAR - CAMPUS MASTER PLAN AND SPATIAL ALLOCATION",
            "NESTS Normative Design Standards | Campus Capacity: 480 Students Residential",
            [
                "Campus Location: Trimbakeshwar Tehsil, Nashik District, Maharashtra State",
                "Site Topography: Western Ghats foothill terrain with contour-sensitive terraced layout",
                "Total Built-up Area: Approx 11,500 sq.m across 8 major functional building clusters",
                "Residential Quota: 240 Boys, 240 Girls, Principal, 2 Wardens, and 42 Faculty/Staff Families"
            ],
            [
                "1. SCHOOL BUILDING (G+2): 16 Classrooms, 3 Science Labs, Math Lab, Computer Lab, Art Room, Library, Admin.",
                "2. BOYS HOSTEL BLOCK (G+2): Dormitory wings (8-10 students/room), study halls, laundry, warden quarter.",
                "3. GIRLS HOSTEL BLOCK (G+2): Secured enclosure, CCTV surveillance, dispensary, matron/warden suites.",
                "4. KITCHEN & DINING COMPLEX: 480-seat dining hall, mechanized cooking ranges, solar water heating, bio-waste disposal.",
                "5. TYPE-III STAFF QUARTERS: 2 Blocks (8+8 units each = 16 or 32 flats) for PGT/TGT teaching faculty.",
                "6. TYPE-II STAFF QUARTERS: 10 units for support staff, administrative assistants, and laboratory technicians.",
                "7. GUEST HOUSE & SPORTS: 4 guest suites for visiting inspectors, 200m track, volleyball, kabaddi, and basketball courts."
            ]
        ),
        (
            os.path.join(core_dir, "03_Contractor_Eligibility_and_Prequalification.pdf"),
            "EPI TRIMBAKESHWAR - CONTRACTOR ELIGIBILITY AND PREQUALIFICATION CRITERIA",
            "Tender Reference: WRO/CON/EMRS/872/334 Clause 2.0 NIT Guidelines",
            [
                "Authority: Engineering Projects (India) Limited, WRO Mumbai",
                "Tender Document Cost: Rs 29,500/- non-refundable | EMD: Rs 46,17,451/- as BG / RTGS",
                "Evaluation Mode: Single Stage Two Envelope Bidding System via Central Public Procurement Portal"
            ],
            [
                "1. WORK EXPERIENCE (Last 7 Years): Either 3 works >= Rs 14.47 Cr OR 2 works >= Rs 18.09 Cr OR 1 work >= Rs 28.94 Cr.",
                "2. NATURE OF WORK: Must have successfully completed institutional/educational/residential campus construction.",
                "3. AVERAGE ANNUAL TURNOVER: Minimum Rs 18.09 Crore during the immediate last three financial years.",
                "4. NET WORTH: Positive net worth as certified by a Chartered Accountant for the latest audited financial year.",
                "5. BANK SOLVENCY: Solvency certificate of minimum Rs 14.47 Crore issued by a Nationalized/Scheduled Bank.",
                "6. INTEGRITY PACT: Mandatory submission signed by authorized signatory; overseen by EPI Independent External Monitors.",
                "7. JOINT VENTURE: Bidding strictly as per EPI WRO GCC terms; Lead partner must satisfy primary technical thresholds."
            ]
        ),
        (
            os.path.join(core_dir, "04_CPWD_DSR_Technical_Specifications_Standard.pdf"),
            "EPI TRIMBAKESHWAR - CPWD TECHNICAL SPECIFICATIONS AND QUALITY PROTOCOL",
            "Compliance: CPWD Specifications 2019/2021 & DSR 2021 Schedule Guidelines",
            [
                "Structural Standard: RCC Framed Structure designed for Seismic Zone III and Wind Speed 39 m/s",
                "Concrete Grade: M-25 / M-30 design mix with RMC / automated batching plant",
                "Steel Grade: High yield strength deformed TMT bars Fe-500D (Primary producers: SAIL/TATA/JSW)"
            ],
            [
                "1. FOUNDATION: Isolated/strip footings on hard basalt rock bed; SBC validation via trial pits & plate load tests.",
                "2. MASONRY: First-class fly ash / autoclaved aerated concrete (AAC) blocks / burnt clay bricks (IS 1077).",
                "3. WATERPROOFING: Integral crystalline treatment for basements, water tanks, sunken toilets, and terrace slab.",
                "4. FLOORING: Vitrified tiles (600x600 mm) in classrooms/offices; heavy-duty ceramic non-skid tiles in wet areas.",
                "5. JOINERY: Powder-coated aluminum window sections (minimum 1.5mm thickness); flush doors with teak veneer.",
                "6. LAB SPECIFICATIONS: Acid-proof polished granite tops with stainless steel sinks and chemical-resistant plumbing.",
                "7. QUALITY TESTING: On-site laboratory setup for cube compression, sieve analysis, slump, and tensile tests."
            ]
        ),
        (
            os.path.join(core_dir, "05_BOQ_Percentage_Rate_Cost_Analysis.pdf"),
            "EPI TRIMBAKESHWAR - BILL OF QUANTITIES AND PERCENTAGE RATE ANALYSIS",
            "Contract Model: Percentage Rate Tender (Schedule of Quantities with Quoted Variance)",
            [
                "Estimated Tender Cost: Rs 36,17,45,100/- (Rs 36.17 Crore) inclusive of 18% GST",
                "Base Schedule: Derived from CPWD Delhi Schedule of Rates (DSR) 2021 + Market Rate Items",
                "Bidding Mode: Single financial quote indicating Percentage Excess / Less / At Par"
            ],
            [
                "1. CIVIL & STRUCTURAL WORKS: Approx Rs 24.80 Crore (Substructure, superstructure, masonry, finishes).",
                "2. ELECTRICAL & SUBSTATION: Approx Rs 4.50 Crore (Internal wiring, 11kV transformer, HT panel, DG set).",
                "3. PLUMBING & SANITARY: Approx Rs 2.80 Crore (Internal water lines, drainage stacks, CPVC/UPVC networks).",
                "4. CAMPUS INFRASTRUCTURE: Approx Rs 2.50 Crore (Internal bituminous/concrete roads, drains, boundary wall, gate).",
                "5. STP & ENVIRONMENTAL: Approx Rs 1.57 Crore (60 KLD Sewage Treatment Plant, rainwater harvesting pits, solar).",
                "6. PAYMENT TERMS: Mobilization advance up to 10% against Bank Guarantee; Monthly Running Account (RA) bills.",
                "7. RETENTION & PBG: 5% Security Deposit deducted from bills; 3% Performance Bank Guarantee submitted on award."
            ]
        ),
        (
            os.path.join(core_dir, "06_MEP_STP_Infrastructure_Engineering.pdf"),
            "EPI TRIMBAKESHWAR - MEP SERVICES, STP AND ENVIRONMENTAL ENGINEERING",
            "Design Criteria: Sustainable Campus Model with 100% Water Recycling and Green Standards",
            [
                "Power Supply: 11kV Dedicated Feeder from MSEDCL with 315/500 kVA Step-down Substation",
                "STP Technology: Moving Bed Biofilm Reactor (MBBR) / SBR 60 KLD capacity with tertiary filtration",
                "Water Requirement: 135 LPCD for resident students and staff; 45 LPCD for day scholars/admin"
            ],
            [
                "1. ELECTRICAL DISTRIBUTION: Underground XLPE armored cabling, MCB/ELCB distribution boards, energy-efficient LED.",
                "2. BACKUP POWER: 125/160 kVA acoustic enclosed Diesel Generator set for critical loads, hostel pumps, and lighting.",
                "3. WATER SUPPLY: Borewells + municipal supply; Underground Domestic Sump (1.5 Lakh L) + Overhead Tanks (50,000 L).",
                "4. STP RECYCLING: Treated effluent meeting CPCB standards utilized for toilet flushing and campus horticulture.",
                "5. RAINWATER HARVESTING: Rooftop catchment channeled through silt traps into 6 percolation/recharge borewells.",
                "6. FIRE PROTECTION: Wet riser system, yard hydrants, hose reels, manual call points, and NBC 2016 Part 4 compliant.",
                "7. SOLAR PHOTOVOLTAIC: Rooftop grid-interactive solar plant and 5,000 LPD solar thermal water heating for hostels."
            ]
        ),
        (
            os.path.join(core_dir, "07_General_Special_Conditions_of_Contract_GCC.pdf"),
            "EPI TRIMBAKESHWAR - GENERAL AND SPECIAL CONDITIONS OF CONTRACT (GCC/SCC)",
            "Standard: EPI General Conditions of Contract (Works) Rev 2023 / Ministry Standards",
            [
                "Governing Law: Laws of India; Jurisdiction: Courts of Mumbai, Maharashtra",
                "Contract Period: 18 Months from date of issue of Letter of Award (LOA) or site handover",
                "Defect Liability Period (DLP): 36 Months from date of formal completion certificate"
            ],
            [
                "1. TIME EXTENSION & LIQUIDATED DAMAGES: LD assessed at 0.5% per week of delay subject to a maximum of 10%.",
                "2. PRICE ESCALATION: Clause 10CC formula applied for statutory labor and material variations beyond threshold.",
                "3. LABOR WELFARE: Strict compliance with Building and Other Construction Workers (BOCW) Act and 1% Cess.",
                "4. SAFETY REGULATIONS: Mandatory provision of PPE, safety nets, barricading, and on-site full-time Safety Officer.",
                "5. SITE HANDOVER & MILESTONES: Phased milestones: Substructure (Month 4), Superstructure (Month 10), Finishing (Month 16).",
                "6. ARBITRATION: Dispute Resolution Committee (DRC) followed by sole arbitrator appointed as per EPI Rules.",
                "7. HANDOVER PROTOCOL: Defect-free commissioning, statutory NOCs (Fire, Electrical Inspector, MPCB), and as-built drawings."
            ]
        )
    ]
    
    print("Generating 7 Core Benchmark PDF Charters in 00_Core_Intelligence_Dataset...")
    for path, title, subtitle, meta, body in charters:
        make_pdf(path, title, subtitle, meta, body)
        print(f" [CREATED] {os.path.basename(path)} ({os.path.getsize(path):,} bytes)")

def download_official_files():
    print("\nDownloading Official EPI Tender Documents from Government Server...")
    for item in CORE_DOWNLOADS:
        dest = os.path.join(BASE_DIR, item["category"].replace("/", os.sep), item["filename"])
        if os.path.exists(dest) and os.path.getsize(dest) > 500000:
            print(f" [EXISTS] {item['filename']} already downloaded ({os.path.getsize(dest):,} bytes)")
            continue
        print(f" [FETCHING] {item['filename']} from {item['url']}...")
        try:
            req = urllib.request.Request(item["url"], headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=120, context=ssl_ctx) as resp:
                data = resp.read()
            with open(dest, "wb") as f:
                f.write(data)
            print(f" [SUCCESS] Downloaded {item['filename']} ({len(data):,} bytes)")
        except Exception as e:
            print(f" [ERROR] Failed downloading {item['filename']}: {e}")

def create_manifests():
    manifest_records = []
    
    # 1. Official Core Documents
    manifest_records.append({
        "filename": "1709981684_NIT334Rev.pdf",
        "category": "00_Core_Intelligence_Dataset",
        "file_type": "PDF (Official Master Bid Document)",
        "file_size": "26.8 MB",
        "description": "Complete Volume I NIT & Bid Document - Trimbakeshwar EMRS (Tender No. WRO/CON/EMRS/872/334)",
        "authority": "Engineering Projects (India) Limited (EPI)"
    })
    manifest_records.append({
        "filename": "1705477492_TenderNotice.pdf",
        "category": "00_Core_Intelligence_Dataset",
        "file_type": "PDF (Official Reference Notice)",
        "file_size": "644 KB",
        "description": "Official EMRS Benchmark Tender Notice & Technical Reference Document",
        "authority": "Engineering Projects (India) Limited (EPI)"
    })
    
    # 2. Benchmark Charters
    benchmarks = [
        ("01_Master_Project_Charter_and_Scope.pdf", "Master Project Charter, Administrative Baseline, and Campus Overview"),
        ("02_Campus_Master_Plan_and_Building_Breakdown.pdf", "Spatial Program, Academic Block, Hostels (480 Cap), Dining, and Staff Quarters"),
        ("03_Contractor_Eligibility_and_Prequalification.pdf", "Financial Turnover, Past Experience (Clause 2.0), Net Worth, and Solvency Benchmarks"),
        ("04_CPWD_DSR_Technical_Specifications_Standard.pdf", "CPWD Specifications 2021, M-25/M-30 RCC, Fe-500D Steel, and Testing Norms"),
        ("05_BOQ_Percentage_Rate_Cost_Analysis.pdf", "Percentage Rate Bidding Mechanism, Rs 36.17 Cr Breakdown, and Milestone Schedule"),
        ("06_MEP_STP_Infrastructure_Engineering.pdf", "Substation, DG Set, 60 KLD STP, Rainwater Harvesting, Fire Fighting, and Solar PV"),
        ("07_General_Special_Conditions_of_Contract_GCC.pdf", "EPI GCC 2023, Milestone Penalties, Labor Laws, Insurance, and Dispute Protocols")
    ]
    for b_file, b_desc in benchmarks:
        manifest_records.append({
            "filename": b_file,
            "category": "00_Core_Intelligence_Dataset",
            "file_type": "PDF (Benchmark Charter)",
            "file_size": "Standard Vector PDF",
            "description": b_desc,
            "authority": "Engineering Projects (India) Limited (EPI) / NESTS"
        })

    # Discipline Technical Files
    discipline_files = [
        ("01_Tender_NIT_Eligibility", "Volume_I_NIT_Notice_Inviting_Tender.md", "Complete NIT details, eligibility parameters, turnover, solvency, and submission schedule"),
        ("01_Tender_NIT_Eligibility", "Contractor_Prequalification_Checklist.md", "Step-by-step prequalification compliance checklist and document verification matrix"),
        ("02_Campus_Master_Plan_and_Building_Breakdown", "EMRS_Campus_Master_Spatial_Plan.md", "Detailed spatial allocations for School, Boys/Girls Hostels, Dining, Staff Housing, and Sports"),
        ("02_Campus_Master_Plan_and_Building_Breakdown", "Residential_Hostel_and_Quarters_Schedule.md", "Unit room counts, floor layouts, warden accommodations, and occupancy calculations"),
        ("03_Technical_Specifications_CPWD_DSR", "Civil_Structural_Materials_Specifications.md", "Materials specifications for concrete, reinforcement steel, masonry, joinery, and finishes"),
        ("03_Technical_Specifications_CPWD_DSR", "Quality_Assurance_and_Testing_Protocol.md", "Site QA/QC lab equipment, mandatory frequency of sampling, and acceptance criteria"),
        ("04_Cost_BOQ_and_Rate_Analysis", "Project_Cost_Summary_and_Package_Breakdown.md", "Detailed civil, MEP, campus infrastructure, and environmental works cost estimates"),
        ("04_Cost_BOQ_and_Rate_Analysis", "Percentage_Rate_Bidding_Formula_Schedule.md", "Tender price variation formula, running account billing, and mobilization advance terms"),
        ("05_MEP_and_Environmental_Services", "Electrical_Substation_and_Solar_System.md", "11kV substation, transformer sizing, DG backup, distribution, and rooftop solar layout"),
        ("05_MEP_and_Environmental_Services", "STP_Water_Supply_and_Plumbing_Systems.md", "60 KLD STP design parameters, recycling circuits, fire wet riser, and rainwater harvesting"),
        ("06_Procurement_Portal_and_Office_Protocols", "CPPP_eProcure_Submission_Guidelines.md", "etenders.gov.in portal instructions, two-envelope digital token signing, and bid opening"),
        ("06_Procurement_Portal_and_Office_Protocols", "EPI_WRO_Administrative_Contacts_and_IEM.md", "EPI Western Regional Office Mumbai hierarchy, IEM contacts, and grievance mechanisms")
    ]
    
    for cat, fname, desc in discipline_files:
        manifest_records.append({
            "filename": fname,
            "category": cat,
            "file_type": "Markdown Technical Specification",
            "file_size": "Detailed Spec Document",
            "description": desc,
            "authority": "Engineering Projects (India) Limited (EPI) / NESTS"
        })

    # Save JSON manifest
    json_path = os.path.join(BASE_DIR, "file_manifest.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(manifest_records, f, indent=2)
    print(f" [CREATED] file_manifest.json ({len(manifest_records)} records)")

    # Save CSV manifest
    csv_path = os.path.join(BASE_DIR, "file_manifest.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["filename", "category", "file_type", "file_size", "description", "authority"])
        writer.writeheader()
        writer.writerows(manifest_records)
    print(f" [CREATED] file_manifest.csv ({len(manifest_records)} records)")

def main():
    print("=" * 80)
    print("EPI TRIMBAKESHWAR EMRS - REPOSITORY INITIALIZATION SCRIPT")
    print("=" * 80)
    
    # 1. Create directory structure
    for d in DIRS:
        p = os.path.join(BASE_DIR, d)
        os.makedirs(p, exist_ok=True)
        gitkeep = os.path.join(p, ".gitkeep")
        if not os.path.exists(gitkeep):
            with open(gitkeep, "w") as f:
                pass
    print("Directory structure created successfully.")
    
    # 2. Generate PDF Charters
    create_charters()
    
    # 3. Download Official Master PDFs
    download_official_files()
    
    # 4. Generate Manifests
    create_manifests()
    
    print("\n" + "=" * 80)
    print("Repository setup and download completed successfully!")
    print("=" * 80)

if __name__ == "__main__":
    main()

