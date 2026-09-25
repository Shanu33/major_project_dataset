import csv
import os

out_dir = "11_Estimation_Readiness/v2_verified_release"
os.makedirs(out_dir, exist_ok=True)

# -------------------------------------------------------------
# TASK B: OPENING SCHEDULE RECONCILIATION
# -------------------------------------------------------------
opening_rec_file = os.path.join(out_dir, "opening_schedule_reconciliation.csv")
opening_headers = [
    "opening_type",
    "drawing_confirmed_dimensions",
    "older_file_dimensions",
    "conflict_status",
    "controlling_source",
    "corrective_action",
    "impact_on_prior_calculations"
]

opening_rows = [
    [
        "D1 (Toilet Flush Door)",
        "800 x 2100 mm (Width: 800 mm, Height: 2100 mm, Sill: 0 mm)",
        "1000 x 2100 mm (calculated_quantities_high_confidence.csv line 10 & architectural_quantity_readiness.csv line 9)",
        "CONFLICT_DISCREPANCY_DETECTED",
        "04_Architectural_Drawings/Tender_drawing_1_SitePlan_GroundFloor_pdf-2025-Aug-28-17-38-39.pdf (Sheet RITES/BLD/AR/TD/005 p.9 'SCHEDULE OF DOORS' item 1: D1 800x2100; Sheet AR/TD/014 p.18)",
        "Older prototype file marked SUPERSEDED for opening dimensions. Controlling drawing specification of 800x2100mm enforced across all v2 registers.",
        "Single door area is 1.680 sq.m (not 2.100 sq.m; -0.420 sq.m/door variance). Across 48 toilet doors in the single tower, total opening area is 80.640 sq.m (not 100.800 sq.m). Prior masonry deductions based on 1000x2100 over-deducted toilet partition wall openings by 20.160 sq.m, erroneously understating toilet masonry volume by 2.318 m3."
    ],
    [
        "D2 (Bedroom & Internal Door)",
        "1000 x 2100 mm (Width: 1000 mm, Height: 2100 mm, Sill: 0 mm)",
        "900 x 2100 mm (calculated_quantities_high_confidence.csv line 10 & architectural_quantity_readiness.csv line 9)",
        "CONFLICT_DISCREPANCY_DETECTED",
        "04_Architectural_Drawings/Tender_drawing_1_SitePlan_GroundFloor_pdf-2025-Aug-28-17-38-39.pdf (Sheet RITES/BLD/AR/TD/005 p.9 'SCHEDULE OF DOORS' item 2: D2 1000x2100; Sheet AR/TD/014 p.18)",
        "Older prototype file marked SUPERSEDED for opening dimensions. Controlling drawing specification of 1000x2100mm enforced across all v2 registers.",
        "Single door area is 2.100 sq.m (not 1.890 sq.m; +0.210 sq.m/door variance). Across 96 bedroom/internal doors in the tower, total opening area is 201.600 sq.m (not 181.440 sq.m). Prior masonry deductions based on 900x2100 under-deducted partition openings by 20.160 sq.m, erroneously overstating internal partition masonry volume by 2.318 m3."
    ],
    [
        "D3 (Main Entrance Door)",
        "1050 x 2100 mm (Width: 1050 mm, Height: 2100 mm, Sill: 0 mm)",
        "750 x 2100 mm (calculated_quantities_high_confidence.csv line 10 & architectural_quantity_readiness.csv line 9)",
        "CONFLICT_DISCREPANCY_DETECTED",
        "04_Architectural_Drawings/Tender_drawing_1_SitePlan_GroundFloor_pdf-2025-Aug-28-17-38-39.pdf (Sheet RITES/BLD/AR/TD/005 p.9 'SCHEDULE OF DOORS' item 3: D3 1050x2100; Sheet AR/TD/014 p.18)",
        "Older prototype file marked SUPERSEDED for opening dimensions. Controlling drawing specification of 1050x2100mm enforced across all v2 registers.",
        "Single door area is 2.205 sq.m (not 1.575 sq.m; +0.630 sq.m/door variance). Across 72 entrance doors in the tower, total opening area is 158.760 sq.m (not 113.400 sq.m). Prior masonry deductions based on 750x2100 severely under-deducted entrance wall openings by 45.360 sq.m, erroneously overstating 230mm corridor masonry by 10.433 m3."
    ],
    [
        "DW1 (Living Room Balcony Combo)",
        "2000 x 2100 mm (Width: 2000 mm, Height: 2100 mm, Area: 4.200 sq.m)",
        "NOT_LISTED (Omitted from older calculated_quantities_high_confidence.csv door table)",
        "OMISSION_IN_LEGACY_PROTOTYPE",
        "04_Architectural_Drawings/Tender_drawing_1_SitePlan_GroundFloor_pdf-2025-Aug-28-17-38-39.pdf (Sheet AR/TD/005 p.9 & Sheet AR/TD/014)",
        "Direct observation cataloged in v2 register as combination opening. Not counted in 216 flush door total.",
        "Omission in legacy files prevented bay-wise external wall opening deduction, forcing reliance on synthetic 23% gross external wall deduction ratio (ASM-007)."
    ],
    [
        "DW2 (Living Room Balcony Alternate Combo)",
        "2295 x 2100 mm (Width: 2295 mm, Height: 2100 mm, Area: 4.820 sq.m)",
        "NOT_LISTED (Omitted from older calculated_quantities_high_confidence.csv door table)",
        "OMISSION_IN_LEGACY_PROTOTYPE",
        "04_Architectural_Drawings/Tender_drawing_1_SitePlan_GroundFloor_pdf-2025-Aug-28-17-38-39.pdf (Sheet AR/TD/005 p.9 & Sheet AR/TD/014)",
        "Direct observation cataloged in v2 register as combination opening. Not counted in 216 flush door total.",
        "Omission in legacy files contributed to blocking deterministic external wall deduction modeling."
    ],
    [
        "SD1 (Electrical Shaft Door)",
        "900 x 2100 mm (Width: 900 mm, Height: 2100 mm, Sill: 100 mm, Area: 1.890 sq.m)",
        "NOT_LISTED (Omitted from older door schedule summary)",
        "OMISSION_IN_LEGACY_PROTOTYPE",
        "04_Architectural_Drawings/Tender_drawing_1_SitePlan_GroundFloor_pdf-2025-Aug-28-17-38-39.pdf (Sheet AR/TD/005 p.9 & Sheet AR/TD/014)",
        "Cataloged in v2 register under service doors; excluded from residential flush door total.",
        "Shaft opening deductions were unapplied in legacy shaft wall takeoff."
    ],
    [
        "SD2 (Plumbing / Service Shaft Door)",
        "600 x 2100 mm per Sheet 005 schedule (600 x 2000 mm on Sheet 015 detail; Sill: 100 mm)",
        "NOT_LISTED (Omitted from older door schedule summary)",
        "CROSS_SHEET_DISCREPANCY_AND_LEGACY_OMISSION",
        "04_Architectural_Drawings/Tender_drawing_1_SitePlan_GroundFloor_pdf-2025-Aug-28-17-38-39.pdf (Sheet AR/TD/005 p.9 vs Sheet AR/TD/015 p.19)",
        "Cataloged in v2 register with cross-sheet variance noted; schedule height 2100mm retained as primary baseline.",
        "Variance of 0.06 sq.m/door affects plumbing shaft wall opening deduction."
    ],
    [
        "SD3 (Fire Hose Cabinet Shaft Door)",
        "900 x 2100 mm (Width: 900 mm, Height: 2100 mm, Sill: 100 mm, Area: 1.890 sq.m)",
        "NOT_LISTED (Omitted from older door schedule summary)",
        "OMISSION_IN_LEGACY_PROTOTYPE",
        "04_Architectural_Drawings/Tender_drawing_1_SitePlan_GroundFloor_pdf-2025-Aug-28-17-38-39.pdf (Sheet AR/TD/005 p.9 & Sheet AR/TD/014)",
        "Cataloged in v2 register under service doors; excluded from residential flush door total.",
        "Corridor wall masonry deductions require shaft door integration."
    ],
    [
        "SD4 (Mumty / Plant Room Door)",
        "1200 x 2100 mm (Width: 1200 mm, Height: 2100 mm, Sill: 100 mm, Area: 2.520 sq.m)",
        "NOT_LISTED (Omitted from older door schedule summary)",
        "OMISSION_IN_LEGACY_PROTOTYPE",
        "04_Architectural_Drawings/Tender_drawing_1_SitePlan_GroundFloor_pdf-2025-Aug-28-17-38-39.pdf (Sheet AR/TD/005 p.9 & Sheet AR/TD/014)",
        "Cataloged in v2 register under service doors; excluded from residential flush door total.",
        "Mumty perimeter wall deduction requires SD4 integration."
    ],
    [
        "W1 (Bedroom Window)",
        "1200 x 1200 mm (Width: 1200 mm, Height: 1200 mm, Sill: 900 mm, Lintel: 2100 mm)",
        "1200 x 1200 mm",
        "CONCORDANT",
        "04_Architectural_Drawings/Tender_drawing_1_SitePlan_GroundFloor_pdf-2025-Aug-28-17-38-39.pdf (Sheet AR/TD/005 p.9 & Sheet AR/TD/014)",
        "Direct observation retained in v2 register. Count = 48 nos.",
        "Opening area 1.440 sq.m confirmed."
    ],
    [
        "W2 (Kitchen Window)",
        "1000 x 1225 mm per Sheet 005 schedule (1000 x 1500 mm on Sheet 015 detail; Sill: 1225 mm)",
        "1000 x 1225 mm",
        "CROSS_SHEET_DISCREPANCY_NOTED",
        "04_Architectural_Drawings/Tender_drawing_1_SitePlan_GroundFloor_pdf-2025-Aug-28-17-38-39.pdf (Sheet AR/TD/005 p.9 vs Sheet AR/TD/015 p.19)",
        "Schedule size 1000x1225mm retained as controlling baseline; 1000x1500mm detail noted for reconciliation.",
        "Area variance 1.225 sq.m vs 1.500 sq.m across 24 units (+6.60 sq.m opening area impact)."
    ],
    [
        "W3 (Staircase Well Window)",
        "2300 x 1100 mm (Width: 2300 mm, Height: 1100 mm, Sill: 1000 mm, Lintel: 2100 mm)",
        "2300 x 1100 mm",
        "CONCORDANT",
        "04_Architectural_Drawings/Tender_drawing_1_SitePlan_GroundFloor_pdf-2025-Aug-28-17-38-39.pdf (Sheet AR/TD/005 p.9 & Sheet AR/TD/015)",
        "Direct observation retained in v2 register. Count = 24 nos.",
        "Opening area 2.530 sq.m confirmed."
    ],
    [
        "W4 (Secondary Bedroom Window)",
        "1200 x 1200 mm (Width: 1200 mm, Height: 1200 mm, Sill: 900 mm, Lintel: 2100 mm)",
        "1200 x 1200 mm",
        "CONCORDANT",
        "04_Architectural_Drawings/Tender_drawing_1_SitePlan_GroundFloor_pdf-2025-Aug-28-17-38-39.pdf (Sheet AR/TD/005 p.9 & Sheet AR/TD/015)",
        "Direct observation retained in v2 register. Count = 24 nos.",
        "Opening area 1.440 sq.m confirmed."
    ],
    [
        "V1 (Attached Toilet Ventilator)",
        "515 x 875 mm (Width: 515 mm, Height: 875 mm, Sill: 1225 mm, Lintel: 2100 mm)",
        "515 x 875 mm",
        "CONCORDANT",
        "04_Architectural_Drawings/Tender_drawing_1_SitePlan_GroundFloor_pdf-2025-Aug-28-17-38-39.pdf (Sheet AR/TD/005 p.9 & Sheet AR/TD/014)",
        "Direct observation retained in v2 register. Count = 24 nos.",
        "Opening area 0.451 sq.m confirmed."
    ],
    [
        "V2 (Common Toilet Ventilator)",
        "615 x 875 mm (Width: 615 mm, Height: 875 mm, Sill: 1225 mm, Lintel: 2100 mm)",
        "615 x 875 mm",
        "CONCORDANT",
        "04_Architectural_Drawings/Tender_drawing_1_SitePlan_GroundFloor_pdf-2025-Aug-28-17-38-39.pdf (Sheet AR/TD/005 p.9 & Sheet AR/TD/015)",
        "Direct observation retained in v2 register. Count = 24 nos.",
        "Opening area 0.538 sq.m confirmed."
    ]
]

with open(opening_rec_file, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(opening_headers)
    w.writerows(opening_rows)

print(f"Wrote {len(opening_rows)} rows to {opening_rec_file}")


# -------------------------------------------------------------
# TASK C: LEGACY MODEL QUARANTINE REGISTER
# -------------------------------------------------------------
quarantine_file = os.path.join(out_dir, "legacy_model_quarantine_register.csv")
quarantine_headers = [
    "quarantine_id",
    "source_file",
    "element_or_work_package",
    "reported_quantity",
    "reported_unit",
    "reported_gang_productivity",
    "reported_mandays_or_duration",
    "source_classification",
    "use_for_training",
    "use_for_ground_truth",
    "reason_for_quarantine",
    "governing_prohibition_and_remediation"
]

quarantine_rows = [
    [
        "QRN-LBR-001",
        "06_Labour_and_Duration/labour_estimate.csv (line 2)",
        "Piling Foundation (207 piles)",
        "207.00", "piles", "2.5 piles/rig-day", "580 mandays (83 days / 2 rigs -> 42 days)",
        "LEGACY_UNVALIDATED", "NO", "NO",
        "Missing approved BBS, unresolved pile termination depth (18m DBR assumption), unvalidated material quantities, and no contractor productivity logs.",
        "Prohibited from use in ML training or deterministic scheduling. Remediation requires contractor approved borehole pile termination depth chart and rig log records."
    ],
    [
        "QRN-LBR-002",
        "06_Labour_and_Duration/labour_estimate.csv (line 3)",
        "Substructure Concrete & Caps",
        "293.06", "m3", "25 m3/day", "117 mandays (12 days)",
        "LEGACY_UNVALIDATED", "NO", "NO",
        "Unresolved foundation schedule conflict (54 layout entities vs 84 summary caps, 23.38 m3 variance), unallocated strip caps, unvalidated material quantities, and arbitrary gang productivity.",
        "Prohibited from training use. Remediation requires approved pile cap GA drawing with numbered cap marks and pour sequencing plan."
    ],
    [
        "QRN-LBR-003",
        "06_Labour_and_Duration/labour_estimate.csv (line 4)",
        "Plinth Beams & Grade Slab",
        "108.06", "m3", "20 m3/day", "54 mandays (6 days)",
        "LEGACY_UNVALIDATED", "NO", "NO",
        "Gross grid centerline includes column nodes; grade slab includes unmeasured 5.70 m3 edge thickening; no contractor productivity logs; unvalidated material quantities.",
        "Prohibited from training use. Remediation requires clear bay-by-bay plinth beam spans and perimeter grade slab detailing."
    ],
    [
        "QRN-LBR-004",
        "06_Labour_and_Duration/labour_estimate.csv (line 5)",
        "Substructure Reinforcement",
        "128.74", "MT", "250 kg/pair-day", "1030 mandays (65 days)",
        "LEGACY_UNVALIDATED", "NO", "NO",
        "Complete absence of approved contractor BBS; rebar steel derived from parametric intensities (94.2 kg/m3 for piles, 110 kg/m3 for caps); no contractor bar bender gang logs.",
        "Prohibited from training use. Remediation requires structural engineering BBS per IS 2502 detailing cut lengths, hooks, and laps."
    ],
    [
        "QRN-LBR-005",
        "06_Labour_and_Duration/labour_estimate.csv (line 6)",
        "Superstructure Columns & Walls",
        "482.19", "m3", "20 m3/day", "241 mandays (25 days)",
        "LEGACY_UNVALIDATED", "NO", "NO",
        "Member height is architectural-section derived; beam-column joint intersections not deduplicated; unvalidated material quantities; arbitrary gang productivities.",
        "Prohibited from training use. Remediation requires structural column elevations and concrete pump log verification."
    ],
    [
        "QRN-LBR-006",
        "06_Labour_and_Duration/labour_estimate.csv (line 7)",
        "Superstructure Beams & Slabs",
        "745.71", "m3", "30 m3/day", "249 mandays (25 days)",
        "LEGACY_UNVALIDATED", "NO", "NO",
        "Gross beam grid length (403.5m) includes column nodes; slab thickness 130mm is assumed average; monolithic joint duplication; unvalidated material quantities.",
        "Prohibited from training use. Remediation requires member-wise beam clear spans and slab panel clear boundaries."
    ],
    [
        "QRN-LBR-007",
        "06_Labour_and_Duration/labour_estimate.csv (line 8)",
        "Superstructure Reinforcement",
        "172.11", "MT", "250 kg/pair-day", "1377 mandays (69 days)",
        "LEGACY_UNVALIDATED", "NO", "NO",
        "Missing approved contractor BBS; beam rebar relies on 140 kg/m3 and slab on 89.17 kg/m3; Seismic Zone V ductile link complexities unmodeled.",
        "Prohibited from training use. Remediation requires official fabricator BBS with shape codes, hook dimensions, and lap schedules."
    ],
    [
        "QRN-LBR-008",
        "06_Labour_and_Duration/labour_estimate.csv (line 9)",
        "Superstructure Shuttering",
        "9160.00", "sq.m", "15 sq.m/pair-day", "1221 mandays (76 days)",
        "LEGACY_UNVALIDATED", "NO", "NO",
        "Formwork contact area calculated using gross parametric multipliers without bay-by-bay beam soffit or drop details; unvalidated material quantities.",
        "Prohibited from training use. Remediation requires shop formwork layout and cycling schedule."
    ],
    [
        "QRN-LBR-009",
        "06_Labour_and_Duration/labour_estimate.csv (line 10)",
        "Brick Masonry (230mm & 115mm)",
        "623.65", "m3", "1.25 m3/gang-day", "1247 mandays (78 days)",
        "LEGACY_UNVALIDATED", "NO", "NO",
        "Relies on gross room perimeters without deducting concrete columns and beams; uses synthetic opening deduction ratios (ASM-007: 23%, ASM-008: 10%); no site mason gang logs.",
        "Prohibited from training use. Remediation requires dimensioned wall centerline layout plan with structural block-outs."
    ],
    [
        "QRN-LBR-010",
        "06_Labour_and_Duration/labour_estimate.csv (line 11)",
        "Internal & External Plastering",
        "14850.00", "sq.m", "9.0 sq.m/pair-day", "3300 mandays (138 days)",
        "LEGACY_UNVALIDATED", "NO", "NO",
        "Derived from gross surface area ratio (ASM-009); 4-face elevation envelopes and beam soffit drop schedules missing; arbitrary gang productivity rates.",
        "Prohibited from training use. Remediation requires architectural elevation envelope and bay-by-bay plaster surface schedule."
    ],
    [
        "QRN-LBR-011",
        "06_Labour_and_Duration/labour_estimate.csv (line 12)",
        "Flooring Tiling & Stone Work",
        "3803.60", "sq.m", "8.0 sq.m/pair-day", "951 mandays (79 days)",
        "LEGACY_UNVALIDATED", "NO", "NO",
        "Total area includes unverified corridor multipliers; carpet area approximations; no contractor tile layer gang logs.",
        "Prohibited from training use. Remediation requires flat-by-flat room finishes schedule and corridor bay layout."
    ],
    [
        "QRN-LBR-012",
        "06_Labour_and_Duration/labour_estimate.csv (line 13)",
        "Internal & External Painting",
        "15700.00", "sq.m", "35 sq.m/day", "673 mandays (67 days)",
        "LEGACY_UNVALIDATED", "NO", "NO",
        "Derived indirectly from gross plaster area; trade-specific schedules missing; arbitrary painter gang productivity.",
        "Prohibited from training use. Remediation requires paint finish schedule and elevation facade areas."
    ],
    [
        "QRN-LBR-013",
        "06_Labour_and_Duration/labour_estimate.csv (line 14)",
        "Terrace Waterproofing",
        "483.60", "sq.m", "20 sq.m/pair-day", "48 mandays (12 days)",
        "LEGACY_UNVALIDATED", "NO", "NO",
        "Parapet upstands, rainwater coving, and Mumty roof detailing omitted; arbitrary gang productivity.",
        "Prohibited from training use. Remediation requires waterproofing sectional details and approved applicator methodology."
    ],
    [
        "QRN-LBR-014",
        "06_Labour_and_Duration/labour_estimate.csv (line 15)",
        "Doors Windows & Railings",
        "420.00", "assemblies", "4 units/day", "210 mandays (35 days)",
        "LEGACY_UNVALIDATED", "NO", "NO",
        "Assembly count aggregates mismatched door schedules and unverified railing lengths; arbitrary carpenter/fitter productivities.",
        "Prohibited from training use. Remediation requires reconciled opening schedule and balcony railing shop drawings."
    ],
    [
        "QRN-LBR-015",
        "06_Labour_and_Duration/labour_estimate.csv (line 16)",
        "TOTAL SINGLE TOWER LABOUR (PRELIMINARY)",
        "NOT_APPLICABLE", "mandays", "Various unverified gang rates", "11298 mandays (Peak 65-80 workers)",
        "LEGACY_UNVALIDATED", "NO", "NO",
        "Aggregate sum of ungrounded parametric labour line items; violates core governance prohibiting labour estimation on unresolved foundation and absent BBS.",
        "Strictly quarantined. Total labour mandays must remain locked as NOT_CALCULATED until all primary engineering prerequisites are satisfied."
    ],
    [
        "QRN-DUR-001",
        "06_Labour_and_Duration/duration_estimate.csv (line 2)",
        "Full Contract Package (8 Towers + GH + CS + Infrastructure)",
        "8 Towers + Ancillary Buildings + External Works", "campus scope", "24 Months (720 Days)", "24 Months (720 Days)",
        "PROJECT_LEVEL_CONTRACTUAL_FACT", "NO", "NO",
        "Official contract period awarded to M/s Badri Rai & Company (RITES Status Dec 2025: Rs 128.14 Cr excl GST, 24 months). Applies strictly to the multi-building campus as a whole.",
        "Prohibit conversion of the 24-month whole-complex duration into a tower duration via arithmetic division (e.g. 24/8 = 3 months or concurrent 24 months). Does not represent isolated single-tower duration."
    ],
    [
        "QRN-DUR-002",
        "06_Labour_and_Duration/duration_estimate.csv (line 3)",
        "Single Isolated Typical Housing Tower",
        "1 Typical Stilt+6 Residential Tower", "single tower scope", "NOT_CALCULATED", "NOT_CALCULATED",
        "ISOLATED_TOWER_UNMODULATION", "NO", "NO",
        "Single tower independent construction duration has NOT been calculated. No critical path model has been run. Foundation schedule is contradictory and no contractor baseline programme exists.",
        "Must remain locked as NOT_CALCULATED. Prohibit synthetic milestone generation or duration modeling until approved Primavera P6 / CPM contractor programme is recovered."
    ]
]

with open(quarantine_file, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(quarantine_headers)
    w.writerows(quarantine_rows)

print(f"Wrote {len(quarantine_rows)} rows to {quarantine_file}")


# -------------------------------------------------------------
# TASK D: REPRIORITIZED EVIDENCE REQUEST REGISTER V2
# -------------------------------------------------------------
req_v2_file = os.path.join(out_dir, "missing_evidence_request_register_v2.csv")
req_v2_headers = [
    "request_id",
    "missing_document",
    "responsible_organization",
    "exact_technical_question",
    "affected_quantities_trades",
    "current_confidence_impact",
    "what_it_will_unblock",
    "acceptance_criteria",
    "priority",
    "recommended_acquisition_method"
]

req_v2_rows = [
    [
        "REQ-V2-001",
        "Approved Pile Termination / Founding-Level & Tabulated Pile Schedule",
        "EPC Contractor (M/s Badri Rai & Co.) / Project Geotechnical Consultant / RITES Supervising Engineer",
        "What is the approved design termination depth, founding stratum reduced level (RL), cut-off elevation, and pile cage detailing for each of the 207 bored cast-in-situ piles under the typical residential tower?",
        "Substructure Piling Concrete (1,053.49 m3), Pile Reinforcement Steel (99.24 MT), Foundation Excavation/Boring Mandays, Rig Cycle Times",
        "Severe. Forces reliance on a generic DBR range (15m to 20m, midpoint 18.0m, ASM-001). A ±2.5m depth variance across the site alters concrete volume by up to ±146.3 m3 (±14%) and substructure steel by ±13.8 MT.",
        "Converts pile concrete and steel from ESTIMATED to deterministic engineering calculation; establishes binding substructure quantity baseline; unblocks piling duration modeling.",
        "Signed structural substructure drawing or tabulated schedule detailing individual pile coordinates, ground level, cut-off level, toe level, socketing depth, and rebar lap locations.",
        "Priority 1",
        "Formal Contractor RFI / Engineer-in-Charge Technical Submission retrieval from RITES NERPO project archives."
    ],
    [
        "REQ-V2-002",
        "Approved Pile-Cap General Arrangement & Tabulated Pile-Cap Schedule",
        "EPC Contractor (M/s Badri Rai & Co.) / EPC Structural Design Consultant / RITES NERPO",
        "How is the critical contradiction between the 54 cap entities visible on Sheet STR/TD/101 and the 84 caps reported in the preliminary summary resolved, and what are the exact boundary dimensions (L x W x D) and pile allocations for the 91 piles located under continuous strip caps?",
        "Foundation Pile Cap Concrete Volume (185.00 to 208.38 m3), Pile Cap Reinforcement Steel (20.35 MT), Shuttering Areas, Excavation Pit Volumes",
        "Critical Unresolved Contradiction. Substructure concrete volume has an irreconcilable variance of 23.38 m3; cap thickness is ambiguous (750mm marked on plan vs 1000mm assumed in preliminary models, ASM-003); 91 piles remain unallocated.",
        "Resolves foundation structural contradiction; establishes deterministic cap volume and formwork contact area; unblocks substructure concrete pour and shuttering cycle time modeling.",
        "Approved foundation GA drawing showing numbered cap marks (PC-1 to PC-n, strip caps PC-W), tabulated schedule of dimensions, verified depth for every cap type, and complete 207-pile allocation map.",
        "Priority 1",
        "Formal Technical Clarification to RITES Tender Cell-NERPO / Badri Rai & Co. Engineering Office."
    ],
    [
        "REQ-V2-003",
        "Approved Contractor Bar Bending Schedules (BBS) & Structural Shop Drawings",
        "EPC Contractor (M/s Badri Rai & Co.) / Approved Rebar Fabricator / RITES Supervising Engineer",
        "What are the approved member-by-member bar marks, bar diameters, shape codes, bending dimensions, cut lengths, hook lengths, and lap splice staggering locations per IS 2502 and IS 13920:2016 for all structural members (Columns C1-C3, Shear walls SW1-SW10, Plinth beams PB1-PB34, Floor beams B1-B34, Terrace beams TB1-TB34, Slabs S1-S2, Stairs, and OHT)?",
        "All Structural Reinforcement Steel (Columns: 52.41 MT, Walls: 30.12 MT, Beams: 53.76 MT, Slabs: 36.69 MT, Piles: 99.24 MT, Caps: 20.35 MT, Total: 300.85 MT), Bar Bending Labour Mandays",
        "Critical Blocker across all structural steel. All current rebar weights rely on crude parametric intensities (89.17 to 140 kg/m3) or formula-based lap approximations (50d rule), producing errors of 20% to 30% in high-ductility Seismic Zone V rebar. Labour mandays for bar benders cannot be calculated deterministically without cut and bend counts.",
        "Converts 300.85 MT of estimated steel into shop-verifiable physical quantities; eliminates parametric steel assumptions; unblocks deterministic rebar fixing productivity and labour manday calculations.",
        "Approved Bar Bending Schedule (BBS) spreadsheets and rebar shop drawings signed by RITES Engineer-in-Charge, conforming to IS 2502.",
        "Priority 1",
        "Contractor Technical Submittal retrieval from Site Engineering Office (Duliajan BQ Site)."
    ],
    [
        "REQ-V2-004",
        "Member-Wise Beam & Slab Schedule with Clear Spans and Joint Deduplication Guidelines",
        "EPC Structural Design Consultant / EPC Contractor (M/s Badri Rai & Co.) / RITES NERPO",
        "What are the individual clear spans (excluding column and shear wall head nodes) for each of the 108 beam segments per floor, and what are the net panel clear areas and thickness variations for floor slabs S1 and S2 (excluding monolithic 230mm beam web ribs)?",
        "Plinth Beam Concrete (47.61 m3), Floor Beam Concrete (289.80 m3), Terrace Beam Concrete (48.30 m3), Suspended Slab Concrete (386.71 m3), Slab/Beam Formwork Shuttering Areas",
        "High. Gross grid centerline length (403.5m) and uniform 130mm slab thickness double-count concrete at beam-column joint intersections (49 vertical elements) and beam-slab ribs, inflating structural framing concrete by 8% to 12% and distorting floor cycle times.",
        "Eliminates joint duplication; establishes net member volumes; yields true shuttering contact surface areas for accurate cycle-time and formwork reuse modeling.",
        "Structural general arrangement drawings with bay-by-bay clear span schedules, member cross-sections, and panel-by-panel slab layouts with void/core coordinates.",
        "Priority 2",
        "Project Design Consultant structural calculation submittal / CAD engineering model extract."
    ],
    [
        "REQ-V2-005",
        "Room-Wise Architectural Finish Schedule & Dimensioned Wall Centerline Layout Plan",
        "Project Architectural Consultant / EPC Contractor (M/s Badri Rai & Co.) / OIL Civil Engineering Dept",
        "What are the exact room-by-room clear dimensions, wall centerline lengths subtracting structural columns and shear wall panels, bay-by-bay clear wall heights under beam soffits, and trade-wise finish specifications for all floors and corridors?",
        "External 230mm Brick Masonry (216.80 m3), Internal 115mm Brick Masonry (406.85 m3), Cement Plaster (14,850 sq.m), Flooring & Skirting (2,700 sq.m), Mason/Plasterer Labour Mandays",
        "High. Current masonry calculations rely on synthetic opening deduction ratios (ASM-007: 23%, ASM-008: 10%) and gross perimeters, overestimating masonry volume by up to 15-20% by double-counting concrete members; plaster and paint quantities lack elevation envelopes; finishes labour cannot be modeled.",
        "Replaces synthetic deduction percentages with exact CAD geometry; establishes precise plaster/flooring areas; unblocks masonry and plastering labour estimations.",
        "Dimensioned architectural working drawings showing wall centerlines with column block-outs, lintel/sill levels, room finish schedule table, and gross 4-face elevation surface areas.",
        "Priority 2",
        "Architectural Working Drawings release from RITES/OIL project office."
    ],
    [
        "REQ-V2-006",
        "Approved Contractor Baseline Construction Master Programme (Primavera P6 / MS Project)",
        "EPC Contractor (M/s Badri Rai & Co.) / Project Management Consultant (RITES NERPO)",
        "What is the approved single-tower critical path schedule, activity logic network, sequence of structural pours, floor cycle time (days per floor), and gang productivity records for the typical residential tower under Assam monsoon site conditions?",
        "Single Tower Construction Duration (currently NOT_CALCULATED), Milestone Schedule, Peak/Average Labour Deployment, Equipment Rig Days",
        "High. Prevents duration modeling. The overall contract duration is 24 months for 8 towers + 4 ancillary buildings + campus infrastructure concurrently; converting 24 months into single-tower duration via pro-rata division is strictly prohibited.",
        "Establishes binding single-tower construction programme; reveals true critical path (piling vs structural frame); unblocks CPM duration modeling and crew leveling.",
        "Native Primavera P6 (.xer) or MS Project schedule file approved by RITES Engineer-in-Charge, showing activity-level WBS for Tower Block A (typical).",
        "Priority 2",
        "Contractor Planning Department baseline submittal retrieval."
    ],
    [
        "REQ-V2-007",
        "Overhead Water Tank (OHT) Structural Detailing & Reinforcement Drawing",
        "EPC Structural Design Consultant / EPC Contractor (M/s Badri Rai & Co.) / RITES NERPO",
        "What are the structural wall thickness, base slab thickness, roof slab details, water-stop construction joint layout, and IS 3370 water-retaining reinforcement detailing for the rooftop Overhead Water Tank?",
        "OHT Concrete Volume (16.50 m3), OHT Reinforcement Steel (1.98 MT), Water-retaining Waterproofing, Tank Formwork",
        "Moderate. Tank wall thickness is NOT visible on Sheet STR/TD/109 and wall rebar is NOT scheduled; estimating tank quantities currently relies on generic engineering code assumptions (ASM-010).",
        "Replaces code assumptions with approved structural geometry; completes roof-level structural framing takeoff.",
        "Structural detail sheet showing plan, cross-sections, wall thicknesses, and tabulated bar schedule for the rooftop OHT.",
        "Priority 2",
        "Structural Drawing addendum request."
    ],
    [
        "REQ-V2-008",
        "Approved Itemized EPC Cost Breakdown / Priced Bill of Quantities for Typical Housing Tower",
        "Oil India Limited (OIL) / RITES Limited (Tender Cell-NERPO) / Contractor Badri Rai & Co.",
        "What is the approved work package billing break-up and trade-wise price breakdown for a single typical Stilt+6 residential tower (BOQ Item 1.01 component of the INR 128.14 Cr contract award), including itemized rates for civil, structural, finishes, plumbing, and electrical works?",
        "Single Tower Capital Cost Validation, Unit Cost per sq.m Plinth Area, Trade Cost Distribution, Commercial Accuracy Assessment",
        "Commercial Blocker. Without an approved priced BOQ or work package cost breakdown, cost accuracy remains NOT CALCULATED. Pro-rata 1/8th division (INR 16.0175 Cr) is strictly a rough project-level benchmark that cannot be validated.",
        "Establishes binding cost ground truth; enables commercial accuracy calculations; unlocks automated cost estimating model validation against actual contract pricing.",
        "Contractor approved contract price breakdown schedule, billing schedule of payments, or detailed unit rate analysis approved by OIL/RITES.",
        "Priority 3",
        "Commercial & Contracts Division archive retrieval (OIL Duliajan / RITES NERPO Guwahati)."
    ]
]

with open(req_v2_file, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(req_v2_headers)
    w.writerows(req_v2_rows)

print(f"Wrote {len(req_v2_rows)} rows to {req_v2_file}")

