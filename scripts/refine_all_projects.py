#!/usr/bin/env python3
"""
Master Dataset Refinement & Standardization Script
Strictly enforces the Canonical 10-Subdirectory Architecture, 12-Column Manifest,
and Completeness Table & Classification across all 12 Indian Residential Construction Projects.
"""

import os
import sys
import shutil
import csv
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

PROJECT_METADATA = {
    "NIT-Nalanda": {
        "project_name": "Construction of Residential Buildings (Package 1C) at Nalanda University Campus",
        "tender_reference": "Package 1C (Residential Buildings)",
        "package": "Faculty Apartments (Type 1B, 2, 3), Bungalows & Student Hostels (T1-T13)",
        "authority": "Nalanda University, Rajgir, Bihar",
        "official_status": "Official (Nalanda University / eprocure.gov.in)",
        "date": "2017-2019",
        "building_scope": "Faculty Apartments, Faculty Bungalows & Hostels T1-T13",
        "classification": "Gold",
        "classification_desc": "Ready for end-to-end prototype (Full drawings, BOQ, specs & cost verified for same scope)",
        "sources": [
            ("Nalanda University Portal", "https://www.nalandauniv.edu.in"),
            ("CPPP Tender Portal", "https://eprocure.gov.in/eprocure/app")
        ],
        "completeness": {
            "Tender/NIT": ("Yes", "Yes", "Yes"),
            "Architectural drawings": ("Yes", "Yes", "Yes"),
            "Structural drawings": ("Yes", "Yes", "Yes"),
            "Civil specifications": ("Yes", "Yes", "Yes"),
            "BOQ quantities": ("Yes", "Yes", "Validation only"),
            "Cost/rates": ("Yes", "Yes", "Validation only"),
            "Time schedule": ("Yes", "Yes", "Validation only"),
            "Soil/geotech": ("Yes", "Yes", "Optional but valuable"),
            "Execution actuals": ("Yes", "Yes", "Optional but valuable")
        }
    },
    "OIL-RITES-Duliajan-BQ-Housing": {
        "project_name": "Construction of BQ Workmen Housing Complex at Duliajan (EPC Mode-II)",
        "tender_reference": "RITES/NERPO/OIL/BQ-HOUSING/25 (CPP: 2025_RITES_246752_1)",
        "package": "8 Towers Stilt+6 (192 units), Guest House, Community Centre, Substation, STP",
        "authority": "Oil India Limited (OIL) / RITES Ltd.",
        "official_status": "Official (RITES Ltd. / Oil India Ltd.)",
        "date": "2024-2025",
        "building_scope": "8 Residential Towers (Stilt+6), Guest House, Community Centre",
        "classification": "Gold",
        "classification_desc": "Ready for end-to-end prototype (Turnkey EPC with full drawings, DBR, 310-pg geotech & BOQ)",
        "sources": [
            ("RITES Tender Portal", "https://www.rites.com"),
            ("CPPP Portal", "https://eprocure.gov.in/eprocure/app")
        ],
        "completeness": {
            "Tender/NIT": ("Yes", "Yes", "Yes"),
            "Architectural drawings": ("Yes", "Yes", "Yes"),
            "Structural drawings": ("Yes", "Yes", "Yes"),
            "Civil specifications": ("Yes", "Yes", "Yes"),
            "BOQ quantities": ("Yes", "Yes", "Validation only"),
            "Cost/rates": ("Yes", "Yes", "Validation only"),
            "Time schedule": ("Yes", "Yes", "Validation only"),
            "Soil/geotech": ("Yes", "Yes", "Optional but valuable"),
            "Execution actuals": ("Yes", "Yes", "Optional but valuable")
        }
    },
    "BMC-Deonar-600-Tenements": {
        "project_name": "Turnkey Construction of 2,068 Tenements on Plot Known as 600 Tenements, Deonar",
        "tender_reference": "Bid No. 7200035221 / ETH_7000022191",
        "package": "6 High-Rise Towers (P1+P2+P3+Stilt+22 Floors), 60,881 m2 Podium, Building 04",
        "authority": "Brihanmumbai Municipal Corporation (BMC / MCGM)",
        "official_status": "Official (BMC / MCGM Portal)",
        "date": "2022-08-13",
        "building_scope": "Building 04 (P+S+22 Floors) & Podium P1-P3",
        "classification": "Gold",
        "classification_desc": "Ready for end-to-end prototype (Full Building 04 8-sheet drawing pack, Podium pack & BUA cost)",
        "sources": [
            ("BMC Official Portal", "https://www.mcgm.gov.in"),
            ("Mahatenders Portal", "https://mahatenders.gov.in")
        ],
        "completeness": {
            "Tender/NIT": ("Yes", "Yes", "Yes"),
            "Architectural drawings": ("Yes", "Yes", "Yes"),
            "Structural drawings": ("Yes", "Yes", "Yes"),
            "Civil specifications": ("Yes", "Yes", "Yes"),
            "BOQ quantities": ("Yes", "Yes", "Validation only"),
            "Cost/rates": ("Yes", "Yes", "Validation only"),
            "Time schedule": ("Yes", "Yes", "Validation only"),
            "Soil/geotech": ("No", "No", "Optional but valuable"),
            "Execution actuals": ("Yes", "Yes", "Optional but valuable")
        }
    },
    "BHEL-Township-Jagdishpur": {
        "project_name": "Construction of Multi-Storey Flats Type-A/B/C/D + CEO Residence & Utility Buildings for Township at Jagdishpur",
        "tender_reference": "BHE/FP/CVL/021 (Earlier: BHE/FP/CVL/012, Consultancy: BHE/FP/CVL/001)",
        "package": "260 Flats (8 Multi-Storey Blocks Type-A/B/C/D), 2 CEO Residences, Transit Hostel, Club/Gym, Shopping Center, Dispensary",
        "authority": "Bharat Heavy Electricals Limited (BHEL) - CSU & FP Jagdishpur",
        "official_status": "Official (bhel.com / tenders.bhel.com)",
        "date": "2023-2024",
        "building_scope": "260 Flats (Type-A 128u, Type-B 64u, Type-C 56u, Type-D 12u) + 2 CEO Residences + Utilities on 31.6 Acres",
        "classification": "Silver",
        "classification_desc": "Useful multi-block township package (Complete 114-pg master tender BHE/FP/CVL/021, 260 flats + 2 CEO residences, 8-pg specification charts)",
        "sources": [
            ("BHEL Master Tender Document", "https://www.bhel.com/sites/default/files/NIT-GCC-SCC-DRG-SPEC-BOQ%20Cover%20Township-Final%20Revised_1.pdf"),
            ("BHEL Stage-I Tender Document", "https://www.bhel.com/sites/default/files/GCC%20+%20SCC%20+%20DRG%20Township-Final.pdf"),
            ("BHEL Engineering Consultancy BOQ", "https://www.bhel.com/sites/default/files/SCC-DRG-BOQ%20Final.pdf"),
            ("BHEL Engineering Technical Specs", "https://www.bhel.com/sites/default/files/Tech%20Specs-FINAL.pdf"),
            ("Scribd Township BOQ Benchmark", "https://www.scribd.com/document/423198487/Township-BOQ-With-Corrigendum"),
            ("BHEL Contracts Concluded Report", "https://tenders.bhel.com/sites/default/files/CC_01.01.2025_to_31.01.2025-2025-08-08-09:51:39.pdf")
        ],
        "completeness": {
            "Tender/NIT": ("Yes", "Yes", "Yes"),
            "Architectural drawings": ("Partial", "Yes", "16 reference sheets in tender; full CAD drawings in RAR archive require portal login"),
            "Structural drawings": ("Partial", "Yes", "Structural design basis and pile equipment in tender; GFC drawings issued post-award"),
            "Civil specifications": ("Yes", "Yes", "Yes"),
            "BOQ quantities": ("Yes", "Yes", "Validation only"),
            "Cost/rates": ("Yes", "Yes", "Validation only"),
            "Time schedule": ("Yes", "Yes", "Validation only"),
            "Soil/geotech": ("No", "No", "Geotechnical investigation framework in BHE/FP/CVL/001; borehole logs not in public domain"),
            "Execution actuals": ("No", "No", "Optional but valuable")
        }
    },
    "SBI-Enclave-Hyderabad": {
        "project_name": "Construction of 134 Residential Flats (2 Towers) + Office + Clubhouse for State Bank of India",
        "tender_reference": "SBI Real Estate Hyderabad / Part B GCC, Part C SCC, Part D DBR",
        "package": "134 Residential Flats across 2 Towers (B+S+14 Floors), Office Building & Clubhouse",
        "authority": "State Bank of India (SBI)",
        "official_status": "Official (bank.sbi)",
        "date": "2024-2025",
        "building_scope": "2 Residential Towers (134 Flats), Office Building, Clubhouse",
        "classification": "Gold",
        "classification_desc": "Ready for end-to-end prototype (Official 7.97 MB Structural DBR + GCC 2.61 MB + SCC 1.72 MB)",
        "sources": [
            ("SBI Structural DBR", "https://bank.sbi/webfiles/uploads/files_2526/07/290720251210-PART%20D-DBR.pdf"),
            ("SBI GCC Document", "https://bank.sbi/webfiles/uploads/files_2526/07/290720251209-PART%20B%20GCC.pdf"),
            ("SBI SCC Document", "https://bank.sbi/webfiles/uploads/files_2526/07/290720251209-PART%20CSCC.pdf")
        ],
        "completeness": {
            "Tender/NIT": ("Yes", "Yes", "Yes"),
            "Architectural drawings": ("Yes", "Yes", "Yes"),
            "Structural drawings": ("Yes", "Yes", "Yes"),
            "Civil specifications": ("Yes", "Yes", "Yes"),
            "BOQ quantities": ("Yes", "Yes", "Validation only"),
            "Cost/rates": ("Yes", "Yes", "Validation only"),
            "Time schedule": ("Yes", "Yes", "Validation only"),
            "Soil/geotech": ("Yes", "Yes", "Optional but valuable"),
            "Execution actuals": ("No", "No", "Optional but valuable")
        }
    },
    "SBI-DN-Nagar-Andheri-122-Flats": {
        "project_name": "Construction of 122 NOS Residential Flats (2 Towers) for SBI DN Nagar Andheri West Mumbai in EPC Mode",
        "tender_reference": "SBI/CC/2025-26/DNN/01",
        "package": "122 Residential Flats across 2 High-Rise Towers in EPC Turnkey Mode",
        "authority": "State Bank of India (SBI) - Premises Department Corporate Office",
        "official_status": "Official (sbi.co.in / sbi.bank.in)",
        "date": "2025-08-26",
        "building_scope": "122 Residential Flats (2 High-Rise Towers)",
        "classification": "Silver",
        "classification_desc": "Useful metropolitan EPC high-rise package (Full Parts B, C, D, E, F, drawings & financial schedule)",
        "sources": [
            ("SBI Procurement Portal", "https://sbi.co.in/web/sbi-in-the-news/procurement-news"),
            ("NIT Document", "https://sbi.co.in/documents/39129/51516783/NOTICE+INVITING+TENDER20250828084234367.pdf"),
            ("Part F Financial Bid", "https://sbi.bank.in/webfiles/uploads/files_2526/09/170920251556-PART%20F%20PRICE%20BID%20AND%20BOQ.pdf"),
            ("Part D Technical Specs", "https://sbi.bank.in/webfiles/uploads/files_2526/08/280820251414-PART%20D_TECH%20SPEC.pdf"),
            ("Part E Tender Drawings", "https://sbi.bank.in/documents/39129/57554832/PART+A+15.07.2026.pdf/4d4bf503-e695-61e3-b383-6b55f82f5192?t=1784120792508")
        ],
        "completeness": {
            "Tender/NIT": ("Yes", "Yes", "Yes"),
            "Architectural drawings": ("Yes", "Yes", "Yes"),
            "Structural drawings": ("Partial", "Yes", "Post-award GFC required"),
            "Civil specifications": ("Yes", "Yes", "Yes"),
            "BOQ quantities": ("Yes", "Yes", "Validation only"),
            "Cost/rates": ("Yes", "Yes", "Validation only"),
            "Time schedule": ("No", "No", "In tender document"),
            "Soil/geotech": ("Partial", "Yes", "Shared post-award only"),
            "Execution actuals": ("No", "No", "Optional but valuable")
        }
    },
    "NPCIL-Anuvijay-240-Quarters": {
        "project_name": "Construction of 240 Nos. of D-Type Residential Quarters (6 Blocks of G+10 Floors) including External Services",
        "tender_reference": "2025_NPCIL_222105_1 / NPCIL/KK-3&4/CONST/CIVIL-INFRA/PT/2018/150",
        "package": "6 Blocks G+10 (240 D-Type Units), Water Transmission Main, Sewer Trunks, Roads, 11kV Substation",
        "authority": "Nuclear Power Corporation of India Limited (NPCIL) – KKNPP Units 3 & 4",
        "official_status": "Official (NPCIL Portal / CPPP)",
        "date": "2025-07-15",
        "building_scope": "6 Blocks of G+10 High-Rise Quarters (240 D-Type Units)",
        "classification": "Silver",
        "classification_desc": "Useful nuclear township package (Official EOI, Item-Rate BOQ, Technical Specs, 3 Official 10Cr Registers)",
        "sources": [
            ("NPCIL Live Tenders", "https://www.npcil.nic.in/content/262_1_livetenders.aspx"),
            ("CPPP Portal", "https://etenders.gov.in/eprocure/app"),
            ("NPCIL 10Cr Register (Apr 2026)", "https://www.npcil.nic.in/WriteReadData/userfiles/file/10Cr_01Apr2026_01_WO.pdf"),
            ("NPCIL 10Cr Register (Jul 2024)", "https://www.npcil.nic.in/WriteReadData/userfiles/file/10Cr_24Jul2024_01_WO.pdf"),
            ("NPCIL 10Cr Register (Jun 2024)", "https://www.npcil.nic.in/WriteReadData/userfiles/file/10Cr_28Jun2024_01_WO.pdf")
        ],
        "completeness": {
            "Tender/NIT": ("Yes", "Yes", "Yes"),
            "Architectural drawings": ("Yes", "Yes", "Yes"),
            "Structural drawings": ("Partial", "Yes", "Post-award GFC required"),
            "Civil specifications": ("Yes", "Yes", "Yes"),
            "BOQ quantities": ("Yes", "Yes", "Validation only"),
            "Cost/rates": ("Yes", "Yes", "Validation only"),
            "Time schedule": ("Yes", "Yes", "Validation only"),
            "Soil/geotech": ("No", "No", "Optional but valuable"),
            "Execution actuals": ("Yes", "Yes", "Optional but valuable")
        }
    },
    "IIT-Kanpur-Type-II-Apartments": {
        "project_name": "Construction of Type-II Apartments (G+10, 80 Nos) at IIT Kanpur",
        "tender_reference": "NIT No. 44/Composite/D3/2024-25",
        "package": "Type-II Apartments (G+10, 80 Flats) with Electrical, Lifts & Fire Fighting",
        "authority": "Indian Institute of Technology Kanpur (IITK) – IWD",
        "official_status": "Official (IIT Kanpur IWD Portal)",
        "date": "2025-03-03",
        "building_scope": "Type-II Apartment Tower (G+10, 80 Flats)",
        "classification": "Silver",
        "classification_desc": "Useful but missing standalone CAD drawing files (Drawing registry & 190-page tender PDF present)",
        "sources": [
            ("IIT Kanpur IWD", "https://www.iitk.ac.in/iwd/tender.htm"),
            ("CPPP Portal", "https://eprocure.gov.in")
        ],
        "completeness": {
            "Tender/NIT": ("Yes", "Yes", "Yes"),
            "Architectural drawings": ("Yes", "Yes", "Yes"),
            "Structural drawings": ("No", "No", "No"),
            "Civil specifications": ("Yes", "Yes", "Yes"),
            "BOQ quantities": ("Yes", "Yes", "Validation only"),
            "Cost/rates": ("Yes", "Yes", "Validation only"),
            "Time schedule": ("Yes", "Yes", "Validation only"),
            "Soil/geotech": ("No", "No", "Optional but valuable"),
            "Execution actuals": ("No", "No", "Optional but valuable")
        }
    },
    "EPI-Trimbakeshwar-EMRS": {
        "project_name": "Construction of Eklavya Model Residential School (EMRS) at Trimbakeshwar, Nashik",
        "tender_reference": "WRO/CON/EMRS/872/334",
        "package": "Residential Campus (School G+2, Boys Hostel 240, Girls Hostel 240, Dining, 42 Flats, STP)",
        "authority": "Engineering Projects (India) Limited (EPI) / NESTS (MoTA)",
        "official_status": "Official (EPI Portal / CPPP)",
        "date": "2024-03-09",
        "building_scope": "Entire EMRS Residential Campus (480 Students)",
        "classification": "Silver",
        "classification_desc": "Useful but contractor produces GFC structural drawings post-award (26.8 MB Volume I Bid PDF present)",
        "sources": [
            ("EPI Official Portal", "https://epi.gov.in"),
            ("CPPP Portal", "https://etenders.gov.in/eprocure/app")
        ],
        "completeness": {
            "Tender/NIT": ("Yes", "Yes", "Yes"),
            "Architectural drawings": ("Yes", "Yes", "Yes"),
            "Structural drawings": ("No", "No", "No"),
            "Civil specifications": ("Yes", "Yes", "Yes"),
            "BOQ quantities": ("Yes", "Yes", "Validation only"),
            "Cost/rates": ("Yes", "Yes", "Validation only"),
            "Time schedule": ("Yes", "Yes", "Validation only"),
            "Soil/geotech": ("No", "No", "Optional but valuable"),
            "Execution actuals": ("No", "No", "Optional but valuable")
        }
    },
    "EPI-Dhenkanal-ICDS-Staff-Quarters": {
        "project_name": "Tender for Construction of E-Type Staff Quarter (S+4) for ICDS Staff Quarter at Dhenkanal, Odisha (2nd Call)",
        "tender_reference": "EPI/CO/CON/977/861",
        "package": "1 Block E-Type Staff Quarter (Stilt + 4 Floors), External Services & Site Development",
        "authority": "Engineering Projects (India) Ltd. (EPI) / WCD Govt of Odisha",
        "official_status": "Official (epi.gov.in)",
        "date": "2024-09-25",
        "building_scope": "E-Type Staff Quarter (S+4)",
        "classification": "Silver",
        "classification_desc": "Useful institutional package (Complete 3-volume tender package without login, BOQ & Rs 6.94 Cr award)",
        "sources": [
            ("EPI Tender Portal", "https://epi.gov.in/tender"),
            ("Volume 1 Tender Document", "https://epi.gov.in/admin/image/tenders/1727335871_Volume1.pdf"),
            ("Volume 2 Specifications & Drawings", "https://epi.gov.in/admin/image/tenders/1727335871_volume2.pdf"),
            ("Volume 3 BOQ Price Bid", "https://epi.gov.in/admin/image/tenders/1727335871_Volume3.pdf")
        ],
        "completeness": {
            "Tender/NIT": ("Yes", "Yes", "Yes"),
            "Architectural drawings": ("Yes", "Yes", "Yes"),
            "Structural drawings": ("Partial", "Yes", "Post-award GFC required"),
            "Civil specifications": ("Yes", "Yes", "Yes"),
            "BOQ quantities": ("Yes", "Yes", "Validation only"),
            "Cost/rates": ("Yes", "Yes", "Validation only"),
            "Time schedule": ("Yes", "Yes", "Validation only"),
            "Soil/geotech": ("No", "No", "Optional but valuable"),
            "Execution actuals": ("Yes", "Yes", "Optional but valuable")
        }
    },
    "WB-PWD-Burdwan-Type-I-II-Quarters": {
        "project_name": "Construction of Proposed Residential Type-I & Type-II Quarters at Burdwan Division Campus",
        "tender_reference": "BOQ_1634922 / WB PWD Social Sector Burdwan",
        "package": "Type-I (1BHK) & Type-II (2BHK) Quarters (G+1/G+2 Blocks), External Services & Campus Development",
        "authority": "Public Works Department (PWD), Government of West Bengal - Burdwan Division",
        "official_status": "Official (wbtenders.gov.in / pwd.wb.gov.in)",
        "date": "2024-2025",
        "building_scope": "Type-I & Type-II Quarters (G+1/G+2 Blocks, 16 Units)",
        "classification": "Silver",
        "classification_desc": "Useful state PWD housing dataset (Official WBF-2911 contract form, itemized BOQ schedule & WB PWD SOR standards)",
        "sources": [
            ("WB eTender Portal", "https://wbtenders.gov.in/nicgep/app"),
            ("WB PWD Portal", "https://pwd.wb.gov.in"),
            ("Official WBF-2911 Form", "https://wbxpress.com/wp-content/uploads/2019/12/WBF-2911.pdf")
        ],
        "completeness": {
            "Tender/NIT": ("Yes", "Yes", "Yes"),
            "Architectural drawings": ("Yes", "Yes", "Yes"),
            "Structural drawings": ("Partial", "Yes", "Post-award GFC required"),
            "Civil specifications": ("Yes", "Yes", "Yes"),
            "BOQ quantities": ("Yes", "Yes", "Validation only"),
            "Cost/rates": ("Yes", "Yes", "Validation only"),
            "Time schedule": ("Yes", "Yes", "Validation only"),
            "Soil/geotech": ("No", "No", "Optional but valuable"),
            "Execution actuals": ("No", "No", "Optional but valuable")
        }
    },
    "KMRL-Kochi-Metro-Muttom-Quarters": {
        "project_name": "Multi-Storey Residential Staff Quarters at Muttom (Phase-I)",
        "tender_reference": "KMRL/PRJ/STAFF QTRS @ MUTTOM-162/2014/TEN 03-15",
        "package": "Multi-Storey Residential Staff Quarters (Type-II, III, IV units)",
        "authority": "Kochi Metro Rail Limited (KMRL)",
        "official_status": "Official (Kochi Metro Portal)",
        "date": "2015-03-15",
        "building_scope": "Residential Staff Quarters Towers at Muttom Depot",
        "classification": "Silver",
        "classification_desc": "Useful design consultancy + construction master package (6.47 MB Tender PDF present)",
        "sources": [
            ("Kochi Metro Portal", "https://kochimetro.org")
        ],
        "completeness": {
            "Tender/NIT": ("Yes", "Yes", "Yes"),
            "Architectural drawings": ("Yes", "Yes", "Yes"),
            "Structural drawings": ("No", "No", "No"),
            "Civil specifications": ("Yes", "Yes", "Yes"),
            "BOQ quantities": ("Yes", "Yes", "Validation only"),
            "Cost/rates": ("Yes", "Yes", "Validation only"),
            "Time schedule": ("Yes", "Yes", "Validation only"),
            "Soil/geotech": ("No", "No", "Optional but valuable"),
            "Execution actuals": ("No", "No", "Optional but valuable")
        }
    },
    "DFCCIL-Jaipur-Staff-Quarters": {
        "project_name": "Construction of Type-3 Staff Quarters at 7 DFC Stations & FLN Building Extension",
        "tender_reference": "JP-EN-Quarter-2024-11 / JP-EN-Quarter-2023-18",
        "package": "Type-3 Quarters at REJN, AELN, DBLN, BAGN, SMPN, PMPN, FLN & FLN Service Building",
        "authority": "Dedicated Freight Corridor Corporation of India Limited (DFCCIL)",
        "official_status": "Official (IREPS / DFCCIL)",
        "date": "2024-07-12",
        "building_scope": "Standard Type-3 Quarters & FLN Vertical Extension",
        "classification": "Silver",
        "classification_desc": "Useful railway housing package (July 2024 & Dec 2023 Master PDFs present; structural proof-checking)",
        "sources": [
            ("IREPS Portal", "https://www.ireps.gov.in"),
            ("DFCCIL Portal", "https://dfccil.com")
        ],
        "completeness": {
            "Tender/NIT": ("Yes", "Yes", "Yes"),
            "Architectural drawings": ("Yes", "Yes", "Yes"),
            "Structural drawings": ("No", "No", "No"),
            "Civil specifications": ("Yes", "Yes", "Yes"),
            "BOQ quantities": ("Yes", "Yes", "Validation only"),
            "Cost/rates": ("Yes", "Yes", "Validation only"),
            "Time schedule": ("Yes", "Yes", "Validation only"),
            "Soil/geotech": ("No", "No", "Optional but valuable"),
            "Execution actuals": ("No", "No", "Optional but valuable")
        }
    },
    "K-RIDE-Belandur-Road-Quarters": {
        "project_name": "Belandur Road Station Building & Hosur Doubling Railway Staff Quarters",
        "tender_reference": "Belandur Road Station & Hosur Quarters Package",
        "package": "Belandur Road Station Facilities + Type-II & Type-III Quarters (16 Units)",
        "authority": "Rail Infrastructure Development Company (Karnataka) Limited (K-RIDE)",
        "official_status": "Official (K-RIDE / eproc.karnataka.gov.in)",
        "date": "2023-08-15",
        "building_scope": "Railway Staff Quarters Type-II/III & Station Facilities",
        "classification": "Silver",
        "classification_desc": "Useful railway residential package (313-page bid volume + Hosur Quarters volume present)",
        "sources": [
            ("K-RIDE Portal", "https://kride.in"),
            ("Karnataka e-Procurement", "https://eproc.karnataka.gov.in")
        ],
        "completeness": {
            "Tender/NIT": ("Yes", "Yes", "Yes"),
            "Architectural drawings": ("Yes", "Yes", "Yes"),
            "Structural drawings": ("No", "No", "No"),
            "Civil specifications": ("Yes", "Yes", "Yes"),
            "BOQ quantities": ("Yes", "Yes", "Validation only"),
            "Cost/rates": ("Yes", "Yes", "Validation only"),
            "Time schedule": ("Yes", "Yes", "Validation only"),
            "Soil/geotech": ("No", "No", "Optional but valuable"),
            "Execution actuals": ("No", "No", "Optional but valuable")
        }
    },
    "CPWD-RBI-Kharghar-354-Quarters": {
        "project_name": "Construction of 354 Nos. Staff Quarters, Hostel Building & Academic Block for RBI",
        "tender_reference": "01/NIT/CE CUM ED/ EE & SM-I/2024-25",
        "package": "9 Towers (G+10/11, 354 Units), ZTC Hostel (82 suites), Academic Block, Package-2 Interiors",
        "authority": "Reserve Bank of India (RBI) / Central Public Works Department (CPWD)",
        "official_status": "Official (CPWD / RBI)",
        "date": "2024-09-30",
        "building_scope": "354 Residential Quarters across 9 Towers + Hostel + Academic Block",
        "classification": "Silver",
        "classification_desc": "Useful multi-package institutional housing (Package-2 ₹46.25 Cr interior BOQ & NUPC Drawing spec)",
        "sources": [
            ("RBI Tender Window", "https://www.rbi.org.in/Scripts/BS_ViewTenders.aspx?Id=12121"),
            ("CPWD eTender Portal", "https://etender.cpwd.gov.in")
        ],
        "completeness": {
            "Tender/NIT": ("Yes", "Yes", "Yes"),
            "Architectural drawings": ("Yes", "Yes", "Yes"),
            "Structural drawings": ("No", "No", "No"),
            "Civil specifications": ("Yes", "Yes", "Yes"),
            "BOQ quantities": ("Yes", "Yes", "Validation only"),
            "Cost/rates": ("Yes", "Yes", "Validation only"),
            "Time schedule": ("Yes", "Yes", "Validation only"),
            "Soil/geotech": ("No", "No", "Optional but valuable"),
            "Execution actuals": ("No", "No", "Optional but valuable")
        }
    },
    "NBCC-GPRA-Sarojini-Nagar": {
        "project_name": "Redevelopment of GPRA Colony at Sarojini Nagar, New Delhi",
        "tender_reference": "Packages III, VI, V-A, V-B, V-C, IV-A, IV-C, VII-A/B",
        "package": "Mega-Redevelopment across 10,190 dwelling units + Commercial",
        "authority": "NBCC (India) Limited / MoHUA",
        "official_status": "Official (NBCC / CPPP)",
        "date": "2020-2024",
        "building_scope": "Multi-package GPRA Township (10,190 Units)",
        "classification": "Reference only",
        "classification_desc": "Useful context across mega packages, but unsuitable for single-building quantity model validation",
        "sources": [
            ("NBCC Portal", "https://www.nbccindia.in"),
            ("NBCC e-Nivida", "https://nbcc.enivida.com")
        ],
        "completeness": {
            "Tender/NIT": ("Yes", "Yes", "Yes"),
            "Architectural drawings": ("Yes", "Yes", "No"),
            "Structural drawings": ("No", "No", "No"),
            "Civil specifications": ("Yes", "Yes", "Yes"),
            "BOQ quantities": ("Yes", "Yes", "Validation only"),
            "Cost/rates": ("Yes", "Yes", "Validation only"),
            "Time schedule": ("Yes", "Yes", "Validation only"),
            "Soil/geotech": ("No", "No", "Optional but valuable"),
            "Execution actuals": ("No", "No", "Optional but valuable")
        }
    },
    "TCIL-NVS-JNV-Azamgarh-Quarters": {
        "project_name": "Conversion of SP Shed to Regular Staff Quarters including Construction of Shortfall Quarters at JNV Azamgarh (UP)",
        "tender_reference": "TCIL/C/PD(UP)/NVS/2026/08 (CPP: 2026_TCIL_277790_1)",
        "package": "1 Block Type-II Quarters (G+1, 8 Flats), 1 Guest House (4 Suites), SP Shed Dismantling & Campus Infrastructure",
        "authority": "Navodaya Vidyalaya Samiti (NVS) / Telecommunications Consultants India Limited (TCIL)",
        "official_status": "Official (tcil.net.in / CPPP)",
        "date": "2026-05-16",
        "building_scope": "Type-II Quarters (G+1, 8 Units) & Guest House (4 Suites) + External Infrastructure",
        "classification": "Silver",
        "classification_desc": "Useful school staff housing package (Complete master technical bid & 69-page BOQ with floor plans & area statements)",
        "sources": [
            ("TCIL Official Tender Portal", "https://www.tcil.net.in"),
            ("Volume I Technical Bid", "https://www.tcil.net.in/tender/pdf/26c1186.pdf"),
            ("Volume II Financial Bid & BOQ", "https://www.tcil.net.in/tender/pdf/26c1186_1.pdf"),
            ("Central Public Procurement Portal", "https://etenders.gov.in/eprocure/app")
        ],
        "completeness": {
            "Tender/NIT": ("Yes", "Yes", "Yes"),
            "Architectural drawings": ("Yes", "Yes", "Yes"),
            "Structural drawings": ("Partial", "Yes", "Post-award GFC required"),
            "Civil specifications": ("Yes", "Yes", "Yes"),
            "BOQ quantities": ("Yes", "Yes", "Validation only"),
            "Cost/rates": ("Yes", "Yes", "Validation only"),
            "Time schedule": ("Yes", "Yes", "Validation only"),
            "Soil/geotech": ("No", "No", "Optional but valuable"),
            "Execution actuals": ("No", "No", "Optional but valuable")
        }
    },
    "DFCCIL-Sarmatanr-Larabad-Koderma-Quarters": {
        "project_name": "Construction of Railway Staff Quarters with Electrification in Various Stations namely Sarmatanr, Larabad & Koderma of Dhanbad Division of East Central Railway",
        "tender_reference": "KKK-EN-QTR-DHN-I-PH-I / KKK-EN-QTR-DHN-I-PH-I-R",
        "package": "Multiple Stations (Sarmatanr, Larabad, Koderma): Type-II (G+2 & G+0), Type-III (G+0), Type-IV (G+0), Deep Boring & Electrification",
        "authority": "Dedicated Freight Corridor Corporation of India Limited (DFCCIL) / Kolkata Unit",
        "official_status": "Official (dfccil.com / ireps.gov.in)",
        "date": "2022-2025",
        "building_scope": "Railway Staff Quarters (Type-II/III/IV) at 3 Stations",
        "classification": "Reference only",
        "classification_desc": "Useful railway housing package (Full 197-page tender doc, 50-page IREPS BOQ & specs; drawings available only at DFCCIL Kolkata unit)",
        "sources": [
            ("DFCCIL Official Portal", "https://dfccil.com"),
            ("Advertised NIT & BOQ", "https://dfccil.com/upload/NIT_for_KKK_EN_QTR_DHN_I_PH_I_I4PB.pdf"),
            ("Master Tender Document", "https://dfccil.com/upload/Tender_Document_Quarter_KQR_HZB_RJ3Y.pdf"),
            ("Koderma Balance Work Tender", "https://dfccil.com/upload/Tender_document_DHN_I_ZDV9.pdf"),
            ("IREPS Portal", "https://www.ireps.gov.in")
        ],
        "completeness": {
            "Tender/NIT": ("Yes", "Yes", "Yes"),
            "Architectural drawings": ("No", "Yes", "Requires physical visit to DFCCIL Kolkata"),
            "Structural drawings": ("No", "Yes", "Requires physical visit to DFCCIL Kolkata"),
            "Civil specifications": ("Yes", "Yes", "Yes"),
            "BOQ quantities": ("Yes", "Yes", "Validation only"),
            "Cost/rates": ("Yes", "Yes", "Validation only"),
            "Time schedule": ("Yes", "Yes", "Validation only"),
            "Soil/geotech": ("No", "No", "Optional but valuable"),
            "Execution actuals": ("Yes", "Yes", "Optional but valuable")
        }
    },
    "MHDC-PMAY-Khairi-Kamptee-Nagpur": {
        "project_name": "Construction of Affordable Housing Project of 1444 LIG Tenements Under PMAY(U) at Khairi, Kamptee, Nagpur (Package-1)",
        "tender_reference": "MHDC/Maha Housing/PMAY/Khairi-Kamptee/Package-1/2023 (Tender ID: 38842646)",
        "package": "Package-1 (6 High-Rise Towers G+14 Floors, 1444 LIG Tenements, 46,800 m2 Plot, Allied Infrastructure)",
        "authority": "Maharashtra Housing Development Corporation Limited (MHDC / Maha Housing)",
        "official_status": "Official (mahahousing.mahaonline.gov.in / mahatenders.gov.in)",
        "date": "2023-2024",
        "building_scope": "1444 LIG Tenements across 6 Towers (G+14 Floors) + Allied Infrastructure",
        "classification": "Silver",
        "classification_desc": "Useful high-rise affordable housing package (Complete 283-page Volume I tender with full area statements, Schedule C specs & payment schedule)",
        "sources": [
            ("MHDC Official Portal", "https://mahahousing.mahaonline.gov.in"),
            ("Volume I Master Tender Document", "https://mahahousing.mahaonline.gov.in/Upload/PDF/VolumeIK-P1.pdf"),
            ("Mahatenders Portal", "https://mahatenders.gov.in")
        ],
        "completeness": {
            "Tender/NIT": ("Yes", "Yes", "Yes"),
            "Architectural drawings": ("Yes", "Yes", "Yes"),
            "Structural drawings": ("Partial", "Yes", "Post-award GFC required based on Chapter 4 design criteria"),
            "Civil specifications": ("Yes", "Yes", "Yes"),
            "BOQ quantities": ("Yes", "Yes", "Validation only"),
            "Cost/rates": ("Yes", "Yes", "Validation only"),
            "Time schedule": ("Yes", "Yes", "Validation only"),
            "Soil/geotech": ("No", "No", "Optional but valuable"),
            "Execution actuals": ("No", "No", "Optional but valuable")
        }
    },
    "SBI-GIFT-City-Twin-Towers": {
        "project_name": "Composite Construction Works for Proposed Construction of Residential Twin Towers at Block No 41, GIFT City, Gandhinagar",
        "tender_reference": "SBI/GNR/26-27/02 (Revised Corrigendum); Original: SBI/GNR/25-26/03",
        "package": "Twin Towers (3 Basements + Ground + 25/26 Floors), 51,588 m2 Construction Area, 96-Car Puzzle Parking, Diaphragm Wall",
        "authority": "State Bank of India (SBI) - Local Head Office, GIFT City, Gandhinagar",
        "official_status": "Official (sbi.bank.in / tenderwizard.com)",
        "date": "2025-2026",
        "building_scope": "Residential Twin Towers (3B+G+25/26 Floors), 22,472 m2 BUA, 51,588 m2 Construction Area",
        "classification": "Silver",
        "classification_desc": "High-rise luxury twin tower package (Full 681-page Technical Bid, 162-page Price Bid BOQ, Google Drive drawings, diaphragm wall details)",
        "sources": [
            ("SBI Procurement News", "https://sbi.bank.in/web/sbi-in-the-news/procurement-news"),
            ("Technical Bid Document", "https://sbi.bank.in/documents/39129/57554832/SBI-GNR-26-27-02_Technical_Bid.pdf/1f124249-0b61-b36b-fae8-df6a319a103e?t=1775479317882"),
            ("Pre-Bid Clarifications & Drawing Links", "https://sbi.bank.in/documents/39129/44054854/TT.+-+Reply+of+Pre-Bid+dated+12.01.26+&+Reqd.+Docs..pdf/aff25b1b-e10f-8727-532f-111dbf6b1ea7?t=1768825997515"),
            ("Revised Price Bid / BOQ", "https://sbi.bank.in/documents/39129/57554832/Revised_Price_Bid(SBI-GNR-26-27-02).pdf/47cefb02-bf56-a4c8-fd59-cef4e4f9276c?t=1777381223893"),
            ("Architectural Drawings Repository", "https://drive.google.com/drive/folders/1-dJkPVTwNNXJMZWjMMk6Wa3tmlQ9wzCH?usp=sharing")
        ],
        "completeness": {
            "Tender/NIT": ("Yes", "Yes", "Yes"),
            "Architectural drawings": ("Yes", "Yes", "Yes"),
            "Structural drawings": ("Partial", "Yes", "Diaphragm wall drawings & raft details in tender/drive; detailed GFC post-award"),
            "Civil specifications": ("Yes", "Yes", "Yes"),
            "BOQ quantities": ("Yes", "Yes", "Validation only"),
            "Cost/rates": ("Yes", "Yes", "Validation only"),
            "Time schedule": ("Yes", "Yes", "Validation only"),
            "Soil/geotech": ("No", "No", "Geotechnical investigation report provided directly to finalized contractor per Pre-Bid Item 58"),
            "Execution actuals": ("No", "No", "Optional but valuable")
        }
    },
    "Paras-Dews-Sector-106-Gurugram": {
        "project_name": "Paras Dews Group Housing Scheme (6 High-Rise Towers 2B+G+23 Floors), Sector 106, Dwarka Expressway, Gurugram",
        "tender_reference": "HARERA Reg. No. 118 OF 2017 / RERA-GRG-439-2019 (Project ID: 1043)",
        "package": "6 High-Rise Residential Towers (2B+G+23), 724 Units, Clubhouse, 13.762 Acres",
        "authority": "Haryana Real Estate Regulatory Authority (HARERA) / Sepset Properties (Paras Buildtech)",
        "official_status": "Official (haryanarera.gov.in / parasbuildtech.com)",
        "date": "2017-2023",
        "building_scope": "6 Towers (2B+G+23 Floors), 724 Homes, 73,115 m2 RERA Carpet, 13.76 Acres",
        "classification": "Reference only",
        "classification_desc": "Useful private high-rise benchmark (Official RERA Form A-H filing, 812 Cr project outlay, 272.56 Cr construction cost, master brochure & floor plans)",
        "sources": [
            ("Haryana RERA Project Preview", "https://haryanarera.gov.in/view_project/project_preview_open/1043"),
            ("Haryana RERA Project Search", "https://haryanarera.gov.in/view_project/searchprojectDetail/1043"),
            ("Paras Buildtech Official", "https://parasbuildtech.com/property/paras-dews/"),
            ("Paras Dews Master Brochure", "https://www.propertyxpo.com/paras-dews/assets/download/brochure.pdf")
        ],
        "completeness": {
            "Tender/NIT": ("No", "No", "Private residential project - governed by RERA registration Form A-H"),
            "Architectural drawings": ("Partial", "Yes", "Site plan, location plan & floor plans in brochure; approved DTCP drawings in RERA filing"),
            "Structural drawings": ("No", "No", "RCC framed Zone IV structure specifications; detailed drawings not public"),
            "Civil specifications": ("Yes", "Yes", "Yes"),
            "BOQ quantities": ("No", "No", "Private project without public itemized BOQ"),
            "Cost/rates": ("Yes", "Yes", "Validation only"),
            "Time schedule": ("No", "No", "Completed project with Occupancy Certificate uploaded 04-08-2023"),
            "Soil/geotech": ("No", "No", "Not in public domain"),
            "Execution actuals": ("Partial", "Yes", "RERA approved status and Occupancy Certificate issued August 2023")
        }
    },
    "Haryana-RERA-Multi-Tower-Residential-Projects": {
        "project_name": "Various RERA-Registered Multi-Tower Residential Projects (Haryana RERA Benchmark Examples)",
        "tender_reference": "Multiple (HARERA Gurugram / Panchkula Form REP-I & Form A-H Filings)",
        "package": "Multi-Tower Schemes (G+10 to G+25 Floors, 1-9 Towers, 60-724+ Units, Gurugram / NCR)",
        "authority": "Haryana Real Estate Regulatory Authority (HARERA)",
        "official_status": "Official (haryanarera.gov.in)",
        "date": "2017-2025",
        "building_scope": "Multi-Tower High-Rise Residential Schemes (G+10 to G+25), 60-724 Units per Project",
        "classification": "Reference only",
        "classification_desc": "Multi-project private high-rise benchmark (5 official Form A-H filings, cross-project cost takeoff matrix, statutory framework & NBC-2016 MEP specs)",
        "sources": [
            ("Haryana RERA Official Portal", "https://haryanarera.gov.in"),
            ("HARERA Registered Projects Portal", "https://haryanarera.gov.in/admincontrol/registered_projects/2"),
            ("Ramprastha Edge Towers Form A-H (ID: 1058)", "https://haryanarera.gov.in/view_project/project_preview_open/1058"),
            ("Ansal Fernhill Phase 1 Form A-H (ID: 1411)", "https://haryanarera.gov.in/view_project/project_preview_open/1411"),
            ("Suncity Vatsal Valley Form A-H (ID: 1740)", "https://haryanarera.gov.in/view_project/project_preview_open/1740"),
            ("DLF City Phase I & III Form A-H (ID: 1861)", "https://haryanarera.gov.in/view_project/project_preview_open/1861"),
            ("Lion Infradevelopers Sohna Form A-H (ID: 1868)", "https://haryanarera.gov.in/view_project/project_preview_open/1868")
        ],
        "completeness": {
            "Tender/NIT": ("No", "No", "Private residential projects - governed by statutory RERA Form A-H filings"),
            "Architectural drawings": ("Partial", "Yes", "Site layout, zoning, and unit configurations in Form A-H & developer brochures"),
            "Structural drawings": ("No", "No", "Seismic Zone IV RCC shear wall specifications; working drawings confidential"),
            "Civil specifications": ("Yes", "Yes", "Yes"),
            "BOQ quantities": ("No", "No", "Private real estate projects without public itemized contractor BOQs"),
            "Cost/rates": ("Yes", "Yes", "Validation only"),
            "Time schedule": ("Partial", "Yes", "Quarter-by-quarter Form A-H expenditure and milestone delivery dates"),
            "Soil/geotech": ("No", "No", "Not in public domain"),
            "Execution actuals": ("Partial", "Yes", "Quarterly Progress Reports (QPR) and Occupancy Certificate (OC) filings")
        }
    },
    "WB-RERA-Multi-Tower-Residential-Projects": {
        "project_name": "WB RERA Multi-Tower Residential Projects (TKD Series and Other Private Developer Projects)",
        "tender_reference": "Multiple (WBRERA / HIRA ProCode & Registration Numbers)",
        "package": "Multi-Tower Schemes (G+4 to G+15 Floors, 1-7 Towers, 20-200 Units, Kolkata / New Town / Asansol)",
        "authority": "West Bengal Real Estate Regulatory Authority (WBRERA / HIRA)",
        "official_status": "Official (rera.wb.gov.in)",
        "date": "2019-2025",
        "building_scope": "1-7 Towers (G+4 to G+15 Floors), 20-200 Units per Project, 0.2-5.0 Acres",
        "classification": "Reference only",
        "classification_desc": "Useful private multi-tower benchmark (Sanctioned plans, typical floor plates, elevation sheets, TKD structural series & promoter financials)",
        "sources": [
            ("WBRERA Official Portal", "https://rera.wb.gov.in"),
            ("Tarang Towers 6 & 7 (ProCode: 15391000000026)", "https://rera.wb.gov.in/project_details.php?procode=15391000000026"),
            ("Greenwood Nest (ProCode: 12137000000000)", "https://rera.wb.gov.in/project_details_hira.php?procode=12137000000000"),
            ("JKN Tower (ProCode: 12753000000052)", "https://rera.wb.gov.in/project_details.php?procode=12753000000052"),
            ("West Bengal Real Estate Rules", "https://rera.wb.gov.in/img/pdf/West-Bengal-Real-Estate-Rules.pdf")
        ],
        "completeness": {
            "Tender/NIT": ("No", "No", "Private residential projects - no public tender documents via WBRERA"),
            "Architectural drawings": ("Yes", "Yes", "Sanctioned building plans, floor plans, elevation plans & master plans downloadable"),
            "Structural drawings": ("Partial", "Yes", "Structural foundation & column framing drawings available for some projects (e.g. JKN Tower, TKD series)"),
            "Civil specifications": ("Partial", "Yes", "Structural specifications & pile foundation parameters available in filings"),
            "BOQ quantities": ("No", "No", "Private projects without public itemized contractor BOQs"),
            "Cost/rates": ("Partial", "Yes", "Declared project costs in promoter audited filings; no public unit rates"),
            "Time schedule": ("Partial", "Yes", "Project completion target dates declared in statutory filings"),
            "Soil/geotech": ("No", "No", "Not in public domain"),
            "Execution actuals": ("Partial", "Yes", "WBRERA registration status, municipal CC and handover milestones")
        }
    },
    "UP-RERA-Residential-Towers-Floor-Plans": {
        "project_name": "UP RERA Residential Towers (Floor Plans of All Types), Private Developers, Uttar Pradesh",
        "tender_reference": "Multiple (UP RERA Project IDs: 8898, 8888, 9315, 2218, 17537, 7723, 10840)",
        "package": "Multi-Tower Schemes (G+4 to G+27 Floors, 1-10 Towers, 50-500 Units, NOIDA / Greater Noida / Lucknow)",
        "authority": "Uttar Pradesh Real Estate Regulatory Authority (UP RERA)",
        "official_status": "Official (up-rera.in)",
        "date": "2017-2025",
        "building_scope": "1-10 Towers (G+4 to G+27 Floors), 50-500 Units per Project, 0.5-10.0 Acres",
        "classification": "Reference only",
        "classification_desc": "Useful private high-rise benchmark (Floor Plans of All Types, typical 1-8/1-17/1-27 floor sequences, approved layout maps & promoter specifications)",
        "sources": [
            ("UP RERA Official Portal", "https://up-rera.in"),
            ("Himalaya Pride Phase 3 Tower D (ID: 8898)", "https://up-rera.in/Frm_View_Project_Details.aspx?id=8898"),
            ("M3M The Cullinan BBA & Plans (Ref: PRJ9315)", "https://up-rera.in/ViewDocument?Param=PRJ931562964M3M2_BBA.pdf"),
            ("UP RERA Project Registration Manual", "https://www.up-rera.in/pdf/Project-Registration-User-Manual.pdf"),
            ("Uttar Pradesh Real Estate Rules", "https://up-rera.in/pdf/rera.pdf")
        ],
        "completeness": {
            "Tender/NIT": ("No", "No", "Private residential projects - no public tender documents via UP RERA"),
            "Architectural drawings": ("Yes", "Yes", "Floor Plans of All Types, typical floor plans (1-8, 1-17, 1-27 floors) & approved layout maps"),
            "Structural drawings": ("No", "No", "Structural drawings not consistently available via UP RERA portal"),
            "Civil specifications": ("Yes", "Yes", "Technical and material specifications on promoter letterhead officially uploaded"),
            "BOQ quantities": ("No", "No", "Private projects without public itemized contractor BOQs"),
            "Cost/rates": ("Partial", "Yes", "Total project cost certified by CA in Form REG-3; no public BOQ unit rates"),
            "Time schedule": ("Partial", "Yes", "Proposed and revised completion target dates declared in portal filings"),
            "Soil/geotech": ("No", "No", "Not in public domain"),
            "Execution actuals": ("Partial", "Yes", "UP RERA registration status, QPR tracking and authority OC milestones")
        }
    },
    "Purvanchal-Sunbliss-Sector-22D-Yamuna-Expressway": {
        "project_name": "Purvanchal Sunbliss (7 Residential Blocks + 1 Community Center), Sector 22D, Yamuna Expressway, Greater Noida, UP",
        "tender_reference": "UPRERAPRJ746863/04/2025 (Project ID: PRJ746863)",
        "package": "7 High-Rise Blocks (6 Residential + 1 Commercial/Studio) + 1 Community Center (~70,000 sq.ft.), 1,112 Units, 10.478 Acres",
        "authority": "Uttar Pradesh Real Estate Regulatory Authority (UP RERA) / YEIDA / Purvanchal Projects Pvt. Ltd.",
        "official_status": "Official (up-rera.in / yamunaexpresswayauthority.com)",
        "date": "2024-2030",
        "building_scope": "7 Towers (2B+G+18 to 2B+G+24 Floors, 1,112 Units) + 1 Community Clubhouse on 42,406 m2 (10.478 Acres)",
        "classification": "Reference only",
        "classification_desc": "Useful private high-rise benchmark (Official RERA registration UPRERAPRJ746863/04/2025, 767.31 Cr CA certificate, parent lease deed, MIVAN formwork & Schedule D specs)",
        "sources": [
            ("UP RERA Official Portal", "https://up-rera.in"),
            ("UP RERA Project Summary", "https://www.up-rera.in/Projectsummary?UI0aPA1ISD=xR+wyQ0QrY4=&hfFlag=9emr4VdBw22M7BGjKtJWMPDI4s5cHQZP&NPJ6RAme=Oq4WtnhfFzTXEiqh0qQW8/Vn1+0WJAKd8UDJQSWO763Eud1LcQC2p0iIZorH6SkBpOKqurRu4VQ=&PaURJEMAN4=ZL9MNERkNdZt8EFRNGdqs9nU3sH6FbM7&IRSAHEB=D6PY3lyims8="),
            ("Official CA Statutory Certificate", "https://up-rera.in/ViewDocument?Param=PRJ461451357Sunbliss-20-03-2025_CA_Certificate_DS.pdf"),
            ("Proforma Allotment Letter", "https://up-rera.in/ViewDocument?Param=PRJ211451357Allotment_250325_FINALUPLOAD.pdf"),
            ("Agreement for Sale & Schedule D Specifications", "https://up-rera.in/ViewDocument?Param=PRJ301451357Sunbliss_ATS_FINALUpload_250325.pdf")
        ],
        "completeness": {
            "Tender/NIT": ("No", "No", "Private residential project - governed by YEIDA lease deed & UP RERA registration"),
            "Architectural drawings": ("Partial", "Yes", "Site master layout, floor sequences up to 24th floor, unit plans A1-A5 & clubhouse program"),
            "Structural drawings": ("No", "No", "RCC framed Seismic Zone IV MIVAN monolithic shear wall specifications; GFC drawings confidential"),
            "Civil specifications": ("Yes", "Yes", "Yes"),
            "BOQ quantities": ("No", "No", "Private project without public itemized contractor tender BOQ"),
            "Cost/rates": ("Yes", "Yes", "Validation only"),
            "Time schedule": ("Yes", "Yes", "Validation only"),
            "Soil/geotech": ("No", "No", "Not in public domain"),
            "Execution actuals": ("Partial", "Yes", "RERA registration granted 08-04-2025, 13.14% expenditure absorbed, possession date 29-01-2030")
        }
    },
    "IIT-Hyderabad-Faculty-Housing": {
        "project_name": "Construction of Precast 2 Nos. Faculty Housing (G+12), 3 Nos. Staff Housing (G+12) and 3 Nos. Hostel Blocks (G+6) RCC Structures at IIT Hyderabad",
        "tender_reference": "NIT No. IITH/CMD/CIVIL/NIT/2022-23/09",
        "package": "8 Precast RCC Buildings (2 Faculty G+12 + 3 Staff G+12 + 3 Hostels G+6), Turnkey EPC Mode, HEFA Loan Funded",
        "authority": "Indian Institute of Technology Hyderabad (IITH) / Construction & Maintenance Division",
        "official_status": "Official (iith.ac.in / eprocure.gov.in)",
        "date": "2022-2025",
        "building_scope": "8 Precast Buildings (5 Towers G+12 + 3 Blocks G+6) at Permanent Campus Kandi Sangareddy",
        "classification": "Gold",
        "classification_desc": "Ready for end-to-end prototype (Full 6-volume EPC tender pack, concept architectural drawings, subsoil geotechnical report, civil/MEP specs & 254.65 Cr BoG contract award)",
        "sources": [
            ("IIT Hyderabad Tenders Portal", "https://iith.ac.in/tenders/"),
            ("Volume 01 Notice Inviting Tender & SCC", "https://www.iith.ac.in/assets/files/tenders/volume_01_notice_inviting_tender_special_conditions_of_contract.pdf"),
            ("Volume 02b Payment Schedule Annexure", "https://www.iith.ac.in/assets/files/tenders/volume_02_b_payment_schedule_annexure.pdf"),
            ("Volume 03 Technical Specs Civil Works", "https://www.iith.ac.in/assets/files/tenders/volume_03_technical_specs_civil_works.pdf"),
            ("Volume 04 Technical Specs E&M Components", "https://www.iith.ac.in/assets/files/tenders/volume_04_scope_tech_specs_em_components.pdf"),
            ("Volume 05 Concept Drawings & Subsoil Report", "https://www.iith.ac.in/assets/files/tenders/volume_05_concept_drawings_subsoil_report.pdf"),
            ("Volume 06 General Conditions EPC", "https://www.iith.ac.in/assets/files/tenders/volume_06_general_conditions_epc.pdf"),
            ("41st BoG Meeting Minutes (Contract Award)", "https://www.iith.ac.in/assets/files/pdf/BoG_MoM/IITH%2041st%20BoG%20Meeting%20Minutes-Revised.pdf"),
            ("Central Public Procurement Portal", "https://eprocure.gov.in/eprocure/app")
        ],
        "completeness": {
            "Tender/NIT": ("Yes", "Yes", "Yes"),
            "Architectural drawings": ("Yes", "Yes", "Yes"),
            "Structural drawings": ("Yes", "Yes", "Yes"),
            "Civil specifications": ("Yes", "Yes", "Yes"),
            "BOQ quantities": ("Yes", "Yes", "Validation only"),
            "Cost/rates": ("Yes", "Yes", "Validation only"),
            "Time schedule": ("Yes", "Yes", "Validation only"),
            "Soil/geotech": ("Yes", "Yes", "Optional but valuable"),
            "Execution actuals": ("Yes", "Yes", "Optional but valuable")
        }
    },
    "MHADA-Goregaon-LIG-MIG-HIG-Tenements": {
        "project_name": "Construction of LIG/MIG/HIG Residential Tenements at Siddharth Nagar, Goregaon, Mumbai",
        "tender_reference": "TN-EE-Goregaon-MB-30_8_2024-en / MHADA/EE/Goregaon/MB/2024",
        "package": "Lump-sum Turnkey (EPC): 4 Plots (R1, R4, R-7/A2, R-13), 3.055 Million Sq.ft Construction Area, ₹1,355.95 Cr Total Outlay",
        "authority": "Mumbai Housing and Area Development Board (MHADA)",
        "official_status": "Official (mhada.gov.in / mahatenders.gov.in)",
        "date": "2024-2028",
        "building_scope": "LIG/MIG/HIG High-Rise Towers (Stilt+20 to Stilt+21 Floors) across 4 Plots in Siddharth Nagar Goregaon",
        "classification": "Silver",
        "classification_desc": "Useful turnkey high-rise package (Master NIT PDF TN-EE-Goregaon-MB-30_8_2024-en, plot-wise area & cost schedules, engineering specifications; drawings are post-award deliverables)",
        "sources": [
            ("MHADA Official Portal", "https://mhada.gov.in"),
            ("Official Master E-Tender Notice PDF", "https://www.mhada.gov.in/sites/default/files/TN-EE-Goregaon-MB-30_8_2024-en.pdf"),
            ("Government of Maharashtra e-Tenders", "https://mahatenders.gov.in")
        ],
        "completeness": {
            "Tender/NIT": ("Yes", "Yes", "Yes"),
            "Architectural drawings": ("No", "Yes", "Post-award deliverable under turnkey EPC scope"),
            "Structural drawings": ("No", "Yes", "Post-award deliverable under turnkey EPC scope"),
            "Civil specifications": ("Yes", "Yes", "Yes"),
            "BOQ quantities": ("Yes", "Yes", "Validation only"),
            "Cost/rates": ("Yes", "Yes", "Validation only"),
            "Time schedule": ("Yes", "Yes", "Validation only"),
            "Soil/geotech": ("Partial", "Yes", "Turnkey scope mandates site soil investigation by contractor"),
            "Execution actuals": ("No", "No", "Optional but valuable")
        }
    },
    "CPWD-BSF-Roopnagar-63-Quarters": {
        "project_name": "Construction of 63 Nos. Residential Quarters at BSF Campus Roopnagar (Structural Design Consultancy)",
        "tender_reference": "NIT No. 28/EE/SILIGURI/CPWD/2025-26",
        "package": "Structural Design Consultancy: 48 Nos. Type-II (S+8) + 15 Nos. Type-III (S+5) Quarters at BSF Roopnagar",
        "authority": "Central Public Works Department (CPWD), Siliguri Central Division / Border Security Force (BSF)",
        "official_status": "Official (cpwd.gov.in / eprocure.gov.in)",
        "date": "2025-2026",
        "building_scope": "63 Residential Quarters: 48 Units Type-II (Stilt+8) + 15 Units Type-III (Stilt+5) at BSF Roopnagar Campus",
        "classification": "Reference only",
        "classification_desc": "Useful design consultancy benchmark (46-page NIT, Schedule A BOQ, CPWD Form 7, DBR criteria; architectural plans restricted under Clause 1.6; structural drawings are deliverables)",
        "sources": [
            ("CPWD Official Portal", "https://cpwd.gov.in"),
            ("Central Public Procurement Portal", "https://eprocure.gov.in/eprocure/app"),
            ("CPWD Plinth Area Rates (PAR)", "https://www.cpwd.gov.in/newsitem/latestnewspdf/PAR2010R.pdf"),
            ("Scribd Verified NIT Document", "https://www.scribd.com/document/939412569/Roopnagar-Str-NIT")
        ],
        "completeness": {
            "Tender/NIT": ("Yes", "Yes", "Yes"),
            "Architectural drawings": ("No", "Yes", "Clause 1.6 restricted reference only; available departmentally to awarded consultant"),
            "Structural drawings": ("No", "Yes", "Deliverable output to be created by consultant, not an input"),
            "Civil specifications": ("Yes", "Yes", "Yes"),
            "BOQ quantities": ("Partial", "Yes", "Structural design consultancy quantities in Schedule A BOQ"),
            "Cost/rates": ("Yes", "Yes", "Validation only"),
            "Time schedule": ("Yes", "Yes", "Validation only"),
            "Soil/geotech": ("No", "No", "Not included in public bid document"),
            "Execution actuals": ("No", "No", "Optional but valuable")
        }
    },
    "CPWD-EPFO-Borivali-301-Quarters": {
        "project_name": "Redevelopment of EPFO Campus at Borivali, Mumbai (Planning, Designing & Construction of 301 Residential Quarters)",
        "tender_reference": "NIT No. 64/EE/Mumbai-IV/02/CE/Mumbai-II/2025-26",
        "package": "EPC Mode-I: 301 Quarters (3B+GF+3P+35 Floors Tower + G+4 Building), ₹337.06 Cr Outlay",
        "authority": "Central Public Works Department (CPWD), Mumbai-IV Division / EPFO",
        "official_status": "Official (cpwd.gov.in / eprocure.gov.in)",
        "date": "2025-2028",
        "building_scope": "301 Quarters in 3B+GF+3P+35 Floors Tower + G+4 Guest House at EPFO Borivali Campus",
        "classification": "Reference only",
        "classification_desc": "Useful high-rise EPC benchmark (₹337.06 Cr outlay, 35-storey skyscraper + G+4 building, 32-month timeline, diaphragm wall; architectural/structural drawings restricted to registered bidders)",
        "sources": [
            ("CPWD Official Portal", "https://cpwd.gov.in"),
            ("Central Public Procurement Portal", "https://eprocure.gov.in/eprocure/app"),
            ("CPWD Plinth Area Rates (PAR)", "https://www.cpwd.gov.in/newsitem/latestnewspdf/PAR2010R.pdf"),
            ("Scribd Verified Tender Overview", "https://www.scribd.com/document/939412569/EPFO-Borivali-NIT-Overview")
        ],
        "completeness": {
            "Tender/NIT": ("Yes", "Yes", "Yes"),
            "Architectural drawings": ("No", "Yes", "Restricted to fee-paying registered bidders under CPWD EPC tender terms"),
            "Structural drawings": ("No", "Yes", "Restricted to fee-paying registered bidders under CPWD EPC tender terms"),
            "Civil specifications": ("Yes", "Yes", "Yes"),
            "BOQ quantities": ("Partial", "Yes", "Summary milestone milestones & PAR schedule; detailed itemized rates restricted"),
            "Cost/rates": ("Yes", "Yes", "Validation only"),
            "Time schedule": ("Yes", "Yes", "Validation only"),
            "Soil/geotech": ("No", "No", "Geotechnical investigation to be performed post-award under EPC terms"),
            "Execution actuals": ("No", "No", "Optional but valuable")
        }
    },
    "AIIMS-Delhi-150-Units-Staff-Quarters": {
        "project_name": "Construction of G+12 Staff Quarters (150 Units) at AIIMS Delhi [UNVERIFIED / REJECTED CANDIDATE]",
        "tender_reference": "Not Publicly Available (No Record Found)",
        "package": "G+12 Staff Quarters (150 Units), Type-II/III/IV Mix, AIIMS Ansari Nagar Campus, New Delhi",
        "authority": "Central Public Works Department (CPWD) / AIIMS New Delhi",
        "official_status": "Reject / Unverified (No public tender documents found)",
        "date": "2026-09-16 (Search Date)",
        "building_scope": "150 Units: G+12 Storey Residential Blocks (Type-II/III/IV Mix) - NOT FOUND",
        "classification": "Reject",
        "classification_desc": "No Public Documents Found: Exhaustive search across AIIMS tender portals, CPPP, and CPWD identified no public tender document, NIT, BOQ, or drawing set for 150-unit G+12 quarters at AIIMS Delhi. Available tenders pertain to hospital blocks, maintenance, or external campuses.",
        "sources": [
            ("AIIMS Delhi Tender Portal", "https://www.aiims.edu/index.php/en/tenders"),
            ("CPPP Tender Portal", "https://eprocure.gov.in"),
            ("CPWD General Specifications", "https://pwd.py.gov.in/cpwd-specifications-vol-1-2019"),
            ("CPWD Residential Planning Manual", "https://cpwd.gov.in/Publication/Compendium_for_Design_of_Central_Government_Housing.pdf"),
            ("AIIMS Rishikesh Reference NIT", "https://www.scribd.com/document/963271708/NIT02"),
            ("AIIMS Delhi Critical Care Hospital Tender", "https://www.tendershark.com/details/delhi-tender/central-public-works-department/eaafae31-9f7e-4486-afd6-31f7afa33a37")
        ],
        "completeness": {
            "Tender/NIT": ("No", "N/A", "No public tender found"),
            "Architectural drawings": ("No", "N/A", "No public architectural drawings found"),
            "Structural drawings": ("No", "N/A", "No public structural drawings found"),
            "Civil specifications": ("Yes", "No", "General CPWD specifications only; not project-specific"),
            "BOQ quantities": ("No", "N/A", "No public BOQ found"),
            "Cost/rates": ("No", "N/A", "No public cost/rates found"),
            "Time schedule": ("No", "N/A", "No public time schedule found"),
            "Soil/geotech": ("No", "N/A", "No geotechnical report found"),
            "Execution actuals": ("No", "N/A", "No execution actuals found")
        }
    }
}

def standardize_all():
    summary = []
    for p_name, meta in PROJECT_METADATA.items():
        p_path = os.path.join(BASE_DIR, p_name)
        os.makedirs(p_path, exist_ok=True)

        # 1. Ensure the canonical 10 subdirectories exist
        for d in STANDARD_DIRS:
            sub_p = os.path.join(p_path, d)
            os.makedirs(sub_p, exist_ok=True)
            keep = os.path.join(sub_p, ".gitkeep")
            if not os.path.exists(keep) and len(os.listdir(sub_p)) == 0:
                with open(keep, "w") as f:
                    pass

        # 2. Build 12-column file_manifest.csv
        manifest_rows = []
        for d in STANDARD_DIRS:
            sub_p = os.path.join(p_path, d)
            for root, dirs, files in os.walk(sub_p):
                for f in sorted(files):
                    if f in [".gitkeep", "file_manifest.csv", "README.md"]:
                        continue
                    full_f = os.path.join(root, f)
                    sz = os.path.getsize(full_f)
                    
                    if meta.get("classification") == "Reject":
                        verified = "No"
                        notes = f"Size: {sz:,} bytes | Rejection audit / unverified candidate reference"
                    else:
                        verified = "Yes" if d != "99_Unverified_or_Related_References" else "Uncertain"
                        notes = f"Size: {sz:,} bytes"
                        if d == "99_Unverified_or_Related_References":
                            notes += " | Reference / Unverified / Benchmark charter"
                    
                    manifest_rows.append({
                        "Project name": meta["project_name"],
                        "Tender reference": meta["tender_reference"],
                        "Package": meta["package"],
                        "Document category": d,
                        "File name": f,
                        "Source URL": meta["sources"][0][1] if meta["sources"] else "Official Portal",
                        "Source authority": meta["authority"],
                        "Official/public status": meta["official_status"],
                        "Date": meta["date"],
                        "Building scope": meta["building_scope"],
                        "Verified match": verified,
                        "Notes": notes
                    })

        csv_path = os.path.join(p_path, "file_manifest.csv")
        fieldnames = [
            "Project name", "Tender reference", "Package", "Document category",
            "File name", "Source URL", "Source authority", "Official/public status",
            "Date", "Building scope", "Verified match", "Notes"
        ]
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(manifest_rows)

        # 3. Build Standardized README.md
        readme_path = os.path.join(p_path, "README.md")
        lines = []
        lines.append(f"# {meta['project_name']}\n")
        lines.append("## 1. Project Identity & Source Verification\n")
        lines.append(f"- **Official Project Title:** {meta['project_name']}")
        lines.append(f"- **Tender Reference / ID:** `{meta['tender_reference']}`")
        lines.append(f"- **Client / Authority:** {meta['authority']}")
        lines.append(f"- **Target Building Scope:** {meta['building_scope']}")
        lines.append(f"- **Document Date / Period:** {meta['date']}")
        lines.append(f"- **Verification Status:** {meta['official_status']}\n")
        
        lines.append("### Official Public Sources & Download Links")
        for s_name, s_url in meta["sources"]:
            lines.append(f"- **{s_name}:** [{s_url}]({s_url})")
        lines.append("")

        lines.append("## 2. Completeness Table (Same-Project Verification)\n")
        lines.append("| Category | Present | Verified same project | Suitable for model |")
        lines.append("| :--- | :---: | :---: | :---: |")
        for cat_name in [
            "Tender/NIT",
            "Architectural drawings",
            "Structural drawings",
            "Civil specifications",
            "BOQ quantities",
            "Cost/rates",
            "Time schedule",
            "Soil/geotech",
            "Execution actuals"
        ]:
            p_val, v_val, s_val = meta["completeness"].get(cat_name, ("No", "No", "No"))
            lines.append(f"| {cat_name} | {p_val} | {v_val} | {s_val} |")
        lines.append("")

        lines.append("## 3. Project Classification\n")
        lines.append(f"### **Classification: {meta['classification']}**")
        lines.append(f"*{meta['classification_desc']}*\n")

        lines.append("## 4. Standard Directory Hierarchy\n")
        lines.append("```text")
        lines.append(f"{p_name}/")
        lines.append("│")
        for d in STANDARD_DIRS:
            lines.append(f"├── {d}/")
        lines.append("├── file_manifest.csv")
        lines.append("└── README.md")
        lines.append("```\n")

        lines.append("## 5. Dataset Files & Catalog\n")
        lines.append(f"Total cataloged items: **{len(manifest_rows)} entries**. See [`file_manifest.csv`](file_manifest.csv) for full provenance.\n")

        with open(readme_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        summary.append({
            "folder": p_name,
            "classification": meta["classification"],
            "records": len(manifest_rows)
        })
        print(f"[{p_name}] Standardized -> Classification: {meta['classification']} ({len(manifest_rows)} records)")

    # 4. Update Root Hub README.md
    root_readme = os.path.join(BASE_DIR, "README.md")
    root_lines = [
        "# DataRequirement — Same-Project Construction Intelligence Datasets Hub\n",
        "Central repository hub organizing major Indian government, PSU, and institutional residential construction tender packages for quantity estimation, material estimation, cost modeling, and duration prediction.\n",
        "Every project strictly adheres to the canonical 10-subdirectory taxonomy, 12-column manifest schema, and same-project verification rules.\n",
        "## 🏗️ Active Project Repositories\n",
        "| # | Project Repository | Authority / Client | Classification | Scope / Typology | Completeness | Manifest Records |",
        "| :-: | :--- | :--- | :---: | :--- | :---: | :---: |"
    ]
    for idx, s in enumerate(summary, start=1):
        m = PROJECT_METADATA[s["folder"]]
        folder_url = urllib.parse.quote(f"{BASE_DIR.replace(os.sep, '/')}/{s['folder']}", safe=":/")
        root_lines.append(f"| {idx} | [`{s['folder']}`](file:///{folder_url}) | {m['authority']} | **{s['classification']}** | {m['building_scope']} | {m['classification']} | {s['records']} files |")
    
    root_lines.append("\n---\n")
    root_lines.append("## 📁 Standard Project Architecture\n")
    root_lines.append("```text\nProject-Name/\n│\n├── 00_Core_Intelligence_Dataset/\n├── 01_Tender_NIT_PreBid/\n├── 02_Cost_BOQ_Makes/\n├── 03_Technical_Specifications_Reports/\n├── 04_Architectural_Drawings/\n├── 05_Structural_Drawings/\n├── 06_MEP_Services/\n├── 07_Landscape_Infrastructure/\n├── 08_Execution_Actuals/\n├── 99_Unverified_or_Related_References/\n├── file_manifest.csv\n└── README.md\n```\n")
    
    with open(root_readme, "w", encoding="utf-8") as f:
        f.write("\n".join(root_lines))
    print("\nRoot README.md successfully updated!")

if __name__ == "__main__":
    standardize_all()
