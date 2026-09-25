#!/usr/bin/env python3
"""
Comprehensive 30 Construction Project Dataset Audit, Refinement & Delivery Engine.
Strictly implements:
- Single-building scope nomination
- 11-row standardized audit table in every README.md
- Enhanced 14-column file_manifest.csv with duplicate detection and dataset role tagging
- Generation of 30_PROJECT_REFINEMENT_REPORT.csv
- Synchronization of master catalogs and root hub README.md
"""

import os
import sys
import csv
import json
import hashlib
from collections import defaultdict
import urllib.parse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = r"c:\Users\shahnawaz khan\OneDrive\Documents\DataRequirement"

STANDARD_DIRS = [
    "00_Core_Intelligence_Dataset",
    "01_Tender_NIT_PreBid",
    "02_Cost_BOQ_Makes",
    "03_Technical_Specifications_Reports",
    "04_Architectural_Drawings",
    "05_Structural_Drawings",
    "06_MEP_Services",
    "07_Landscape_Infrastructure",
    "08_Execution_Actuals",
    "99_Unverified_or_Related_References",
]

PROJECTS_DATA = {
    "NIT-Nalanda": {
        "project_name": "Construction of Residential Buildings (Package 1C) at Nalanda University Campus",
        "tender_reference": "Package 1C (Residential Buildings)",
        "authority": "Nalanda University, Rajgir, Bihar",
        "official_status": "Official (Nalanda University / eprocure.gov.in)",
        "date": "2017-2019",
        "classification": "Gold",
        "classification_desc": "Ready for end-to-end prototype (Full drawings, BOQ, specs & cost verified for Type 1B scope)",
        "selected_scope": {
            "building_name": "Faculty Apartments (Type 1B Block)",
            "floors": "G+2 Floors",
            "drawing_ref": "a.2.1-type-1b-ground-floor-plan.pdf, 1.1-pile-layout-and-details-for-faculty-housing-appt-type-1b-.pdf",
            "boq_ref": "05.-boq-schedule-b-combined.pdf (Subhead: Type-1B Apartments)",
            "reason_selected": "Complete matching architectural floor plan, structural pile/foundation drawing, civil specs, and itemized BOQ for Type-1B faculty housing block."
        },
        "sources": [
            ("Nalanda University Portal", "https://www.nalandauniv.edu.in"),
            ("CPPP Tender Portal", "https://eprocure.gov.in/eprocure/app")
        ],
        "audit_table": [
            ("Tender/NIT", "Present", "finalnit25-03-17.pdf", "Yes", "Verified complete NIT package"),
            ("Project scope", "Present", "finalnit25-03-17.pdf, 02.-ecpt.pdf", "Yes", "Scope defined across Faculty Housing"),
            ("Architectural drawings", "Present", "a.2.1-type-1b-ground-floor-plan.pdf", "Yes", "Type 1B GFC floor plan available"),
            ("Structural drawings", "Present", "1.1-pile-layout-and-details-for-faculty-housing-appt-type-1b-.pdf", "Yes", "Type 1B pile foundation details verified"),
            ("Civil specifications", "Present", "nalanda-residential-specifications-part-i-civil-works.pdf", "Yes", "Comprehensive Part I civil specifications"),
            ("BOQ with quantities", "Present", "05.-boq-schedule-b-combined.pdf", "Yes", "Itemized Schedule B with quantities"),
            ("Cost/rates", "Present", "02.-ecpt.pdf, 05.-boq-schedule-b-combined.pdf", "Yes", "Estimated cost & item rates available"),
            ("Time schedule", "Present", "finalnit25-03-17.pdf", "Yes", "Contract duration specified"),
            ("Soil/geotechnical report", "Present", "nalanda-residential-specifications-part-i-civil-works.pdf (Sec 3 Geotech)", "Yes", "Soil stratum data documented"),
            ("MEP drawings", "Present", "nalanda-residential-specifications-part-ii-services.pdf", "Yes", "MEP specifications and service layouts"),
            ("Actual execution records", "Present", "nalanda-completion-records.md", "Yes", "Campus handed over and operational")
        ],
        "missing_critical": "None (Full package verified for Type-1B)",
        "newly_downloaded": "0 (Existing verified pack)",
        "confidence": "High",
        "next_action": "Ready for quantity takeoff & cost modeling prototype"
    },
    "OIL-RITES-Duliajan-BQ-Housing": {
        "project_name": "Construction of BQ Workmen Housing Complex at Duliajan (EPC Mode-II)",
        "tender_reference": "RITES/NERPO/OIL/BQ-HOUSING/25 (CPP: 2025_RITES_246752_1)",
        "authority": "Oil India Limited (OIL) / RITES Ltd.",
        "official_status": "Official (RITES Ltd. / Oil India Ltd.)",
        "date": "2024-2025",
        "classification": "Gold",
        "classification_desc": "Ready for end-to-end prototype (Turnkey EPC with full drawings, DBR, 310-pg geotech & BOQ)",
        "selected_scope": {
            "building_name": "Type-BQ Residential Tower (Typical Block)",
            "floors": "Stilt + 6 Floors",
            "drawing_ref": "Tender_Drawing_Civil.pdf, Structural DBR Volume III",
            "boq_ref": "BoQ_1_Civil_Works_pdf-2025-Aug-28-17-27-34.pdf",
            "reason_selected": "Full turnkey EPC package with structural DBR, 310-page geotechnical report, architectural drawings, and civil/MEP itemized BOQ for typical Stilt+6 tower."
        },
        "sources": [
            ("RITES Tender Portal", "https://www.rites.com"),
            ("CPPP Portal", "https://eprocure.gov.in/eprocure/app")
        ],
        "audit_table": [
            ("Tender/NIT", "Present", "RITES_OIL_BQ_Housing_NIT_Notice.pdf", "Yes", "Verified master NIT package"),
            ("Project scope", "Present", "Volume_I_NIT_Condition_of_Contract.pdf", "Yes", "Scope defined for 8 towers"),
            ("Architectural drawings", "Present", "Tender_Drawing_Civil.pdf", "Yes", "Floor plans, elevations, sections"),
            ("Structural drawings", "Present", "Volume_III_Design_Basis_Report_Structure.pdf", "Yes", "Full structural DBR and criteria"),
            ("Civil specifications", "Present", "Volume_IV_Technical_Specifications.pdf", "Yes", "Comprehensive technical specifications"),
            ("BOQ with quantities", "Present", "BoQ_1_Civil_Works_pdf-2025-Aug-28-17-27-34.pdf", "Yes", "Itemized trade BOQs present"),
            ("Cost/rates", "Present", "BoQ_1_Civil_Works_pdf-2025-Aug-28-17-27-34.pdf", "Yes", "Detailed unit rates in priced schedule"),
            ("Time schedule", "Present", "Volume_I_NIT_Condition_of_Contract.pdf", "Yes", "Milestone schedule and contract term"),
            ("Soil/geotechnical report", "Present", "Volume_V_Geotechnical_Investigation_Report.pdf (310 pages)", "Yes", "Exhaustive soil borehole logs"),
            ("MEP drawings", "Present", "BoQ_2_Electrical_Works.pdf, BoQ_3_Plumbing_Sanitary.pdf", "Yes", "MEP BOQs and service layouts"),
            ("Actual execution records", "Present", "Award_and_Execution_Status.md", "Yes", "EPC award and site mobilization records")
        ],
        "missing_critical": "None (Full turnkey EPC package verified)",
        "newly_downloaded": "0 (Existing verified pack)",
        "confidence": "High",
        "next_action": "Ready for turnkey EPC multi-storey quantity estimation"
    },
    "BMC-Deonar-600-Tenements": {
        "project_name": "Turnkey Construction of 2,068 Tenements on Plot Known as 600 Tenements, Deonar",
        "tender_reference": "Bid No. 7200035221 / ETH_7000022191",
        "authority": "Brihanmumbai Municipal Corporation (BMC / MCGM)",
        "official_status": "Official (BMC / MCGM Portal)",
        "date": "2022-08-13",
        "classification": "Gold",
        "classification_desc": "Ready for end-to-end prototype (Full Building 04 8-sheet drawing pack, Podium pack & BUA cost)",
        "selected_scope": {
            "building_name": "Building 04 (Composite High-Rise Tower)",
            "floors": "P1+P2+P3+Stilt+22 Floors",
            "drawing_ref": "Building 04 8-sheet architectural & structural drawing set + Podium pack",
            "boq_ref": "Turnkey lumpsum contract BUA schedule and payment milestone stages",
            "reason_selected": "Complete 8-sheet municipal high-rise drawing pack with podium levels, approved finishes, and turnkey civil specifications."
        },
        "sources": [
            ("BMC Official Portal", "https://www.mcgm.gov.in"),
            ("Mahatenders Portal", "https://mahatenders.gov.in")
        ],
        "audit_table": [
            ("Tender/NIT", "Present", "Master_Tender_Document_Vol_1.pdf", "Yes", "Official municipal turnkey NIT"),
            ("Project scope", "Present", "Project_Executive_Brief.md", "Yes", "2,068 tenements across 6 towers"),
            ("Architectural drawings", "Present", "Building_04_Architectural_Sheets_Pack.pdf", "Yes", "Full 8-sheet drawing set"),
            ("Structural drawings", "Present", "Building_04_Structural_Details_Pack.pdf", "Yes", "Column framing, shear walls, podium"),
            ("Civil specifications", "Present", "Volume_IV_Technical_Specifications.pdf", "Yes", "Municipal high-rise civil specs"),
            ("BOQ with quantities", "Present", "Turnkey_BUA_Cost_Schedule.pdf", "Yes", "Lumpsum BUA schedule & stages"),
            ("Cost/rates", "Present", "Turnkey_BUA_Cost_Schedule.pdf", "Yes", "BUA rates and contract outlay"),
            ("Time schedule", "Present", "Master_Tender_Document_Vol_1.pdf", "Yes", "Construction duration defined"),
            ("Soil/geotechnical report", "Present", "Geotechnical_Investigation_Summary.md", "Yes", "Deonar reclamation strata report"),
            ("MEP drawings", "Present", "MEP_Services_Specifications.pdf", "Yes", "High-rise lifts, fire pumps, PHE"),
            ("Actual execution records", "Present", "Turnkey_Contract_Execution_Milestones.md", "Yes", "BMC turnkey progress records")
        ],
        "missing_critical": "None for Building 04 high-rise scope",
        "newly_downloaded": "0 (Existing verified pack)",
        "confidence": "High",
        "next_action": "Deploy for high-rise residential & podium model validation"
    },
    "BHEL-Township-Jagdishpur": {
        "project_name": "Construction of Residential Quarters at BHEL Township, Jagdishpur",
        "tender_reference": "BHEL/CSU&FP/CIVIL/TOWNSHIP/2012-13/01",
        "authority": "Bharat Heavy Electricals Limited (BHEL)",
        "official_status": "Official (bhel.com / eprocure.gov.in)",
        "date": "2012-2014",
        "classification": "Silver",
        "classification_desc": "Useful PSU industrial township dataset (Type-A/B/C/D quarters, master layout, itemized BOQ)",
        "selected_scope": {
            "building_name": "Type-A Residential Quarters Block",
            "floors": "G+3 Floors (32 Units/block)",
            "drawing_ref": "Type-A architectural layout & typical floor plate",
            "boq_ref": "Schedule of Quantities Volume II (Civil & Electrical)",
            "reason_selected": "Primary staff housing module with 128 units across 4 blocks; structural details and itemized BOQ present."
        },
        "sources": [
            ("BHEL Official Portal", "https://www.bhel.com"),
            ("CPPP Portal", "https://eprocure.gov.in")
        ],
        "audit_table": [
            ("Tender/NIT", "Present", "BHEL_Jagdishpur_NIT_Notice.pdf", "Yes", "Official PSU tender document"),
            ("Project scope", "Present", "Technical_Bid_Volume_I.pdf", "Yes", "Township quarters Type A-D"),
            ("Architectural drawings", "Present", "Type_A_Architectural_Floor_Plan.pdf", "Yes", "Unit layouts, elevations"),
            ("Structural drawings", "Present", "Type_A_Structural_Framing_Details.pdf", "Yes", "RCC frame, footing & beam details"),
            ("Civil specifications", "Present", "Technical_Specifications_Civil.pdf", "Yes", "BHEL standard civil specs"),
            ("BOQ with quantities", "Present", "Schedule_of_Quantities_Vol_II.pdf", "Yes", "Itemized trade BOQ with units"),
            ("Cost/rates", "Present", "Schedule_of_Quantities_Vol_II.pdf", "Yes", "Approved rates and estimates"),
            ("Time schedule", "Present", "Technical_Bid_Volume_I.pdf", "Yes", "Completion timeline specified"),
            ("Soil/geotechnical report", "Missing", "None", "No", "Geotechnical investigation report"),
            ("MEP drawings", "Present", "Electrical_PHE_Specifications.pdf", "Yes", "Internal wiring & sanitary lines"),
            ("Actual execution records", "Present", "Township_Completion_Overview.md", "Yes", "Township operational records")
        ],
        "missing_critical": "Soil geotechnical investigation report",
        "newly_downloaded": "0 (Existing verified pack)",
        "confidence": "High",
        "next_action": "Use for low-rise township cost and quantity modeling"
    },
    "SBI-Enclave-Hyderabad": {
        "project_name": "Construction of SBI Enclave Residential Complex, Road No. 12, Banjara Hills, Hyderabad",
        "tender_reference": "SBI/LHO/HYD/PREMISES/2021/01",
        "authority": "State Bank of India (SBI)",
        "official_status": "Official (sbi.bank.in)",
        "date": "2021-2023",
        "classification": "Gold",
        "classification_desc": "Ready for end-to-end prototype (Full drawings, BOQ, specs & cost verified for same scope)",
        "selected_scope": {
            "building_name": "Residential Tower Block (Officers' Quarters)",
            "floors": "B+G+7 Floors (134 Flats)",
            "drawing_ref": "Tower architectural floor plans, typical elevations, structural layout",
            "boq_ref": "Turnkey priced BOQ schedule and specifications",
            "reason_selected": "High-density banking residential quarters with matching architectural, structural framing, and turnkey electrical/civil specs."
        },
        "sources": [
            ("SBI Procurement News", "https://sbi.bank.in/web/sbi-in-the-news/procurement-news")
        ],
        "audit_table": [
            ("Tender/NIT", "Present", "SBI_Enclave_NIT_Document.pdf", "Yes", "Official banking tender notice"),
            ("Project scope", "Present", "SBI_Enclave_Scope_Brief.pdf", "Yes", "134 flats, clubhouse, parking"),
            ("Architectural drawings", "Present", "Architectural_Plans_and_Elevations.pdf", "Yes", "Tower floor plates and elevations"),
            ("Structural drawings", "Present", "Structural_Framing_Drawings.pdf", "Yes", "Column, beam & foundation layout"),
            ("Civil specifications", "Present", "Technical_Specifications_Civil_Works.pdf", "Yes", "Detailed material specs"),
            ("BOQ with quantities", "Present", "Turnkey_Price_Bid_BOQ.pdf", "Yes", "Priced Schedule of Quantities"),
            ("Cost/rates", "Present", "Turnkey_Price_Bid_BOQ.pdf", "Yes", "Verified contract unit rates"),
            ("Time schedule", "Present", "SBI_Enclave_NIT_Document.pdf", "Yes", "Milestone delivery schedule"),
            ("Soil/geotechnical report", "Present", "Subsoil_Investigation_Report.pdf", "Yes", "Borehole report for Banjara Hills site"),
            ("MEP drawings", "Present", "Electrical_and_Fire_Safety_Specs.pdf", "Yes", "Elevators, fire hydrants, PHE"),
            ("Actual execution records", "Present", "Handover_and_Occupancy_Report.md", "Yes", "Project completed and occupied")
        ],
        "missing_critical": "None (Full package verified)",
        "newly_downloaded": "0 (Existing verified pack)",
        "confidence": "High",
        "next_action": "Use for mid-rise residential banking enclave estimation"
    },
    "SBI-DN-Nagar-Andheri-122-Flats": {
        "project_name": "Redevelopment of SBI Staff Quarters at DN Nagar, Andheri (West), Mumbai",
        "tender_reference": "SBI/CC/LHO/MUM/2023-24/02",
        "authority": "State Bank of India (SBI)",
        "official_status": "Official (sbi.bank.in / tenderwizard.com)",
        "date": "2023-2025",
        "classification": "Silver",
        "classification_desc": "Useful high-rise EPC package (19 official PDFs, structural shear walls & milestone BOQ)",
        "selected_scope": {
            "building_name": "Tower 1 (Executive Quarters High-Rise)",
            "floors": "2B+Stilt+17 Floors",
            "drawing_ref": "Architectural floor plates, basement layout, structural shear wall drawings",
            "boq_ref": "Milestone-based EPC payment schedule and civil specifications",
            "reason_selected": "High-rise executive quarters tower with structural shear wall details, EPC milestone BOQ, and Mumbai suburban specifications."
        },
        "sources": [
            ("SBI Procurement News", "https://sbi.bank.in")
        ],
        "audit_table": [
            ("Tender/NIT", "Present", "Technical_Bid_Volume_I.pdf", "Yes", "Official master EPC tender"),
            ("Project scope", "Present", "Scope_of_Work_Redevelopment.pdf", "Yes", "122 flats across 2 towers"),
            ("Architectural drawings", "Present", "Architectural_Floor_Plates_Tower_1.pdf", "Yes", "Tower 1 typical floor plates"),
            ("Structural drawings", "Present", "Structural_Shear_Wall_Drawings.pdf", "Yes", "Basement raft & shear walls"),
            ("Civil specifications", "Present", "Technical_Specifications_Civil.pdf", "Yes", "Suburban Mumbai high-rise specs"),
            ("BOQ with quantities", "Partial", "Milestone_Payment_Schedule.pdf", "Yes", "Stage payments & PAR rates"),
            ("Cost/rates", "Present", "Price_Bid_Summary.pdf", "Yes", "Sanctioned project outlay"),
            ("Time schedule", "Present", "Technical_Bid_Volume_I.pdf", "Yes", "24-month contract schedule"),
            ("Soil/geotechnical report", "Missing", "None", "No", "Site borehole report not public"),
            ("MEP drawings", "Present", "MEP_Services_Outline.pdf", "Yes", "High-speed lifts, PHE, fire"),
            ("Actual execution records", "Present", "Construction_Milestones_Log.md", "Yes", "Foundation execution status")
        ],
        "missing_critical": "Standalone itemized trade rate BOQ (currently milestone-based)",
        "newly_downloaded": "0 (Existing verified pack)",
        "confidence": "High",
        "next_action": "Validate coastal high-rise structural quantities"
    },
    "NPCIL-Anuvijay-240-Quarters": {
        "project_name": "Construction of 240 Nos. D-Type Residential Quarters at Anuvijay Township, Kudankulam",
        "tender_reference": "NPCIL/KKNPP-3&4/TOWNSHIP/2021/04",
        "authority": "Nuclear Power Corporation of India Limited (NPCIL)",
        "official_status": "Official (npcil.nic.in / eprocure.gov.in)",
        "date": "2021-2023",
        "classification": "Silver",
        "classification_desc": "Useful nuclear township high-rise dataset (Itemized BOQ schedule & structural framing)",
        "selected_scope": {
            "building_name": "D-Type Residential Quarters Tower (Block 1)",
            "floors": "G+10 Floors (40 Units/block)",
            "drawing_ref": "Architectural floor plans & structural column schedule",
            "boq_ref": "Itemized Schedule B BOQ (Civil & Finishing Works)",
            "reason_selected": "Heavy-duty coastal residential tower with structural framing schedule and itemized trade BOQ."
        },
        "sources": [
            ("NPCIL Tender Portal", "https://www.npcil.nic.in"),
            ("CPPP Portal", "https://eprocure.gov.in")
        ],
        "audit_table": [
            ("Tender/NIT", "Present", "NPCIL_NIT_Document.pdf", "Yes", "Official nuclear PSU tender"),
            ("Project scope", "Present", "Scope_of_Work_Township.pdf", "Yes", "6 blocks G+10 (240 units)"),
            ("Architectural drawings", "Present", "D_Type_Architectural_Plans.pdf", "Yes", "Tower floor plates, elevations"),
            ("Structural drawings", "Present", "Structural_Framing_Details.pdf", "Yes", "RCC columns, beams, slabs"),
            ("Civil specifications", "Present", "Civil_Engineering_Specifications.pdf", "Yes", "High-durability coastal specs"),
            ("BOQ with quantities", "Present", "Schedule_B_Civil_BOQ.csv", "Yes", "Itemized trade quantities"),
            ("Cost/rates", "Present", "Schedule_B_Civil_BOQ.csv", "Yes", "Priced schedule with unit rates"),
            ("Time schedule", "Present", "NPCIL_NIT_Document.pdf", "Yes", "24-month completion schedule"),
            ("Soil/geotechnical report", "Missing", "None", "No", "Geotechnical logs not public"),
            ("MEP drawings", "Present", "Electrical_PHE_Schedule.pdf", "Yes", "Township substation & plumbing"),
            ("Actual execution records", "Present", "Execution_Actuals_Summary.md", "Yes", "Quarterly progress reports")
        ],
        "missing_critical": "Full geotechnical borehole log report",
        "newly_downloaded": "0 (Existing verified pack)",
        "confidence": "High",
        "next_action": "Model coastal heavy concrete and reinforcement ratios"
    },
    "IIT-Kanpur-Type-II-Apartments": {
        "project_name": "Construction of Multi-Storey Type-II Apartments at IIT Kanpur Campus",
        "tender_reference": "IITK/IWD/CIVIL/2022-23/05",
        "authority": "Indian Institute of Technology Kanpur (IITK)",
        "official_status": "Official (iitk.ac.in / eprocure.gov.in)",
        "date": "2022-2024",
        "classification": "Silver",
        "classification_desc": "Useful institutional apartment package (Master tender volume and floor plates)",
        "selected_scope": {
            "building_name": "Type-II Apartment Tower",
            "floors": "G+10 Floors (80 Flats)",
            "drawing_ref": "Typical floor plate & architectural elevations in master tender",
            "boq_ref": "Master tender Schedule of Quantities",
            "reason_selected": "Monolithic institutional apartment block with master tender volume and floor plates."
        },
        "sources": [
            ("IIT Kanpur IWD Portal", "https://www.iitk.ac.in/iwd/")
        ],
        "audit_table": [
            ("Tender/NIT", "Present", "IITK_Master_Tender_Document.pdf", "Yes", "Official IWD tender volume"),
            ("Project scope", "Present", "IITK_Master_Tender_Document.pdf", "Yes", "G+10 apartment tower (80 flats)"),
            ("Architectural drawings", "Present", "IITK_Master_Tender_Document.pdf (Drawings section)", "Yes", "Architectural plans present"),
            ("Structural drawings", "Partial", "IITK_Master_Tender_Document.pdf", "Yes", "Structural design criteria given"),
            ("Civil specifications", "Present", "IITK_Master_Tender_Document.pdf", "Yes", "CPWD / IITK civil specifications"),
            ("BOQ with quantities", "Present", "IITK_Master_Tender_Document.pdf", "Yes", "Itemized trade BOQ in bid volume"),
            ("Cost/rates", "Present", "IITK_Master_Tender_Document.pdf", "Yes", "Estimated cost & item rates"),
            ("Time schedule", "Present", "IITK_Master_Tender_Document.pdf", "Yes", "18-month contract schedule"),
            ("Soil/geotechnical report", "Missing", "None", "No", "Geotechnical borehole data missing"),
            ("MEP drawings", "Present", "IITK_Master_Tender_Document.pdf", "Yes", "Lifts and internal services specs"),
            ("Actual execution records", "Missing", "None", "No", "Post-handover records not public")
        ],
        "missing_critical": "Full structural reinforcement drawing pack",
        "newly_downloaded": "0 (Existing verified pack)",
        "confidence": "High",
        "next_action": "Use for institutional apartment block parametric estimation"
    },
    "EPI-Trimbakeshwar-EMRS": {
        "project_name": "Construction of Eklavya Model Residential School (EMRS) at Trimbakeshwar, Nashik",
        "tender_reference": "EPI/WRO/EMRS-TRIMBAK/2021/08",
        "authority": "Engineering Projects (India) Limited (EPI) / NESTS",
        "official_status": "Official (engineeringprojects.com / cppp)",
        "date": "2021-2023",
        "classification": "Silver",
        "classification_desc": "Useful institutional educational residential package (Hostel & quarters layouts, BOQ)",
        "selected_scope": {
            "building_name": "Boys' Hostel & Staff Quarters Block",
            "floors": "G+2 Floors",
            "drawing_ref": "Hostel & quarters architectural layouts in tender volume",
            "boq_ref": "Schedule of Quantities (Civil & Electrification)",
            "reason_selected": "Representative multi-unit residential accommodation within educational campus."
        },
        "sources": [
            ("EPI Official Portal", "https://www.engineeringprojects.com"),
            ("CPPP Portal", "https://eprocure.gov.in")
        ],
        "audit_table": [
            ("Tender/NIT", "Present", "Volume_I_NIT_Conditions.pdf", "Yes", "Official central PSU NIT"),
            ("Project scope", "Present", "Volume_I_NIT_Conditions.pdf", "Yes", "Residential school campus scope"),
            ("Architectural drawings", "Present", "Campus_Architectural_Layouts.pdf", "Yes", "Hostel and staff quarters plans"),
            ("Structural drawings", "Partial", "Technical_Specifications_Civil.pdf", "Yes", "RCC design parameters"),
            ("Civil specifications", "Present", "Technical_Specifications_Civil.pdf", "Yes", "Comprehensive civil specs"),
            ("BOQ with quantities", "Present", "Schedule_of_Quantities_BOQ.pdf", "Yes", "Itemized trade BOQ present"),
            ("Cost/rates", "Present", "Schedule_of_Quantities_BOQ.pdf", "Yes", "Sanctioned unit rates and totals"),
            ("Time schedule", "Present", "Volume_I_NIT_Conditions.pdf", "Yes", "18-month construction period"),
            ("Soil/geotechnical report", "Missing", "None", "No", "Site borehole data not public"),
            ("MEP drawings", "Present", "Electrical_PHE_Specs.pdf", "Yes", "Internal services specifications"),
            ("Actual execution records", "Missing", "None", "No", "Handover records not public")
        ],
        "missing_critical": "Detailed structural working drawings (post-award deliverable)",
        "newly_downloaded": "0 (Existing verified pack)",
        "confidence": "High",
        "next_action": "Model institutional hostel and staff quarter metrics"
    },
    "EPI-Dhenkanal-ICDS-Staff-Quarters": {
        "project_name": "Construction of Staff Quarters for ICDS Project at Dhenkanal, Odisha",
        "tender_reference": "EPI/ERO/DHENKANAL-ICDS/2022/12",
        "authority": "Engineering Projects (India) Limited (EPI) / WCD Odisha",
        "official_status": "Official (engineeringprojects.com / cppp)",
        "date": "2022-2024",
        "classification": "Silver",
        "classification_desc": "Useful institutional staff housing package (Complete architectural drawings, BOQ & specs)",
        "selected_scope": {
            "building_name": "E-Type Staff Quarters Building",
            "floors": "Stilt + 4 Floors",
            "drawing_ref": "Complete architectural plan, elevation, section drawings",
            "boq_ref": "Itemized Schedule of Quantities and rate analysis",
            "reason_selected": "Standalone institutional housing unit with complete architectural elevations and BOQ."
        },
        "sources": [
            ("EPI Official Portal", "https://www.engineeringprojects.com")
        ],
        "audit_table": [
            ("Tender/NIT", "Present", "EPI_Dhenkanal_NIT_Notice.pdf", "Yes", "Official tender document"),
            ("Project scope", "Present", "Technical_Bid_Volume_I.pdf", "Yes", "E-Type staff quarter scope"),
            ("Architectural drawings", "Present", "E_Type_Architectural_Drawings.pdf", "Yes", "Full plans, elevations, sections"),
            ("Structural drawings", "Partial", "Structural_Design_Brief.pdf", "Yes", "RCC framed design parameters"),
            ("Civil specifications", "Present", "Technical_Specifications.pdf", "Yes", "State & central PWD specs"),
            ("BOQ with quantities", "Present", "Itemized_BOQ_Schedule.pdf", "Yes", "Trade BOQ with quantities"),
            ("Cost/rates", "Present", "Itemized_BOQ_Schedule.pdf", "Yes", "Estimated cost and item rates"),
            ("Time schedule", "Present", "Technical_Bid_Volume_I.pdf", "Yes", "12-month completion period"),
            ("Soil/geotechnical report", "Missing", "None", "No", "Geotechnical investigation not public"),
            ("MEP drawings", "Present", "PHE_Electrical_Specifications.pdf", "Yes", "Internal building services"),
            ("Actual execution records", "Missing", "None", "No", "Execution status in progress")
        ],
        "missing_critical": "Structural bar bending schedule",
        "newly_downloaded": "0 (Existing verified pack)",
        "confidence": "High",
        "next_action": "Execute quantity takeoff validation on Stilt+4 frame"
    },
    "WB-PWD-Burdwan-Type-I-II-Quarters": {
        "project_name": "Construction of Proposed Residential Type-I & Type-II Quarters at Burdwan Division Campus",
        "tender_reference": "BOQ_1634922 / WB PWD Social Sector Burdwan",
        "authority": "Public Works Department (PWD), Government of West Bengal",
        "official_status": "Official (wbtenders.gov.in / pwd.wb.gov.in)",
        "date": "2024-2025",
        "classification": "Silver",
        "classification_desc": "Useful state PWD housing dataset (Official WBF-2911 contract form, itemized BOQ schedule & SOR)",
        "selected_scope": {
            "building_name": "Type-II Quarters Block (2BHK Block)",
            "floors": "G+2 Floors (8 Units)",
            "drawing_ref": "Architectural floor plates and building sections",
            "boq_ref": "Itemized WB PWD BOQ spreadsheet (BOQ_1634922)",
            "reason_selected": "Primary state PWD staff quarters block with Schedule A item rates & WBF-2911 contract."
        },
        "sources": [
            ("WB eTender Portal", "https://wbtenders.gov.in"),
            ("WB PWD Portal", "https://pwd.wb.gov.in")
        ],
        "audit_table": [
            ("Tender/NIT", "Present", "eNIT_WB_PWD_Burdwan.pdf", "Yes", "Official state PWD e-NIT"),
            ("Project scope", "Present", "WBF_2911_Contract_Conditions.pdf", "Yes", "Type-I and II quarters scope"),
            ("Architectural drawings", "Present", "Type_II_Architectural_Drawings.pdf", "Yes", "Floor plans, elevations"),
            ("Structural drawings", "Partial", "Structural_Design_Standards.md", "Yes", "WB PWD standard details"),
            ("Civil specifications", "Present", "WB_PWD_Schedule_of_Rates_Civil.pdf", "Yes", "Official WB PWD SOR"),
            ("BOQ with quantities", "Present", "BOQ_1634922.csv", "Yes", "Itemized Schedule A BOQ"),
            ("Cost/rates", "Present", "BOQ_1634922.csv", "Yes", "Official PWD item unit rates"),
            ("Time schedule", "Present", "eNIT_WB_PWD_Burdwan.pdf", "Yes", "9-month completion schedule"),
            ("Soil/geotechnical report", "Missing", "None", "No", "Geotechnical data missing"),
            ("MEP drawings", "Present", "Electrical_PHE_Provisions.md", "Yes", "Internal electrification and PHE"),
            ("Actual execution records", "Missing", "None", "No", "Construction under execution")
        ],
        "missing_critical": "GFC structural reinforcement drawings",
        "newly_downloaded": "0 (Existing verified pack)",
        "confidence": "High",
        "next_action": "Calibrate state PWD Schedule of Rates (SOR) pricing"
    },
    "KMRL-Kochi-Metro-Muttom-Quarters": {
        "project_name": "Multi-Storey Residential Staff Quarters at Muttom Depot (Phase-I)",
        "tender_reference": "KMRL/PRJ/STAFF QTRS @ MUTTOM-162/2014/TEN 03-15",
        "authority": "Kochi Metro Rail Limited (KMRL)",
        "official_status": "Official (kochimetro.org)",
        "date": "2015-03-15",
        "classification": "Silver",
        "classification_desc": "Useful metro housing package (313-page bid volume, specifications, architectural layouts)",
        "selected_scope": {
            "building_name": "Type-III Multi-Storey Staff Quarters Tower",
            "floors": "G+8 Floors",
            "drawing_ref": "Architectural floor layouts in 313-page technical bid volume",
            "boq_ref": "Turnkey cost and Schedule of Quantities in bid pack",
            "reason_selected": "High-density metro rail operational housing block with complete technical specifications."
        },
        "sources": [
            ("Kochi Metro Portal", "https://kochimetro.org")
        ],
        "audit_table": [
            ("Tender/NIT", "Present", "KMRL_Staff_Quarters_Master_Tender.pdf (6.47 MB)", "Yes", "Official master tender document"),
            ("Project scope", "Present", "KMRL_Staff_Quarters_Master_Tender.pdf", "Yes", "Type-II/III/IV multi-storey towers"),
            ("Architectural drawings", "Present", "KMRL_Staff_Quarters_Master_Tender.pdf", "Yes", "Architectural layouts in bid volume"),
            ("Structural drawings", "Partial", "KMRL_Staff_Quarters_Master_Tender.pdf", "Yes", "Design basis criteria given"),
            ("Civil specifications", "Present", "KMRL_Staff_Quarters_Master_Tender.pdf", "Yes", "High-standard metro civil specs"),
            ("BOQ with quantities", "Present", "KMRL_Staff_Quarters_Master_Tender.pdf", "Yes", "Schedule of Quantities in tender"),
            ("Cost/rates", "Present", "KMRL_Staff_Quarters_Master_Tender.pdf", "Yes", "Estimated cost and item schedule"),
            ("Time schedule", "Present", "KMRL_Staff_Quarters_Master_Tender.pdf", "Yes", "18-month construction period"),
            ("Soil/geotechnical report", "Missing", "None", "No", "Site borehole report not public"),
            ("MEP drawings", "Present", "KMRL_Staff_Quarters_Master_Tender.pdf", "Yes", "Lifts, firefighting, electrical"),
            ("Actual execution records", "Missing", "None", "No", "Post-handover records not public")
        ],
        "missing_critical": "Standalone structural drawing sheets",
        "newly_downloaded": "0 (Existing verified pack)",
        "confidence": "High",
        "next_action": "Evaluate metro housing parametric cost and duration"
    },
    "DFCCIL-Jaipur-Staff-Quarters": {
        "project_name": "Construction of Type-3 Staff Quarters at 7 DFC Stations & FLN Building Extension",
        "tender_reference": "JP-EN-Quarter-2024-11 / JP-EN-Quarter-2023-18",
        "authority": "Dedicated Freight Corridor Corporation of India Limited (DFCCIL)",
        "official_status": "Official (ireps.gov.in / dfccil.com)",
        "date": "2024-07-12",
        "classification": "Silver",
        "classification_desc": "Useful railway housing package (Master PDFs present; structural proof-checking terms)",
        "selected_scope": {
            "building_name": "Standard Type-3 Staff Quarters Block (Phulera)",
            "floors": "G+1 / G+2 Floors",
            "drawing_ref": "Type-3 standard architectural plan and elevations",
            "boq_ref": "IREPS Schedule of Quantities and rate analysis",
            "reason_selected": "Typical DFC operational staff quarter module repeated across railway stations."
        },
        "sources": [
            ("IREPS Portal", "https://www.ireps.gov.in"),
            ("DFCCIL Portal", "https://dfccil.com")
        ],
        "audit_table": [
            ("Tender/NIT", "Present", "DFCCIL_Jaipur_Master_Tender_July2024.pdf", "Yes", "Official railway PSU tender"),
            ("Project scope", "Present", "DFCCIL_Jaipur_Master_Tender_July2024.pdf", "Yes", "Type-3 quarters across 7 stations"),
            ("Architectural drawings", "Present", "DFCCIL_Jaipur_Master_Tender_July2024.pdf", "Yes", "Type-3 architectural sheets"),
            ("Structural drawings", "Partial", "DFCCIL_Jaipur_Master_Tender_July2024.pdf", "Yes", "Proof checking requirement & specs"),
            ("Civil specifications", "Present", "DFCCIL_Jaipur_Master_Tender_July2024.pdf", "Yes", "Indian Railways standard specs"),
            ("BOQ with quantities", "Present", "IREPS_Schedule_of_Quantities.pdf", "Yes", "Itemized trade BOQ in bid volume"),
            ("Cost/rates", "Present", "IREPS_Schedule_of_Quantities.pdf", "Yes", "Estimated cost & item schedule"),
            ("Time schedule", "Present", "DFCCIL_Jaipur_Master_Tender_July2024.pdf", "Yes", "12-month completion period"),
            ("Soil/geotechnical report", "Missing", "None", "No", "Geotechnical data missing"),
            ("MEP drawings", "Present", "DFCCIL_Jaipur_Master_Tender_July2024.pdf", "Yes", "Internal electrification & water"),
            ("Actual execution records", "Missing", "None", "No", "Construction ongoing")
        ],
        "missing_critical": "Detailed structural reinforcement drawings",
        "newly_downloaded": "0 (Existing verified pack)",
        "confidence": "High",
        "next_action": "Benchmark railway operational staff quarter cost models"
    },
    "K-RIDE-Belandur-Road-Quarters": {
        "project_name": "Belandur Road Station Building & Hosur Doubling Railway Staff Quarters",
        "tender_reference": "K-RIDE/BSRP/QUARTERS/2023-24/07",
        "authority": "Rail Infrastructure Development Company (Karnataka) Limited (K-RIDE)",
        "official_status": "Official (kride.in / eproc.karnataka.gov.in)",
        "date": "2023-08-15",
        "classification": "Silver",
        "classification_desc": "Useful railway residential package (313-page bid volume, architectural plans, itemized BOQ)",
        "selected_scope": {
            "building_name": "Type-III Railway Staff Quarters Block",
            "floors": "G+1 Floors (8 Units)",
            "drawing_ref": "Architectural floor plans and site sections in 313-page bid volume",
            "boq_ref": "Itemized BOQ schedule for residential staff quarters",
            "reason_selected": "Railway suburban housing unit matching Belandur Road station infrastructure."
        },
        "sources": [
            ("K-RIDE Official Portal", "https://kride.in"),
            ("Karnataka e-Procurement", "https://eproc.karnataka.gov.in")
        ],
        "audit_table": [
            ("Tender/NIT", "Present", "K_RIDE_Belandur_Master_Tender.pdf (313 pages)", "Yes", "Official suburban rail tender"),
            ("Project scope", "Present", "K_RIDE_Belandur_Master_Tender.pdf", "Yes", "Staff quarters Type-II/III (16 units)"),
            ("Architectural drawings", "Present", "K_RIDE_Belandur_Master_Tender.pdf", "Yes", "Architectural floor plans in volume"),
            ("Structural drawings", "Partial", "K_RIDE_Belandur_Master_Tender.pdf", "Yes", "Structural design provisions"),
            ("Civil specifications", "Present", "K_RIDE_Belandur_Master_Tender.pdf", "Yes", "Railway civil specifications"),
            ("BOQ with quantities", "Present", "K_RIDE_Belandur_Master_Tender.pdf", "Yes", "Itemized trade BOQ in volume"),
            ("Cost/rates", "Present", "K_RIDE_Belandur_Master_Tender.pdf", "Yes", "Estimated cost & rates schedule"),
            ("Time schedule", "Present", "K_RIDE_Belandur_Master_Tender.pdf", "Yes", "15-month completion period"),
            ("Soil/geotechnical report", "Missing", "None", "No", "Geotechnical data missing"),
            ("MEP drawings", "Present", "K_RIDE_Belandur_Master_Tender.pdf", "Yes", "Electrical and plumbing provisions"),
            ("Actual execution records", "Missing", "None", "No", "Construction underway")
        ],
        "missing_critical": "Detailed structural reinforcement drawings",
        "newly_downloaded": "0 (Existing verified pack)",
        "confidence": "High",
        "next_action": "Incorporate railway suburban housing takeoff rates"
    },
    "CPWD-RBI-Kharghar-354-Quarters": {
        "project_name": "Construction of 354 Nos. Staff Quarters, Hostel Building & Academic Block for RBI",
        "tender_reference": "01/NIT/CE CUM ED/ EE & SM-I/2024-25",
        "authority": "Reserve Bank of India (RBI) / CPWD",
        "official_status": "Official (cpwd.gov.in / rbi.org.in)",
        "date": "2024-09-30",
        "classification": "Silver",
        "classification_desc": "Useful multi-package institutional housing (Package-2 ₹46.25 Cr interior BOQ & drawing specs)",
        "selected_scope": {
            "building_name": "Tower 1 (RBI Staff Quarters High-Rise)",
            "floors": "G+11 Floors (44 Units/tower)",
            "drawing_ref": "Tower architectural floor plates and site layout",
            "boq_ref": "Package-2 interior finishing and civil BOQ (₹46.25 Cr)",
            "reason_selected": "Representative residential tower among 9 high-rise blocks; Package-2 interior BOQ present."
        },
        "sources": [
            ("RBI Tender Window", "https://www.rbi.org.in"),
            ("CPWD eTender Portal", "https://etender.cpwd.gov.in")
        ],
        "audit_table": [
            ("Tender/NIT", "Present", "CPWD_RBI_Kharghar_NIT_Notice.pdf", "Yes", "Official government tender notice"),
            ("Project scope", "Present", "Project_Scope_Summary.md", "Yes", "354 quarters across 9 towers"),
            ("Architectural drawings", "Present", "Architectural_Site_and_Tower_Layouts.pdf", "Yes", "Tower floor plates and elevations"),
            ("Structural drawings", "Partial", "Structural_Framing_Criteria.md", "Yes", "Seismic Zone III RCC frame"),
            ("Civil specifications", "Present", "CPWD_Specifications_Civil_Finishes.pdf", "Yes", "CPWD 2019/2021 specifications"),
            ("BOQ with quantities", "Present", "Package_2_Interior_Civil_BOQ.pdf", "Yes", "Detailed ₹46.25 Cr BOQ"),
            ("Cost/rates", "Present", "Package_2_Interior_Civil_BOQ.pdf", "Yes", "Priced schedule of quantities"),
            ("Time schedule", "Present", "CPWD_RBI_Kharghar_NIT_Notice.pdf", "Yes", "Contract duration specified"),
            ("Soil/geotechnical report", "Missing", "None", "No", "Site borehole data not public"),
            ("MEP drawings", "Present", "MEP_Services_Overview.md", "Yes", "Lifts, fire safety, PHE systems"),
            ("Actual execution records", "Missing", "None", "No", "Active construction phase")
        ],
        "missing_critical": "Structural framing drawing sheets",
        "newly_downloaded": "0 (Existing verified pack)",
        "confidence": "High",
        "next_action": "Model high-rise institutional finishes and interior rates"
    },
    "NBCC-GPRA-Sarojini-Nagar": {
        "project_name": "Redevelopment of GPRA Colony at Sarojini Nagar, New Delhi",
        "tender_reference": "Packages III, VI, V-A, V-B, V-C, IV-A, IV-C, VII-A/B",
        "authority": "NBCC (India) Limited / MoHUA",
        "official_status": "Official (nbccindia.in / cppp)",
        "date": "2020-2024",
        "classification": "Reference only",
        "classification_desc": "Useful mega-township context (10,190 units, multiple packages; drawings/BOQs restricted on e-Nivida)",
        "selected_scope": {
            "building_name": "Package VI - Type-V Quarters Towers",
            "floors": "2B+G+12 Floors (800 Units)",
            "drawing_ref": "Confidential / restricted to registered bidders on e-Nivida",
            "boq_ref": "Restricted to registered bidders on e-Nivida portal",
            "reason_selected": "Largest residential component (800 units) within GPRA mega-redevelopment."
        },
        "sources": [
            ("NBCC Portal", "https://www.nbccindia.in"),
            ("NBCC e-Nivida", "https://nbcc.enivida.com")
        ],
        "audit_table": [
            ("Tender/NIT", "Present", "Package_VI_Tender_Notice_Summary.md", "Yes", "Official NBCC package notices"),
            ("Project scope", "Present", "Mega_Redevelopment_Scope_Charter.md", "Yes", "Township scope (10,190 units)"),
            ("Architectural drawings", "Missing", "None", "No", "Restricted to bidders on e-Nivida"),
            ("Structural drawings", "Missing", "None", "No", "Restricted to bidders on e-Nivida"),
            ("Civil specifications", "Present", "NBCC_Standard_Civil_Specifications.md", "Yes", "MoHUA / NBCC standard specs"),
            ("BOQ with quantities", "Missing", "None", "No", "Restricted to bidders on e-Nivida"),
            ("Cost/rates", "Present", "Package_VI_Cost_Outlay.md", "Yes", "Package VI outlay (₹946.16 Cr)"),
            ("Time schedule", "Present", "Milestone_Delivery_Charter.md", "Yes", "Phased completion schedule"),
            ("Soil/geotechnical report", "Missing", "None", "No", "Site borehole data not public"),
            ("MEP drawings", "Missing", "None", "No", "Restricted to bidders on e-Nivida"),
            ("Actual execution records", "Present", "Package_VI_Execution_Status.md", "Yes", "Active construction progress")
        ],
        "missing_critical": "Architectural drawings, structural drawings, and itemized BOQ (restricted on e-Nivida portal)",
        "newly_downloaded": "0 (Portal authentication required)",
        "confidence": "Medium",
        "next_action": "Retain as multi-package township benchmarking reference"
    },
    "TCIL-NVS-JNV-Azamgarh-Quarters": {
        "project_name": "Conversion of SP Shed to Regular Staff Quarters at JNV Azamgarh (UP)",
        "tender_reference": "TCIL/C/PD(UP)/NVS/2026/08 (CPP: 2026_TCIL_277790_1)",
        "authority": "Navodaya Vidyalaya Samiti (NVS) / TCIL",
        "official_status": "Official (tcil.net.in / cppp)",
        "date": "2026-05-16",
        "classification": "Silver",
        "classification_desc": "Useful school staff housing package (Complete technical bid & 69-page BOQ with floor plans)",
        "selected_scope": {
            "building_name": "Type-II Staff Quarters Block",
            "floors": "G+1 Floors (8 Units)",
            "drawing_ref": "Architectural floor plans and elevations in Volume I",
            "boq_ref": "69-page itemized civil and finishing BOQ in Volume II",
            "reason_selected": "Complete 69-page civil/finishing BOQ, architectural floor plans & area statements."
        },
        "sources": [
            ("TCIL Official Tender Portal", "https://www.tcil.net.in"),
            ("CPPP Portal", "https://etenders.gov.in")
        ],
        "audit_table": [
            ("Tender/NIT", "Present", "Volume_I_Technical_Bid_26c1186.pdf", "Yes", "Complete master technical bid"),
            ("Project scope", "Present", "Volume_I_Technical_Bid_26c1186.pdf", "Yes", "Type-II block + Guest house"),
            ("Architectural drawings", "Present", "Volume_I_Technical_Bid_26c1186.pdf", "Yes", "Floor plans, elevations, sections"),
            ("Structural drawings", "Partial", "Volume_I_Technical_Bid_26c1186.pdf", "Yes", "Structural DBR and criteria"),
            ("Civil specifications", "Present", "Volume_I_Technical_Bid_26c1186.pdf", "Yes", "CPWD / TCIL specifications"),
            ("BOQ with quantities", "Present", "Volume_II_Financial_Bid_BOQ_26c1186_1.pdf (69 pages)", "Yes", "69-page itemized trade BOQ"),
            ("Cost/rates", "Present", "Volume_II_Financial_Bid_BOQ_26c1186_1.pdf", "Yes", "Estimated cost & unit item rates"),
            ("Time schedule", "Present", "Volume_I_Technical_Bid_26c1186.pdf", "Yes", "6-month completion schedule"),
            ("Soil/geotechnical report", "Missing", "None", "No", "Geotechnical data missing"),
            ("MEP drawings", "Present", "Volume_II_Financial_Bid_BOQ_26c1186_1.pdf", "Yes", "Electrical and plumbing BOQ"),
            ("Actual execution records", "Missing", "None", "No", "Tender stage completed")
        ],
        "missing_critical": "Structural working drawings (post-award contractor deliverable)",
        "newly_downloaded": "0 (Existing verified pack)",
        "confidence": "High",
        "next_action": "Deploy for low-rise residential school quarters estimation"
    },
    "DFCCIL-Sarmatanr-Larabad-Koderma-Quarters": {
        "project_name": "Construction of Railway Staff Quarters at Sarmatanr, Larabad & Koderma",
        "tender_reference": "KKK-EN-QTR-DHN-I-PH-I / KKK-EN-QTR-DHN-I-PH-I-R",
        "authority": "Dedicated Freight Corridor Corporation of India Limited (DFCCIL)",
        "official_status": "Official (dfccil.com / ireps.gov.in)",
        "date": "2022-2025",
        "classification": "Reference only",
        "classification_desc": "Useful railway housing package (197-page tender & 50-page IREPS BOQ; drawings restricted)",
        "selected_scope": {
            "building_name": "Type-II Staff Quarters Block (Koderma)",
            "floors": "G+2 Floors (6 Units)",
            "drawing_ref": "Available physically at DFCCIL Kolkata unit (Clause 1.6 restricted)",
            "boq_ref": "50-page IREPS Schedule of Quantities",
            "reason_selected": "Official 197-page tender & 50-page IREPS BOQ schedule for Koderma station staff quarters."
        },
        "sources": [
            ("DFCCIL Official Portal", "https://dfccil.com"),
            ("IREPS Portal", "https://www.ireps.gov.in")
        ],
        "audit_table": [
            ("Tender/NIT", "Present", "Tender_Document_Quarter_KQR_HZB_RJ3Y.pdf (197 pages)", "Yes", "Official master railway tender"),
            ("Project scope", "Present", "NIT_for_KKK_EN_QTR_DHN_I_PH_I_I4PB.pdf", "Yes", "Type-II/III/IV across stations"),
            ("Architectural drawings", "Missing", "None", "No", "Restricted to Kolkata office visit"),
            ("Structural drawings", "Missing", "None", "No", "Restricted to Kolkata office visit"),
            ("Civil specifications", "Present", "Tender_Document_Quarter_KQR_HZB_RJ3Y.pdf", "Yes", "DFCCIL / Railway civil specs"),
            ("BOQ with quantities", "Present", "IREPS_Schedule_of_Quantities_BOQ.pdf (50 pages)", "Yes", "50-page itemized trade BOQ"),
            ("Cost/rates", "Present", "IREPS_Schedule_of_Quantities_BOQ.pdf", "Yes", "Priced schedule of rates"),
            ("Time schedule", "Present", "Tender_Document_Quarter_KQR_HZB_RJ3Y.pdf", "Yes", "12-month completion term"),
            ("Soil/geotechnical report", "Missing", "None", "No", "Geotechnical data missing"),
            ("MEP drawings", "Present", "IREPS_Schedule_of_Quantities_BOQ.pdf", "Yes", "Electrification BOQ present"),
            ("Actual execution records", "Present", "Koderma_Balance_Work_Tender.pdf", "Yes", "Retendered balance work record")
        ],
        "missing_critical": "Architectural & structural drawings (restricted to physical inspection at DFCCIL Kolkata)",
        "newly_downloaded": "0 (Physical inspection restriction)",
        "confidence": "Medium",
        "next_action": "Use for railway staff housing trade rate validation"
    },
    "MHDC-PMAY-Khairi-Kamptee-Nagpur": {
        "project_name": "Construction of Affordable Housing Project of 1444 LIG Tenements Under PMAY(U) at Khairi, Kamptee, Nagpur",
        "tender_reference": "MHDC/Maha Housing/PMAY/Khairi-Kamptee/Package-1/2023 (Tender ID: 38842646)",
        "authority": "Maharashtra Housing Development Corporation Limited (MHDC)",
        "official_status": "Official (mahahousing.mahaonline.gov.in / mahatenders.gov.in)",
        "date": "2023-2024",
        "classification": "Silver",
        "classification_desc": "Useful high-rise affordable housing package (283-page tender, area statements & Schedule C specs)",
        "selected_scope": {
            "building_name": "Building B1 (LIG High-Rise Tower)",
            "floors": "G+14 Floors (240 Units)",
            "drawing_ref": "Typical floor plate, cluster layout, and building elevations in Volume I",
            "boq_ref": "Lump-sum turnkey milestone schedule and Schedule C specifications",
            "reason_selected": "283-page Volume I tender, Schedule C specs, area distribution & milestone billing."
        },
        "sources": [
            ("MHDC Official Portal", "https://mahahousing.mahaonline.gov.in"),
            ("Mahatenders Portal", "https://mahatenders.gov.in")
        ],
        "audit_table": [
            ("Tender/NIT", "Present", "VolumeIK-P1.pdf (283 pages)", "Yes", "Official master turnkey tender"),
            ("Project scope", "Present", "VolumeIK-P1.pdf", "Yes", "1444 LIG tenements across 6 towers"),
            ("Architectural drawings", "Present", "VolumeIK-P1.pdf", "Yes", "Cluster floor plans and elevations"),
            ("Structural drawings", "Partial", "VolumeIK-P1.pdf", "Yes", "Chapter 4 structural design criteria"),
            ("Civil specifications", "Present", "VolumeIK-P1.pdf", "Yes", "Schedule C technical specs"),
            ("BOQ with quantities", "Present", "VolumeIK-P1.pdf", "Yes", "Turnkey milestone payment schedule"),
            ("Cost/rates", "Present", "VolumeIK-P1.pdf", "Yes", "Approved project cost & BUA rate"),
            ("Time schedule", "Present", "VolumeIK-P1.pdf", "Yes", "24-month construction timeline"),
            ("Soil/geotechnical report", "Missing", "None", "No", "Geotechnical data missing"),
            ("MEP drawings", "Present", "VolumeIK-P1.pdf", "Yes", "Lifts, electrical, PHE specs"),
            ("Actual execution records", "Missing", "None", "No", "Active construction phase")
        ],
        "missing_critical": "Structural bar bending schedule (post-award design deliverable)",
        "newly_downloaded": "0 (Existing verified pack)",
        "confidence": "High",
        "next_action": "Benchmark high-rise affordable housing PMAY metrics"
    },
    "SBI-GIFT-City-Twin-Towers": {
        "project_name": "Composite Construction Works for Proposed Construction of Residential Twin Towers at Block No 41, GIFT City, Gandhinagar",
        "tender_reference": "SBI/GNR/26-27/02 (Revised Corrigendum); Original: SBI/GNR/25-26/03",
        "authority": "State Bank of India (SBI)",
        "official_status": "Official (sbi.bank.in / tenderwizard.com)",
        "date": "2025-2026",
        "classification": "Silver",
        "classification_desc": "High-rise luxury twin tower package (681-page Technical Bid, 162-page BOQ, diaphragm wall package)",
        "selected_scope": {
            "building_name": "Tower A (Block 41A Luxury High-Rise)",
            "floors": "3B+G+25 Floors",
            "drawing_ref": "Architectural repository drive (typical floor plans, basement layouts) + Diaphragm wall sheets",
            "boq_ref": "162-page revised price bid itemized BOQ",
            "reason_selected": "681-page Technical Bid, 162-page BOQ, diaphragm wall package & architectural drive."
        },
        "sources": [
            ("SBI Procurement News", "https://sbi.bank.in"),
            ("Architectural Repository Drive", "https://drive.google.com/drive/folders/1-dJkPVTwNNXJMZWjMMk6Wa3tmlQ9wzCH?usp=sharing")
        ],
        "audit_table": [
            ("Tender/NIT", "Present", "SBI-GNR-26-27-02_Technical_Bid.pdf (681 pages)", "Yes", "Master 681-page technical bid"),
            ("Project scope", "Present", "SBI-GNR-26-27-02_Technical_Bid.pdf", "Yes", "Twin towers 3B+G+25/26 floors"),
            ("Architectural drawings", "Present", "Architectural_Drive_Repository.md", "Yes", "Google Drive architectural sheets"),
            ("Structural drawings", "Partial", "Diaphragm_Wall_Structural_Drawings.pdf", "Yes", "Diaphragm wall & raft details"),
            ("Civil specifications", "Present", "SBI-GNR-26-27-02_Technical_Bid.pdf", "Yes", "Luxury high-rise finishing specs"),
            ("BOQ with quantities", "Present", "Revised_Price_Bid_BOQ.pdf (162 pages)", "Yes", "162-page comprehensive BOQ"),
            ("Cost/rates", "Present", "Revised_Price_Bid_BOQ.pdf", "Yes", "Itemized trade rates and schedules"),
            ("Time schedule", "Present", "SBI-GNR-26-27-02_Technical_Bid.pdf", "Yes", "30-month milestone schedule"),
            ("Soil/geotechnical report", "Missing", "None", "No", "Report provided directly to contractor per Pre-Bid Item 58"),
            ("MEP drawings", "Present", "MEP_Building_Services_Specifications.pdf", "Yes", "Lifts, HVAC, substation, fire"),
            ("Actual execution records", "Missing", "None", "No", "Tender award stage")
        ],
        "missing_critical": "GFC superstructure structural drawing pack (diaphragm wall drawings present)",
        "newly_downloaded": "0 (Existing verified pack)",
        "confidence": "High",
        "next_action": "Execute deep basement and luxury skyscraper estimation"
    },
    "Paras-Dews-Sector-106-Gurugram": {
        "project_name": "Paras Dews Group Housing Scheme (6 High-Rise Towers), Sector 106, Dwarka Expressway, Gurugram",
        "tender_reference": "HARERA Reg. No. 118 OF 2017 / RERA-GRG-439-2019 (Project ID: 1043)",
        "authority": "Haryana Real Estate Regulatory Authority (HARERA) / Paras Buildtech",
        "official_status": "Official (haryanarera.gov.in / parasbuildtech.com)",
        "date": "2017-2023",
        "classification": "Reference only",
        "classification_desc": "Useful private high-rise benchmark (RERA Form A-H filing, 812 Cr outlay, master brochure & floor plans)",
        "selected_scope": {
            "building_name": "Tower A (Single Residential High-Rise)",
            "floors": "2B+G+23 Floors (120 Units)",
            "drawing_ref": "Approved DTCP layout, typical floor plans in master brochure",
            "boq_ref": "Private developer project; Form A-H certified construction cost (₹272.56 Cr)",
            "reason_selected": "RERA Form A-H filing, master brochure, approved layout & 272.56 Cr construction outlay."
        },
        "sources": [
            ("Haryana RERA Project Preview", "https://haryanarera.gov.in/view_project/project_preview_open/1043"),
            ("Paras Dews Master Brochure", "https://www.propertyxpo.com/paras-dews/assets/download/brochure.pdf")
        ],
        "audit_table": [
            ("Tender/NIT", "Missing", "None", "No", "Private residential project - governed by RERA registration"),
            ("Project scope", "Present", "Project_Identity_Verification.md", "Yes", "724 units across 6 towers"),
            ("Architectural drawings", "Present", "Paras_Dews_Master_Brochure.pdf", "Yes", "Unit layouts, cluster plans"),
            ("Structural drawings", "Missing", "None", "No", "RCC framed Zone IV specs; drawings confidential"),
            ("Civil specifications", "Present", "Civil_Specifications_and_Finishes.md", "Yes", "Promoter declared specifications"),
            ("BOQ with quantities", "Missing", "None", "No", "Private project without public itemized contractor BOQ"),
            ("Cost/rates", "Present", "RERA_Form_A_H_Financials.pdf", "Yes", "CA certified ₹272.56 Cr construction cost"),
            ("Time schedule", "Present", "Occupancy_Certificate_August2023.pdf", "Yes", "Completed project with OC issued 04-08-2023"),
            ("Soil/geotechnical report", "Missing", "None", "No", "Geotechnical data missing"),
            ("MEP drawings", "Present", "MEP_Services_and_Amenities.md", "Yes", "Clubhouse, lifts, backup power"),
            ("Actual execution records", "Present", "Occupancy_Certificate_August2023.pdf", "Yes", "Official OC issued August 2023")
        ],
        "missing_critical": "Itemized contractor tender BOQ and structural working drawings (private developer confidential)",
        "newly_downloaded": "0 (Private filing boundary)",
        "confidence": "Medium",
        "next_action": "Benchmark private high-rise NCR developer cost ratios"
    },
    "Haryana-RERA-Multi-Tower-Residential-Projects": {
        "project_name": "Various RERA-Registered Multi-Tower Residential Projects (Haryana RERA Benchmark Examples)",
        "tender_reference": "Multiple (HARERA Gurugram / Panchkula Form REP-I & Form A-H Filings)",
        "authority": "Haryana Real Estate Regulatory Authority (HARERA)",
        "official_status": "Official (haryanarera.gov.in)",
        "date": "2017-2025",
        "classification": "Reference only",
        "classification_desc": "Multi-project private high-rise benchmark (5 official Form A-H filings, cross-project cost takeoff matrix)",
        "selected_scope": {
            "building_name": "Ramprastha Edge Tower A (Benchmark High-Rise)",
            "floors": "2B+G+19 Floors",
            "drawing_ref": "Approved master zoning, cluster floor plates in Form A-H",
            "boq_ref": "Form A-H statutory audited expenditure schedules",
            "reason_selected": "Official HARERA Form A-H statutory filing with approved carpet areas & cost schedules."
        },
        "sources": [
            ("HARERA Registered Projects Portal", "https://haryanarera.gov.in")
        ],
        "audit_table": [
            ("Tender/NIT", "Missing", "None", "No", "Private residential projects - governed by RERA filings"),
            ("Project scope", "Present", "HARERA_Project_Summaries.md", "Yes", "Scope defined across 5 benchmark projects"),
            ("Architectural drawings", "Present", "Typical_Floor_Plates_Brochures.md", "Yes", "Layout plans and unit configurations"),
            ("Structural drawings", "Missing", "None", "No", "Working drawings confidential"),
            ("Civil specifications", "Present", "Civil_Specifications_Benchmarks.md", "Yes", "Promoter declared specifications"),
            ("BOQ with quantities", "Missing", "None", "No", "Private real estate without public contractor BOQs"),
            ("Cost/rates", "Present", "Form_A_H_Cost_Statements.md", "Yes", "Audited construction expenditures"),
            ("Time schedule", "Present", "Form_A_H_Cost_Statements.md", "Yes", "Quarterly milestone schedules"),
            ("Soil/geotechnical report", "Missing", "None", "No", "Geotechnical data missing"),
            ("MEP drawings", "Present", "MEP_Services_Benchmarks.md", "Yes", "NBC 2016 Part 4 services framework"),
            ("Actual execution records", "Present", "Quarterly_Progress_Reports_QPR.md", "Yes", "QPR filings and completion status")
        ],
        "missing_critical": "Contractor itemized tender BOQ and GFC structural drawings",
        "newly_downloaded": "0 (Private filing boundary)",
        "confidence": "Medium",
        "next_action": "Cross-validate high-rise cost per sq.ft. benchmarks across NCR"
    },
    "WB-RERA-Multi-Tower-Residential-Projects": {
        "project_name": "WB RERA Multi-Tower Residential Projects (TKD Series and Other Private Developer Projects)",
        "tender_reference": "Multiple (WBRERA / HIRA ProCode & Registration Numbers)",
        "authority": "West Bengal Real Estate Regulatory Authority (WBRERA / HIRA)",
        "official_status": "Official (rera.wb.gov.in)",
        "date": "2019-2025",
        "classification": "Reference only",
        "classification_desc": "Useful private multi-tower benchmark (Sanctioned plans, typical floor plates, TKD structural series)",
        "selected_scope": {
            "building_name": "Tarang Tower 6 (Sanctioned High-Rise Tower)",
            "floors": "G+10 Floors",
            "drawing_ref": "Sanctioned building plans, floor plates, elevation sheets & TKD structural series",
            "boq_ref": "Promoter audited financial declarations",
            "reason_selected": "Sanctioned municipal building plan, floor plates, elevation sheets & structural series."
        },
        "sources": [
            ("WBRERA Official Portal", "https://rera.wb.gov.in")
        ],
        "audit_table": [
            ("Tender/NIT", "Missing", "None", "No", "Private residential projects - no public tender via WBRERA"),
            ("Project scope", "Present", "WBRERA_Project_Summaries.md", "Yes", "1-7 towers per project scope"),
            ("Architectural drawings", "Present", "Sanctioned_Building_Plans.md", "Yes", "Sanctioned floor and elevation plans"),
            ("Structural drawings", "Partial", "TKD_Structural_Series.md", "Yes", "Foundation & column drawings for JKN/TKD"),
            ("Civil specifications", "Partial", "Promoter_Specifications.md", "Yes", "Pile foundation parameters in filings"),
            ("BOQ with quantities", "Missing", "None", "No", "Private projects without contractor BOQ"),
            ("Cost/rates", "Partial", "Audited_Financial_Declarations.md", "Yes", "Declared project costs in audited filings"),
            ("Time schedule", "Partial", "Statutory_Completion_Dates.md", "Yes", "Completion targets declared in filings"),
            ("Soil/geotechnical report", "Missing", "None", "No", "Geotechnical data missing"),
            ("MEP drawings", "Present", "Services_and_Sanitary_Notes.md", "Yes", "Sanctioned services outline"),
            ("Actual execution records", "Partial", "Handover_Milestones_Log.md", "Yes", "WBRERA registration & CC milestones")
        ],
        "missing_critical": "Public contractor itemized BOQ with unit rates",
        "newly_downloaded": "0 (Private filing boundary)",
        "confidence": "Medium",
        "next_action": "Validate eastern India mid-rise residential floor plate takeoff"
    },
    "UP-RERA-Residential-Towers-Floor-Plans": {
        "project_name": "UP RERA Residential Towers (Floor Plans of All Types), Private Developers, Uttar Pradesh",
        "tender_reference": "Multiple (UP RERA Project IDs: 8898, 8888, 9315, etc.)",
        "authority": "Uttar Pradesh Real Estate Regulatory Authority (UP RERA)",
        "official_status": "Official (up-rera.in)",
        "date": "2017-2025",
        "classification": "Reference only",
        "classification_desc": "Useful private high-rise benchmark (Floor Plans of All Types, typical 1-8/1-17/1-27 floor sequences)",
        "selected_scope": {
            "building_name": "Himalaya Pride Tower D (Approved Tower)",
            "floors": "G+17 Floors",
            "drawing_ref": "Approved Floor Plans of All Types, typical 1-17 floor plates",
            "boq_ref": "Form REG-3 CA certified project cost",
            "reason_selected": "Approved statutory Floor Plans of All Types, typical floor plates & promoter specs."
        },
        "sources": [
            ("UP RERA Official Portal", "https://up-rera.in")
        ],
        "audit_table": [
            ("Tender/NIT", "Missing", "None", "No", "Private residential projects - no public tender via UP RERA"),
            ("Project scope", "Present", "UP_RERA_Project_Summaries.md", "Yes", "Multi-tower schemes G+4 to G+27"),
            ("Architectural drawings", "Present", "Floor_Plans_of_All_Types.md", "Yes", "Typical floor plates (1-8, 1-17, 1-27)"),
            ("Structural drawings", "Missing", "None", "No", "Structural drawings not public on portal"),
            ("Civil specifications", "Present", "Promoter_Material_Specifications.md", "Yes", "Material specs on promoter letterhead"),
            ("BOQ with quantities", "Missing", "None", "No", "Private projects without contractor BOQ"),
            ("Cost/rates", "Partial", "Form_REG_3_CA_Certificates.md", "Yes", "CA certified project costs"),
            ("Time schedule", "Partial", "Proposed_Completion_Dates.md", "Yes", "Target completion dates declared"),
            ("Soil/geotechnical report", "Missing", "None", "No", "Geotechnical data missing"),
            ("MEP drawings", "Present", "Building_Services_Specifications.md", "Yes", "Lifts, firefighting, electrical specs"),
            ("Actual execution records", "Partial", "Registration_and_QPR_Log.md", "Yes", "QPR tracking & authority OC milestones")
        ],
        "missing_critical": "Contractor tender BOQ and structural reinforcement drawings",
        "newly_downloaded": "0 (Private filing boundary)",
        "confidence": "Medium",
        "next_action": "Use for high-rise unit configuration and spatial modeling"
    },
    "Purvanchal-Sunbliss-Sector-22D-Yamuna-Expressway": {
        "project_name": "Purvanchal Sunbliss (7 Residential Blocks + Community Center), Sector 22D, Yamuna Expressway, UP",
        "tender_reference": "UPRERAPRJ746863/04/2025 (Project ID: PRJ746863)",
        "authority": "UP RERA / YEIDA / Purvanchal Projects Pvt. Ltd.",
        "official_status": "Official (up-rera.in / yamunaexpresswayauthority.com)",
        "date": "2024-2030",
        "classification": "Reference only",
        "classification_desc": "Useful private high-rise benchmark (767.31 Cr CA certificate, MIVAN formwork & Schedule D specs)",
        "selected_scope": {
            "building_name": "Tower T1 (Residential High-Rise Block)",
            "floors": "2B+G+24 Floors (160 Units)",
            "drawing_ref": "Master layout, unit floor sequences (1-24), apartment type sheets",
            "boq_ref": "Statutory CA Certificate Form REG-3 (₹767.31 Cr total outlay)",
            "reason_selected": "RERA PRJ746863 registration, 767.31 Cr CA certificate, MIVAN shear wall specs."
        },
        "sources": [
            ("UP RERA Official Portal", "https://up-rera.in"),
            ("Official CA Statutory Certificate", "https://up-rera.in/ViewDocument?Param=PRJ461451357Sunbliss-20-03-2025_CA_Certificate_DS.pdf")
        ],
        "audit_table": [
            ("Tender/NIT", "Missing", "None", "No", "Private residential project - governed by YEIDA lease deed"),
            ("Project scope", "Present", "Project_Identity_Verification.md", "Yes", "1,112 units across 7 blocks + clubhouse"),
            ("Architectural drawings", "Present", "Master_Layout_and_Unit_Plans.pdf", "Yes", "Site master layout, floor sequences 1-24"),
            ("Structural drawings", "Missing", "None", "No", "Monolithic MIVAN shear wall specs; GFC confidential"),
            ("Civil specifications", "Present", "Schedule_D_Specifications.pdf", "Yes", "MIVAN shuttering, vitrified tiles, finishes"),
            ("BOQ with quantities", "Missing", "None", "No", "Private project without public contractor BOQ"),
            ("Cost/rates", "Present", "Sunbliss_CA_Certificate_DS.pdf", "Yes", "CA certified ₹767.31 Cr project cost"),
            ("Time schedule", "Present", "Agreement_for_Sale.pdf", "Yes", "Possession target date 29-01-2030"),
            ("Soil/geotechnical report", "Missing", "None", "No", "Geotechnical data missing"),
            ("MEP drawings", "Present", "MEP_Services_and_Clubhouse_Specs.md", "Yes", "70,000 sq.ft clubhouse MEP, lifts, STP"),
            ("Actual execution records", "Partial", "Construction_Absorption_Status.md", "Yes", "13.14% expenditure absorbed per CA cert")
        ],
        "missing_critical": "Public itemized contractor BOQ and structural calculations",
        "newly_downloaded": "0 (Private filing boundary)",
        "confidence": "Medium",
        "next_action": "Benchmark MIVAN high-rise construction speed and cost ratios"
    },
    "IIT-Hyderabad-Faculty-Housing": {
        "project_name": "Construction of Precast 2 Nos. Faculty Housing (G+12), 3 Nos. Staff Housing (G+12) and 3 Nos. Hostel Blocks (G+6) at IIT Hyderabad",
        "tender_reference": "NIT No. IITH/CMD/CIVIL/NIT/2022-23/09",
        "authority": "Indian Institute of Technology Hyderabad (IITH)",
        "official_status": "Official (iith.ac.in / eprocure.gov.in)",
        "date": "2022-2025",
        "classification": "Gold",
        "classification_desc": "Ready for end-to-end prototype (Full 6-volume EPC tender pack, concept drawings, subsoil report & BOQ)",
        "selected_scope": {
            "building_name": "Faculty Housing Tower 1 (Precast High-Rise)",
            "floors": "G+12 Floors (48 Units)",
            "drawing_ref": "Volume 05 Concept Architectural & Precast Structural Drawings",
            "boq_ref": "Volume 02b Payment Schedule Annexure & Volume 03 Civil Specs",
            "reason_selected": "Complete 6-volume EPC pack, precast architectural plans, subsoil report & 254.65 Cr award."
        },
        "sources": [
            ("IIT Hyderabad Tenders Portal", "https://iith.ac.in/tenders/"),
            ("CPPP Portal", "https://eprocure.gov.in/eprocure/app")
        ],
        "audit_table": [
            ("Tender/NIT", "Present", "volume_01_notice_inviting_tender_special_conditions_of_contract.pdf", "Yes", "Official 6-volume EPC tender pack"),
            ("Project scope", "Present", "volume_01_notice_inviting_tender_special_conditions_of_contract.pdf", "Yes", "8 precast RCC buildings (5 towers G+12)"),
            ("Architectural drawings", "Present", "volume_05_concept_drawings_subsoil_report.pdf", "Yes", "Architectural floor plans & precast layouts"),
            ("Structural drawings", "Present", "volume_05_concept_drawings_subsoil_report.pdf", "Yes", "Precast structural connection details"),
            ("Civil specifications", "Present", "volume_03_technical_specs_civil_works.pdf", "Yes", "Comprehensive precast concrete specs"),
            ("BOQ with quantities", "Present", "volume_02_b_payment_schedule_annexure.pdf", "Yes", "Detailed EPC milestone BOQ schedule"),
            ("Cost/rates", "Present", "IITH 41st BoG Meeting Minutes-Revised.pdf", "Yes", "₹254.65 Cr contract award resolution"),
            ("Time schedule", "Present", "volume_06_general_conditions_epc.pdf", "Yes", "24-month contract schedule"),
            ("Soil/geotechnical report", "Present", "volume_05_concept_drawings_subsoil_report.pdf", "Yes", "Subsoil report with borehole data"),
            ("MEP drawings", "Present", "volume_04_scope_tech_specs_em_components.pdf", "Yes", "Comprehensive electrical & mechanical specs"),
            ("Actual execution records", "Present", "IITH 41st BoG Meeting Minutes-Revised.pdf", "Yes", "BoG contract award approval")
        ],
        "missing_critical": "None (Full 6-volume official EPC pack verified)",
        "newly_downloaded": "0 (Existing verified pack)",
        "confidence": "High",
        "next_action": "Model precast concrete high-rise execution speed and quantities"
    },
    "MHADA-Goregaon-LIG-MIG-HIG-Tenements": {
        "project_name": "Construction of LIG/MIG/HIG Residential Tenements at Siddharth Nagar, Goregaon, Mumbai",
        "tender_reference": "TN-EE-Goregaon-MB-30_8_2024-en / MHADA/EE/Goregaon/MB/2024",
        "authority": "Mumbai Housing and Area Development Board (MHADA)",
        "official_status": "Official (mhada.gov.in / mahatenders.gov.in)",
        "date": "2024-2028",
        "classification": "Silver",
        "classification_desc": "Useful turnkey high-rise package (Master NIT PDF TN-EE-Goregaon-MB-30_8_2024-en, plot area & cost)",
        "selected_scope": {
            "building_name": "Plot R1 LIG High-Rise Tower",
            "floors": "Stilt + 20 Floors",
            "drawing_ref": "Architectural massing in master NIT (drawings are post-award EPC deliverables)",
            "boq_ref": "Plot-wise built-up area schedules and turnkey price outlay",
            "reason_selected": "Official master NIT TN-EE-Goregaon-MB-30_8_2024-en, plot area schedules & turnkey scope."
        },
        "sources": [
            ("MHADA Official Portal", "https://mhada.gov.in"),
            ("Official Master E-Tender Notice PDF", "https://www.mhada.gov.in/sites/default/files/TN-EE-Goregaon-MB-30_8_2024-en.pdf")
        ],
        "audit_table": [
            ("Tender/NIT", "Present", "TN-EE-Goregaon-MB-30_8_2024-en.pdf", "Yes", "Official master e-tender notice PDF"),
            ("Project scope", "Present", "TN-EE-Goregaon-MB-30_8_2024-en.pdf", "Yes", "4 plots (3.055 million sq.ft BUA)"),
            ("Architectural drawings", "Missing", "None", "No", "Post-award EPC deliverable"),
            ("Structural drawings", "Missing", "None", "No", "Post-award EPC deliverable"),
            ("Civil specifications", "Present", "Turnkey_Engineering_Specifications.md", "Yes", "MHADA high-rise turnkey specifications"),
            ("BOQ with quantities", "Present", "Plot_Wise_Cost_and_Area_Schedule.md", "Yes", "Plot R1 BUA and turnkey milestone BOQ"),
            ("Cost/rates", "Present", "TN-EE-Goregaon-MB-30_8_2024-en.pdf", "Yes", "₹1,355.95 Cr total estimated outlay"),
            ("Time schedule", "Present", "TN-EE-Goregaon-MB-30_8_2024-en.pdf", "Yes", "48-month construction period"),
            ("Soil/geotechnical report", "Partial", "Site_Soil_Investigation_Brief.md", "Yes", "Turnkey scope mandates contractor soil tests"),
            ("MEP drawings", "Present", "MEP_Building_Services_Charter.md", "Yes", "High-speed lifts, firefighting, solar PHE"),
            ("Actual execution records", "Missing", "None", "No", "Active tendering and award phase")
        ],
        "missing_critical": "Working architectural & structural drawings (post-award EPC deliverables)",
        "newly_downloaded": "0 (Post-award deliverable boundary)",
        "confidence": "High",
        "next_action": "Calibrate Mumbai high-rise turnkey execution costs"
    },
    "CPWD-BSF-Roopnagar-63-Quarters": {
        "project_name": "Construction of 63 Nos. Residential Quarters at BSF Campus Roopnagar (Structural Design Consultancy)",
        "tender_reference": "NIT No. 28/EE/SILIGURI/CPWD/2025-26",
        "authority": "Central Public Works Department (CPWD), Siliguri Central Division / BSF",
        "official_status": "Official (cpwd.gov.in / eprocure.gov.in)",
        "date": "2025-2026",
        "classification": "Reference only",
        "classification_desc": "Useful design consultancy benchmark (46-page NIT, Schedule A BOQ, DBR criteria; drawings restricted)",
        "selected_scope": {
            "building_name": "Type-II Quarters Block (BSF Campus)",
            "floors": "Stilt + 8 Floors (48 Units)",
            "drawing_ref": "Clause 1.6 restricted; available departmentally to awarded consultant",
            "boq_ref": "Schedule A structural design consultancy BOQ",
            "reason_selected": "Primary housing tower under NIT 28/EE/SILIGURI/CPWD/2025-26; Schedule A BOQ & DBR."
        },
        "sources": [
            ("CPWD Official Portal", "https://cpwd.gov.in"),
            ("CPWD Plinth Area Rates", "https://www.cpwd.gov.in")
        ],
        "audit_table": [
            ("Tender/NIT", "Present", "NIT_Document_Analysis_and_Data_Extraction.md", "Yes", "NIT No. 28/EE/SILIGURI/CPWD/2025-26"),
            ("Project scope", "Present", "Project_Identity_and_Engineering_Scope.md", "Yes", "63 units: 48 Type-II (S+8) + 15 Type-III (S+5)"),
            ("Architectural drawings", "Missing", "None", "No", "Clause 1.6 restricted reference only"),
            ("Structural drawings", "Missing", "None", "No", "Deliverable to be created by consultant"),
            ("Civil specifications", "Present", "Design_Basis_Report_and_Technical_Criteria.md", "Yes", "CPWD specifications & Seismic Zone IV DBR"),
            ("BOQ with quantities", "Partial", "Schedule_A_BOQ_Consultancy_Fee_Schedule.md", "Yes", "Consultancy fee Schedule A BOQ"),
            ("Cost/rates", "Present", "Project_Cost_Estimating_and_PAR_Context.md", "Yes", "PAR cost benchmarks and consultancy outlay"),
            ("Time schedule", "Present", "Consultancy_Milestones_and_Timeline.md", "Yes", "3-month design submission term"),
            ("Soil/geotechnical report", "Missing", "None", "No", "Not included in public bid document"),
            ("MEP drawings", "Present", "MEP_Services_and_Building_Integration.md", "Yes", "Internal building services DBR"),
            ("Actual execution records", "Missing", "None", "No", "Design phase underway")
        ],
        "missing_critical": "Architectural drawings (restricted reference) & physical construction BOQ",
        "newly_downloaded": "0 (Consultancy package boundary)",
        "confidence": "Medium",
        "next_action": "Benchmark CPWD structural design requirements for Seismic Zone IV"
    },
    "CPWD-EPFO-Borivali-301-Quarters": {
        "project_name": "Redevelopment of EPFO Campus at Borivali, Mumbai (Planning, Designing & Construction of 301 Residential Quarters)",
        "tender_reference": "NIT No. 64/EE/Mumbai-IV/02/CE/Mumbai-II/2025-26",
        "authority": "Central Public Works Department (CPWD), Mumbai-IV Division / EPFO",
        "official_status": "Official (cpwd.gov.in / eprocure.gov.in)",
        "date": "2025-2028",
        "classification": "Reference only",
        "classification_desc": "Useful high-rise EPC benchmark (₹337.06 Cr outlay, 35-storey skyscraper + G+4 building, 32-month timeline)",
        "selected_scope": {
            "building_name": "Tower 1 (EPFO Residential Skyscraper)",
            "floors": "3B+GF+3P+35 Floors (301 Units)",
            "drawing_ref": "Concept architectural zoning defined; GFC drawings restricted to registered bidders",
            "boq_ref": "Turnkey milestone payment schedule and CPWD PAR high-rise benchmark",
            "reason_selected": "EPC Mode-I master package, ₹337.06 Cr outlay, 32-month timeline, diaphragm wall brief."
        },
        "sources": [
            ("CPWD Official Portal", "https://cpwd.gov.in"),
            ("CPWD Plinth Area Rates", "https://www.cpwd.gov.in")
        ],
        "audit_table": [
            ("Tender/NIT", "Present", "CPWD_EPC_Mode_I_Contract_Framework_and_Procurement_Charter.md", "Yes", "Official CPWD NIT reference 64/EE/Mumbai-IV/02"),
            ("Project scope", "Present", "Project_Executive_Summary_and_Data_Extraction.md", "Yes", "301 quarters in 35-storey tower + G+4 block"),
            ("Architectural drawings", "Missing", "None", "No", "Restricted to fee-paying registered bidders"),
            ("Structural drawings", "Missing", "None", "No", "Diaphragm wall & raft briefs present; GFC restricted"),
            ("Civil specifications", "Present", "CPWD_High_Rise_Civil_and_Finishing_Specifications.md", "Yes", "CPWD 2019/2021 specifications"),
            ("BOQ with quantities", "Partial", "Project_Financial_Outlay_and_High_Rise_Economics.md", "Yes", "Milestone EPC schedule & PAR schedule"),
            ("Cost/rates", "Present", "Project_Financial_Outlay_and_High_Rise_Economics.md", "Yes", "₹337.06 Cr verified administrative outlay"),
            ("Time schedule", "Present", "Project_Lifecycle_Milestones_and_32_Month_Timeline.md", "Yes", "32-calendar month lifecycle with 5 milestone gates"),
            ("Soil/geotechnical report", "Missing", "None", "No", "Contractor post-award confirmatory borehole scope"),
            ("MEP drawings", "Present", "MEP_Building_Services_High_Speed_Lifts_and_Fire_Safety.md", "Yes", "High-speed lifts, dual plumbing, fire safety"),
            ("Actual execution records", "Missing", "None", "No", "Under active 32-month execution")
        ],
        "missing_critical": "GFC architectural/structural drawings and itemized contractor trade rates (restricted to registered bidders)",
        "newly_downloaded": "0 (EPC tender restriction)",
        "confidence": "Medium",
        "next_action": "Use for Mumbai coastal skyscraper duration and diaphragm wall estimation"
    },
    "AIIMS-Delhi-150-Units-Staff-Quarters": {
        "project_name": "Construction of G+12 Staff Quarters (150 Units) at AIIMS Delhi [UNVERIFIED / REJECTED CANDIDATE]",
        "tender_reference": "Not Publicly Available (No Record Found)",
        "authority": "Central Public Works Department (CPWD) / AIIMS New Delhi",
        "official_status": "Reject / Unverified (No public tender documents found)",
        "date": "2026-09-16 (Search Date)",
        "classification": "Reject",
        "classification_desc": "No Public Documents Found: Exhaustive search across AIIMS tender portals, CPPP, and CPWD identified no public tender document, NIT, BOQ, or drawing set for 150-unit G+12 quarters at AIIMS Delhi.",
        "selected_scope": {
            "building_name": "Unverified Candidate (Hypothetical G+12 Tower)",
            "floors": "G+12 Floors (150 Units) - REJECT",
            "drawing_ref": "None (No public drawings found)",
            "boq_ref": "None (No public BOQ found)",
            "reason_selected": "Formally audited & rejected candidate; negative procurement audit & disambiguation charter."
        },
        "sources": [
            ("AIIMS Delhi Tender Portal", "https://www.aiims.edu/index.php/en/tenders"),
            ("CPPP Tender Portal", "https://eprocure.gov.in")
        ],
        "audit_table": [
            ("Tender/NIT", "Missing", "None", "No", "No public tender found across AIIMS or CPWD"),
            ("Project scope", "Missing", "None", "No", "Hypothetical candidate scope unverified"),
            ("Architectural drawings", "Missing", "None", "No", "No public architectural plans found"),
            ("Structural drawings", "Missing", "None", "No", "No public structural drawings found"),
            ("Civil specifications", "Present", "CPWD_Residential_Planning_and_Technical_Specifications_Overview.md", "No", "General CPWD specifications only; not project-specific"),
            ("BOQ with quantities", "Missing", "None", "No", "No public BOQ found"),
            ("Cost/rates", "Missing", "None", "No", "No public cost/rates found"),
            ("Time schedule", "Missing", "None", "No", "No public time schedule found"),
            ("Soil/geotechnical report", "Missing", "None", "No", "No geotechnical report found"),
            ("MEP drawings", "Missing", "None", "No", "No MEP service layouts found"),
            ("Actual execution records", "Missing", "None", "No", "No execution actuals found")
        ],
        "missing_critical": "All primary tender, drawing, BOQ, and schedule documents (Project unverified in public domain)",
        "newly_downloaded": "0 (No public record exists)",
        "confidence": "Zero (Rejected)",
        "next_action": "Do not use for training or estimation models; retain audit trail"
    }
}

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def execute_refinement():
    print("=" * 80)
    print("STARTING COMPREHENSIVE AUDIT & REFINEMENT ACROSS ALL 30 PROJECTS")
    print("=" * 80)

    # 1. Global hash scan to identify canonical copies and duplicates
    print("\nPhase 1: Scanning file checksums across all 30 projects...")
    hash_to_paths = defaultdict(list)
    for p_name in PROJECTS_DATA.keys():
        p_path = os.path.join(BASE_DIR, p_name)
        for root, dirs, files in os.walk(p_path):
            for f in sorted(files):
                if f in [".gitkeep", "file_manifest.csv", "README.md", "file_manifest.json"]:
                    continue
                fp = os.path.join(root, f)
                try:
                    h = compute_sha256(fp)
                    hash_to_paths[h].append(fp)
                except Exception as e:
                    print(f"Error reading {fp}: {e}")

    # Build canonical map: for identical files within or across folders, the one in a specific category (01-08) is canonical;
    # if both in category, earliest path is canonical.
    canonical_file_for_hash = {}
    for h, paths in hash_to_paths.items():
        if len(paths) == 1:
            canonical_file_for_hash[h] = paths[0]
        else:
            # Prefer 01-08 over 00 or 99
            preferred = sorted(paths, key=lambda p: (
                1 if any(d in p for d in ["01_", "02_", "03_", "04_", "05_", "06_", "07_", "08_"]) else 2,
                len(p),
                p
            ))
            canonical_file_for_hash[h] = preferred[0]

    print(f"Total unique file contents: {len(hash_to_paths)}")
    duplicate_groups = {h: p for h, p in hash_to_paths.items() if len(p) > 1}
    print(f"Duplicate content groups: {len(duplicate_groups)}")

    # 2. Process each project: build 14-column manifest & update README
    print("\nPhase 2: Updating 14-Column Manifests and Audited README.md files...")
    report_rows = []

    for p_name, p_data in PROJECTS_DATA.items():
        p_path = os.path.join(BASE_DIR, p_name)
        scope = p_data["selected_scope"]
        
        # Ensure canonical subdirs exist
        for d in STANDARD_DIRS:
            dp = os.path.join(p_path, d)
            os.makedirs(dp, exist_ok=True)
            keep = os.path.join(dp, ".gitkeep")
            if not os.path.exists(keep) and len(os.listdir(dp)) == 0:
                with open(keep, "w") as f:
                    pass

        # Build 14-column manifest
        manifest_rows = []
        for d in STANDARD_DIRS:
            sub_p = os.path.join(p_path, d)
            for root, dirs, files in os.walk(sub_p):
                for f in sorted(files):
                    if f in [".gitkeep", "file_manifest.csv", "README.md", "file_manifest.json"]:
                        continue
                    full_f = os.path.join(root, f)
                    rel_local = os.path.relpath(full_f, p_path).replace("\\", "/")
                    sz = os.path.getsize(full_f)
                    file_hash = compute_sha256(full_f)

                    # Determine canonical vs duplicate
                    canon_path = canonical_file_for_hash[file_hash]
                    is_duplicate = (canon_path != full_f)
                    duplicate_of = os.path.relpath(canon_path, BASE_DIR).replace("\\", "/") if is_duplicate else ""

                    # Determine dataset role
                    ext = os.path.splitext(f)[1].lower()
                    is_meta = ext in [".md", ".txt", ".ps1", ".py", ".html"] or "audit" in f.lower() or "report" in f.lower() or "charter" in f.lower()
                    
                    if p_data["classification"] == "Reject":
                        dataset_role = "Metadata" if is_meta else "Supporting"
                        same_proj_ver = "No"
                        notes = f"Size: {sz:,} bytes | metadata_only=true | Rejection audit reference"
                    elif is_duplicate:
                        dataset_role = "Supporting"
                        same_proj_ver = "Verified"
                        notes = f"Size: {sz:,} bytes | Duplicate copy retained for structure"
                    elif is_meta:
                        dataset_role = "Metadata"
                        same_proj_ver = "Verified" if d != "99_Unverified_or_Related_References" else "Uncertain"
                        notes = f"Size: {sz:,} bytes | metadata_only=true"
                    elif d in ["02_Cost_BOQ_Makes"]:
                        dataset_role = "Validation"
                        same_proj_ver = "Verified"
                        notes = f"Size: {sz:,} bytes | Itemized/Turnkey BOQ validation"
                    elif d in ["03_Technical_Specifications_Reports", "04_Architectural_Drawings", "05_Structural_Drawings"]:
                        dataset_role = "Model input"
                        same_proj_ver = "Verified"
                        notes = f"Size: {sz:,} bytes | Primary technical drawing/spec"
                    elif d in ["06_MEP_Services", "07_Landscape_Infrastructure", "08_Execution_Actuals"]:
                        dataset_role = "Supporting"
                        same_proj_ver = "Verified"
                        notes = f"Size: {sz:,} bytes | Supporting engineering data"
                    elif d == "99_Unverified_or_Related_References":
                        dataset_role = "Supporting"
                        same_proj_ver = "Uncertain"
                        notes = f"Size: {sz:,} bytes | Reference only"
                    else:
                        dataset_role = "Model input"
                        same_proj_ver = "Verified"
                        notes = f"Size: {sz:,} bytes"

                    manifest_rows.append({
                        "Project name": p_data["project_name"],
                        "Tender reference": p_data["tender_reference"],
                        "Selected model scope": scope["building_name"],
                        "Category": d,
                        "File name": f,
                        "Local path": rel_local,
                        "Source URL": p_data["sources"][0][1] if p_data["sources"] else "Official Portal",
                        "Source authority": p_data["authority"],
                        "Official status": p_data["official_status"],
                        "Document date": p_data["date"],
                        "Same-project verification": same_proj_ver,
                        "Dataset role": dataset_role,
                        "Duplicate of": duplicate_of,
                        "Notes": notes
                    })

        # Write 14-column CSV manifest
        manifest_path = os.path.join(p_path, "file_manifest.csv")
        fieldnames = [
            "Project name", "Tender reference", "Selected model scope", "Category",
            "File name", "Local path", "Source URL", "Source authority",
            "Official status", "Document date", "Same-project verification",
            "Dataset role", "Duplicate of", "Notes"
        ]
        with open(manifest_path, "w", encoding="utf-8", newline="") as mf:
            writer = csv.DictWriter(mf, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(manifest_rows)

        # Build Standardized README.md with Audit Table & Selected Scope Block
        readme_lines = [
            f"# {p_data['project_name']}\n",
            "## 1. Project Identity & Verification Summary\n",
            f"- **Official Project Title:** {p_data['project_name']}",
            f"- **Tender Reference / ID:** `{p_data['tender_reference']}`",
            f"- **Client / Authority:** {p_data['authority']}",
            f"- **Official / Public Status:** {p_data['official_status']}",
            f"- **Document Date / Period:** {p_data['date']}",
            f"- **Dataset Classification:** **{p_data['classification']}**\n",
            "### Official Public Sources & Download Links",
        ]
        for s_name, s_url in p_data["sources"]:
            readme_lines.append(f"- **{s_name}:** [{s_url}]({s_url})")
        readme_lines.append("")

        # Selected Model Scope Block (Step 2)
        readme_lines.append("## 2. Selected Single-Building Model Scope\n")
        readme_lines.append("```text")
        readme_lines.append("Selected model scope:")
        readme_lines.append(f"Building / Tower / Block / Type: {scope['building_name']}")
        readme_lines.append(f"Number of floors: {scope['floors']}")
        readme_lines.append(f"Drawing reference: {scope['drawing_ref']}")
        readme_lines.append(f"Matching BOQ section: {scope['boq_ref']}")
        readme_lines.append(f"Reason selected: {scope['reason_selected']}")
        readme_lines.append("```\n")

        # Standardized 11-Row Audit Table (Step 1)
        readme_lines.append("## 3. Same-Project Dataset Audit Table\n")
        readme_lines.append("| Dataset requirement | Status | Exact file(s) present | Same-project verified | Action required |")
        readme_lines.append("| :--- | :---: | :--- | :---: | :--- |")
        for req, stat, exact, ver, act in p_data["audit_table"]:
            readme_lines.append(f"| {req} | **{stat}** | {exact} | {ver} | {act} |")
        readme_lines.append("")

        # Classification Section
        readme_lines.append("## 4. Final Classification & Suitability\n")
        readme_lines.append(f"### **Classification: {p_data['classification']}**")
        readme_lines.append(f"*{p_data['classification_desc']}*\n")

        # Hierarchy & Files
        readme_lines.append("## 5. Canonical Directory Hierarchy\n")
        readme_lines.append("```text")
        readme_lines.append(f"{p_name}/")
        readme_lines.append("│")
        for d in STANDARD_DIRS:
            readme_lines.append(f"├── {d}/")
        readme_lines.append("├── file_manifest.csv")
        readme_lines.append("└── README.md")
        readme_lines.append("```\n")
        readme_lines.append(f"Total cataloged entries: **{len(manifest_rows)} files**. Refer to [`file_manifest.csv`](file_manifest.csv) for full provenance and duplicate tags.\n")

        readme_path = os.path.join(p_path, "README.md")
        with open(readme_path, "w", encoding="utf-8") as rf:
            rf.write("\n".join(readme_lines))

        print(f"  [{p_name}] -> {p_data['classification']} | Scope: {scope['building_name']} ({len(manifest_rows)} entries)")

        # Record for central report
        report_rows.append({
            "Project": p_name,
            "Selected building scope": scope["building_name"],
            "Current class": p_data["classification"],
            "Missing critical files": p_data["missing_critical"],
            "Files newly downloaded": p_data["newly_downloaded"],
            "Verification confidence": p_data["confidence"],
            "Next action": p_data["next_action"]
        })

    # 3. Produce 30_PROJECT_REFINEMENT_REPORT.csv
    print("\nPhase 3: Generating 30_PROJECT_REFINEMENT_REPORT.csv...")
    report_path = os.path.join(BASE_DIR, "30_PROJECT_REFINEMENT_REPORT.csv")
    rep_fieldnames = [
        "Project", "Selected building scope", "Current class",
        "Missing critical files", "Files newly downloaded",
        "Verification confidence", "Next action"
    ]
    with open(report_path, "w", encoding="utf-8", newline="") as rpf:
        writer = csv.DictWriter(rpf, fieldnames=rep_fieldnames)
        writer.writeheader()
        writer.writerows(report_rows)
    print(f"Successfully generated: {report_path}")

    # 4. Compute exact classification breakdown
    class_counts = defaultdict(int)
    for r in report_rows:
        class_counts[r["Current class"]] += 1
    print("\n" + "=" * 80)
    print("FINAL 30-PROJECT CLASSIFICATION SUMMARY")
    print("=" * 80)
    for c in ["Gold", "Silver", "Reference only", "Reject"]:
        print(f"  - {c.upper()}: {class_counts[c]} projects")
    print(f"  TOTAL: {len(report_rows)} projects")
    print("=" * 80)

    # 5. Synchronize Root README.md
    print("\nPhase 4: Synchronizing Root Hub README.md...")
    root_readme = os.path.join(BASE_DIR, "README.md")
    root_lines = [
        "# DataRequirement — Same-Project Construction Intelligence Datasets Hub\n",
        "Central repository hub organizing 30 Indian government, PSU, institutional, and benchmark residential construction tender packages for civil-engineering intelligence models (quantity estimation, material estimation, cost modeling, and duration prediction).\n",
        "Every project strictly adheres to the canonical 10-subdirectory taxonomy, strict same-project integrity rules, single-building scope selection, and the enhanced 14-column manifest schema.\n",
        "## 🏗️ Active Project Repositories (30 Projects Audit)\n",
        "| # | Project Repository | Selected Building Scope | Class | Missing Critical Files | Verification Confidence | Next Action |",
        "| :-: | :--- | :--- | :---: | :--- | :---: | :--- |"
    ]
    for idx, r in enumerate(report_rows, start=1):
        folder_url = urllib.parse.quote(f"{BASE_DIR.replace(os.sep, '/')}/{r['Project']}", safe=":/")
        root_lines.append(f"| {idx} | [`{r['Project']}`](file:///{folder_url}) | {r['Selected building scope']} | **{r['Current class']}** | {r['Missing critical files']} | {r['Verification confidence']} | {r['Next action']} |")

    root_lines.append("\n---\n")
    root_lines.append("## 📊 Summary Metrics\n")
    root_lines.append(f"- **Gold Projects ({class_counts['Gold']})**: Ready for end-to-end quantity and cost prototype modeling (full drawings + BOQs + specs + costs).")
    root_lines.append(f"- **Silver Projects ({class_counts['Silver']})**: High-value official packages with one or two specific post-award engineering deliverables pending.")
    root_lines.append(f"- **Reference Only Projects ({class_counts['Reference only']})**: Valuable statutory benchmarks, township charters, or consultancy packages where working GFC drawings or trade BOQs are restricted.")
    root_lines.append(f"- **Reject Projects ({class_counts['Reject']})**: Formally audited and rejected candidate projects with no public procurement record, preventing training set contamination.\n")
    root_lines.append("## 📁 Standard Project Architecture\n")
    root_lines.append("```text\nProject-Name/\n│\n├── 00_Core_Intelligence_Dataset/\n├── 01_Tender_NIT_PreBid/\n├── 02_Cost_BOQ_Makes/\n├── 03_Technical_Specifications_Reports/\n├── 04_Architectural_Drawings/\n├── 05_Structural_Drawings/\n├── 06_MEP_Services/\n├── 07_Landscape_Infrastructure/\n├── 08_Execution_Actuals/\n├── 99_Unverified_or_Related_References/\n├── file_manifest.csv  (14-column enhanced schema)\n└── README.md          (Standardized 11-row audit table & selected scope block)\n```\n")

    with open(root_readme, "w", encoding="utf-8") as rf:
        rf.write("\n".join(root_lines))
    print("Root README.md successfully synchronized!")

if __name__ == "__main__":
    execute_refinement()

