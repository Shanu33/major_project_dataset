import os
import sys
import csv
import json

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = r"c:\Users\shahnawaz khan\OneDrive\Documents\DataRequirement\OIL-RITES-Duliajan-BQ-Housing"

def write_csv(rel_path, headers, rows):
    full_path = os.path.join(BASE_DIR, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    print(f"Updated {rel_path} ({os.path.getsize(full_path)} bytes)")

def write_text(rel_path, content):
    full_path = os.path.join(BASE_DIR, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Updated {rel_path} ({os.path.getsize(full_path)} bytes)")

# 1. Update 03_Quantity_Takeoff/concrete_takeoff.csv
conc_headers = [
    "Item ID", "Structural Element", "Sub-Element Description", "Number of Elements",
    "Length (m)", "Width / Dia (m)", "Depth / Height (m)", "Gross Volume (m3)",
    "Deductions (m3)", "Net Concrete Volume (m3)", "Concrete Grade", "Drawing Reference",
    "Confidence Classification", "Audit Reconciliation & Contradiction Notes"
]
conc_rows = [
    ["CONC-001", "Substructure", "PCC under pile caps & plinth beams", "84 caps + trenches", "Various", "Various", "0.075", "18.00", "0.00", "18.00", "M10", "STR/TD/HOUSING(G+6)/101", "ESTIMATED", "Plan footprint under caps x 0.075m assumed thickness (ASM-003)"],
    ["CONC-002", "Substructure", "Bored cast-in-situ RCC piles", "207 piles", "18.00", "0.60 dia (area 0.2827)", "18.00", "1053.49", "0.00", "1053.49", "M30", "STR/TD/HOUSING(G+6)/100", "ESTIMATED", "207 piles counted; length 18m assumed per DBR range 15-20m (ASM-001)"],
    ["CONC-003", "Substructure", "RCC Pile Caps (Unresolved Count)", "54 layout vs 84 summary", "Various", "Various", "1.000", "185.00", "0.00", "185.00", "M30", "STR/TD/HOUSING(G+6)/101", "ASSUMPTION_REQUIRED", "CRITICAL CONTRADICTION: 54 caps in plan vs 84 in summary; depth 1.0m assumed (ASM-002)"],
    ["CONC-004", "Substructure", "Plinth Beams (PB1 to PB34)", "108 beam segments", "403.50", "0.230", "0.513 (avg)", "47.61", "0.00", "47.61", "M30", "STR/TD/HOUSING(G+6)/105", "ESTIMATED", "Reconciled to 403.5m grid run; weighted section assumed without member schedule"],
    ["CONC-005", "Substructure", "Stilt Grade Slab (GS1 & GS2)", "1 continuous slab", "30.08", "16.08", "0.125", "60.45", "0.00", "60.45", "M30", "STR/TD/HOUSING(G+6)/105", "ASSUMPTION_REQUIRED", "Uniform slab = 54.75 m3; 60.45 m3 requires assumed 5.70 m3 edge thickening"],
    ["CONC-006", "Superstructure", "Columns C1 (1200 x 350 mm)", "4 nos x 7 levels = 28", "1.20", "0.35", "3.00 (avg)", "35.28", "0.00", "35.28", "M30", "STR/TD/HOUSING(G+6)/104", "MEDIUM", "Cross section scheduled on Sheet 104; uses 3.0m clear height across 7 repeated levels"],
    ["CONC-007", "Superstructure", "Columns C2 (1200 x 300 mm)", "8 nos x 7 levels = 56", "1.20", "0.30", "3.00 (avg)", "60.48", "0.00", "60.48", "M30", "STR/TD/HOUSING(G+6)/104", "MEDIUM", "Cross section scheduled on Sheet 104; uses 3.0m clear height across 7 repeated levels"],
    ["CONC-008", "Superstructure", "Columns C3 (1200 x 300 mm)", "4 nos x 7 levels = 28", "1.20", "0.30", "3.00 (avg)", "30.24", "0.00", "30.24", "M30", "STR/TD/HOUSING(G+6)/104", "MEDIUM", "Cross section scheduled on Sheet 104; uses 3.0m clear height across 7 repeated levels"],
    ["CONC-009", "Superstructure", "Shear Walls SW1 (1260 x 230 mm)", "12 nos x 7 levels = 84", "1.26", "0.23", "3.00 (avg)", "73.03", "0.00", "73.03", "M30", "STR/TD/HOUSING(G+6)/104", "MEDIUM", "Cross section scheduled on Sheet 104; uses 3.0m clear height across 7 repeated levels"],
    ["CONC-010", "Superstructure", "Shear Walls SW2 (1500 x 230 mm)", "4 nos x 7 levels = 28", "1.50", "0.23", "3.00 (avg)", "28.98", "0.00", "28.98", "M30", "STR/TD/HOUSING(G+6)/104", "MEDIUM", "Cross section scheduled on Sheet 104; uses 3.0m clear height across 7 repeated levels"],
    ["CONC-011", "Superstructure", "Shear Walls SW3 (1380 x 230 mm)", "4 nos x 7 levels = 28", "1.38", "0.23", "3.00 (avg)", "26.66", "0.00", "26.66", "M30", "STR/TD/HOUSING(G+6)/104", "MEDIUM", "Cross section scheduled on Sheet 104; uses 3.0m clear height across 7 repeated levels"],
    ["CONC-012", "Superstructure", "Shear Walls SW4 (2925 x 230 mm)", "4 nos x 7 levels = 28", "2.925", "0.23", "3.00 (avg)", "56.51", "0.00", "56.51", "M30", "STR/TD/HOUSING(G+6)/104", "MEDIUM", "Cross section scheduled on Sheet 104; uses 3.0m clear height across 7 repeated levels"],
    ["CONC-013", "Superstructure", "Shear Walls SW5 (5030 x 230 mm)", "4 nos x 7 levels = 28", "5.030", "0.23", "3.00 (avg)", "97.18", "0.00", "97.18", "M30", "STR/TD/HOUSING(G+6)/104", "MEDIUM", "Cross section scheduled on Sheet 104; uses 3.0m clear height across 7 repeated levels"],
    ["CONC-014", "Superstructure", "Core Shear Walls SW6-SW10", "5 walls x 7 levels = 35", "13.89", "0.23", "3.00 (avg)", "67.09", "0.00", "67.09", "M30", "STR/TD/HOUSING(G+6)/104", "MEDIUM", "Run length scheduled on Sheet 104; uses 3.0m clear height across 7 repeated levels"],
    ["CONC-015", "Superstructure", "Mumty Columns & Pedestals", "8 nos", "0.30", "0.30", "2.70", "6.74", "0.00", "6.74", "M30", "STR/TD/HOUSING(G+6)/109", "MEDIUM", "Scheduled dimensions; minor pedestal volume estimated"],
    ["CONC-016", "Superstructure", "Floor Beams (Floors 1 to 6)", "648 spans (6 levels)", "2421.00", "0.230", "0.520 (avg)", "289.80", "0.00", "289.80", "M30", "STR/TD/HOUSING(G+6)/107", "ESTIMATED", "Reconciled to 403.5m length/floor; weighted section 0.1197 m2 and 6 repeated floors"],
    ["CONC-017", "Superstructure", "Terrace Beams (TB1 to TB34)", "108 spans (1 level)", "403.50", "0.230", "0.520 (avg)", "48.30", "0.00", "48.30", "M30", "STR/TD/HOUSING(G+6)/108", "ESTIMATED", "Reconciled to 403.5m length; weighted section assumed"],
    ["CONC-018", "Superstructure", "Suspended Floor Slabs (Floors 1-6)", "6 slabs", "30.08", "16.08", "0.130 (avg)", "331.47", "0.00", "331.47", "M30", "STR/TD/HOUSING(G+6)/107", "ESTIMATED", "Reconciled to 424.96 m2 net slab (483.60 - 58.64 voids) x 6 x 130mm weighted thickness"],
    ["CONC-019", "Superstructure", "Terrace Slab & Mumty Roof", "1 slab + mumty", "30.08", "16.08", "0.130 (avg)", "55.24", "0.00", "55.24", "M30", "STR/TD/HOUSING(G+6)/108", "ESTIMATED", "Reconciled to 424.96 m2 net slab x 130mm weighted thickness"],
    ["CONC-020", "Superstructure", "Balcony & Chajja Projections", "7 levels", "Various", "Various", "0.110 (avg)", "20.02", "0.00", "20.02", "M30", "STR/TD/HOUSING(G+6)/107", "ESTIMATED", "Exterior shading projections across 7 levels; unmeasured individual schedule"],
    ["CONC-021", "Superstructure", "Doglegged Staircases (2 cores)", "28 flights total", "Various", "Various", "Various", "26.60", "0.00", "26.60", "M30", "STR/TD/HOUSING(G+6)/110", "MEDIUM", "Flight geometry scheduled on Sheet 110; 28 flights repeated across 7 levels"],
    ["CONC-022", "Superstructure", "Mumty Parapet & Wall Bands", "1 unit", "35.20", "0.150", "1.90", "10.03", "0.00", "10.03", "M30", "STR/TD/HOUSING(G+6)/109", "MEDIUM", "Mumty enclosure dimensions scheduled on Sheet 109"],
    ["CONC-023", "Superstructure", "Overhead Water Tank (OHT)", "Twin tank unit", "Various", "Various", "Various", "16.50", "0.00", "16.50", "M30", "STR/TD/HOUSING(G+6)/109", "ASSUMPTION_REQUIRED", "Tank walls (150mm) and base (200mm) assumed without structural schedule (ASM-010)"]
]
write_csv("03_Quantity_Takeoff/concrete_takeoff.csv", conc_headers, conc_rows)

# 2. Update 07_Final_Prototype_Dataset/calculated_quantities.csv
calc_headers = [
    "Quantity ID", "Item Category", "Item Description", "Takeoff Value", "Unit",
    "Concrete Grade", "Steel Grade", "Engineering Intensity", "Source Drawing", "Confidence Classification"
]
calc_rows = [
    ["QTY-CONC-SUB", "Concrete", "Substructure RCC Concrete (Piles, Caps, Plinth Beams, Grade Slab)", "1346.55", "m3", "M30", "-", "0.394 m3/sq.m plinth", "STR/TD/100-106", "ESTIMATED_DOMINANT"],
    ["QTY-CONC-SUP", "Concrete", "Superstructure RCC Concrete (Columns, Walls, Beams, Slabs, Stairs, OHT)", "1271.00", "m3", "M30", "-", "0.372 m3/sq.m plinth", "STR/TD/103-110", "MEDIUM_DOMINANT"],
    ["QTY-CONC-TOT", "Concrete", "TOTAL RCC M30 CONCRETE (Substructure + Superstructure)", "2617.55", "m3", "M30", "-", "0.766 m3/sq.m plinth", "All Structural Sheets", "DRAWING_BASED_ESTIMATE"],
    ["QTY-CONC-PCC", "Concrete", "PCC Lean Concrete (1:5:10) under pile caps and plinth trenches", "18.00", "m3", "M10", "-", "-", "STR/TD/101", "ESTIMATED"],
    ["QTY-STEL-SUB", "Steel", "Substructure Reinforcement Steel (Piles, Caps, Plinth Beams, Grade Slab)", "128.74", "MT", "-", "Fe 500D", "95.61 kg/m3 concrete", "STR/TD/100-106", "ESTIMATED_DOMINANT"],
    ["QTY-STEL-SUP", "Steel", "Superstructure Reinforcement Steel (Columns, Walls, Beams, Slabs, Stairs, OHT)", "172.11", "MT", "-", "Fe 500D", "135.41 kg/m3 concrete", "STR/TD/103-110", "MEDIUM_DOMINANT"],
    ["QTY-STEL-TOT", "Steel", "TOTAL REINFORCEMENT STEEL (Substructure + Superstructure)", "300.85", "MT", "-", "Fe 500D", "87.98 kg/sq.m plinth", "All Structural Sheets", "DRAWING_BASED_ESTIMATE"],
    ["QTY-MAS-EXT", "Masonry", "External 230mm Brick Masonry in CM 1:6", "216.80", "m3", "-", "-", "0.063 m3/sq.m plinth", "AR/TD/006-012", "ESTIMATED"],
    ["QTY-MAS-INT", "Masonry", "Internal 115mm Partition Brick Masonry in CM 1:4 with hoop iron", "406.85", "m3", "-", "-", "0.119 m3/sq.m plinth", "AR/TD/005-007", "ESTIMATED"],
    ["QTY-MAS-TOT", "Masonry", "TOTAL BRICKWORK (External + Internal)", "623.65", "m3", "-", "-", "0.182 m3/sq.m plinth", "AR/TD/005-012", "ESTIMATED"],
    ["QTY-FIN-PLS", "Finishes", "Total Cement Plaster (Internal 12mm + External 18mm)", "14850.00", "sq.m", "-", "-", "4.34 m2/sq.m plinth", "AR/TD/006-013", "ESTIMATED"],
    ["QTY-FIN-FLR", "Finishes", "Total Tile & Stone Flooring (Vitrified, Ceramic, Kota)", "2700.00", "sq.m", "-", "-", "0.790 m2/sq.m plinth", "AR/TD/005-007, 110", "ESTIMATED"],
    ["QTY-OPN-TOT", "Openings", "Total Doors, Windows & Ventilators", "384", "nos", "-", "-", "16 nos per flat equivalent", "AR/TD/005 Schedule", "HIGH"]
]
write_csv("07_Final_Prototype_Dataset/calculated_quantities.csv", calc_headers, calc_rows)

# 3. Update 07_Final_Prototype_Dataset/validated_items.csv
val_headers = [
    "Item Code", "Item Description", "Model Calculated Value", "Official Reference Value", "Unit",
    "Scope Consistency Check", "Validation Status", "Quantity / Cost Accuracy", "Audit Traceability Reference"
]
val_rows = [
    ["VAL-001", "Tower Plinth Area", "3419.38", "3419.38", "sq.m", "PASS", "SCOPE_CONSISTENCY_CHECK", "N/A", "BoQ_3 Item 1.01 (27355 sqm / 8) & AR/TD/001"],
    ["VAL-002", "Dwelling Unit Count", "24", "24", "units", "PASS", "SCOPE_CONSISTENCY_CHECK", "N/A", "DBR Section 1 & AR/TD/007 (4 units/flr x 6 flrs)"],
    ["VAL-003", "Building Height & Storeys", "Stilt + 6", "Stilt + 6", "storeys", "PASS", "SCOPE_CONSISTENCY_CHECK", "N/A", "BoQ_3 Item 1.01 & AR/TD/010-013 (24.0m ht)"],
    ["VAL-004", "Foundation Bored Piles Count", "207", "Not in BOQ", "piles", "PASS", "DRAWING_VERIFIED_COUNT", "N/A", "Direct count from STR/TD/HOUSING(G+6)/100"],
    ["VAL-005", "Concrete Intensity (Superstructure)", "0.372", "0.35 - 0.40", "m3/sq.m", "N/A", "BENCHMARK_COMPARISON_ONLY", "NOT_CALCULATED", "IS 456 / High-rise residential benchmark"],
    ["VAL-006", "Steel Intensity (Superstructure)", "135.41", "125 - 145", "kg/m3", "N/A", "BENCHMARK_COMPARISON_ONLY", "NOT_CALCULATED", "IS 13920:2016 / Zone V Ductile Detailing"],
    ["VAL-007", "Overall Steel Intensity", "87.98", "80 - 95", "kg/sq.m", "N/A", "BENCHMARK_COMPARISON_ONLY", "NOT_CALCULATED", "Indian High Seismic Deep Piling Benchmark"],
    ["VAL-008", "Single Tower Construction Cost", "125000000", "No Itemized BOQ", "INR", "N/A", "NOT_VALIDATED", "NOT_CALCULATED", "Cost accuracy: NOT CALCULATED. Reason: no official itemized priced BOQ available."]
]
write_csv("07_Final_Prototype_Dataset/validated_items.csv", val_headers, val_rows)

# 4. Update 09_Calculation_Audit/column_wall_height_schedule.csv
col_headers = [
    "Element Mark", "Element Type", "Cross Section (mm)", "Count per Floor", "Number of Levels",
    "Total Member Count", "Clear Height per Level (m)", "Total Height (m)", "Gross Volume (m3)",
    "Concrete Grade", "Drawing Reference", "Confidence Status", "Audit Notes"
]
col_rows = [
    ["C1", "Column", "1200 x 350", 4, 7, 28, "3.00", "21.00", "35.28", "M30", "STR/TD/HOUSING(G+6)/104", "MEDIUM", "Exact schedule on Sheet 104; 3.0m height assumed repeated across 7 levels"],
    ["C2", "Column", "1200 x 300", 8, 7, 56, "3.00", "21.00", "60.48", "M30", "STR/TD/HOUSING(G+6)/104", "MEDIUM", "Exact schedule on Sheet 104; 3.0m height assumed repeated across 7 levels"],
    ["C3", "Column", "1200 x 300", 4, 7, 28, "3.00", "21.00", "30.24", "M30", "STR/TD/HOUSING(G+6)/104", "MEDIUM", "Exact schedule on Sheet 104; 3.0m height assumed repeated across 7 levels"],
    ["SW1", "Shear Wall", "1260 x 230", 12, 7, 84, "3.00", "21.00", "73.03", "M30", "STR/TD/HOUSING(G+6)/104", "MEDIUM", "Exact schedule on Sheet 104; 3.0m height assumed repeated across 7 levels"],
    ["SW2", "Shear Wall", "1500 x 230", 4, 7, 28, "3.00", "21.00", "28.98", "M30", "STR/TD/HOUSING(G+6)/104", "MEDIUM", "Exact schedule on Sheet 104; 3.0m height assumed repeated across 7 levels"],
    ["SW3", "Shear Wall", "1380 x 230", 4, 7, 28, "3.00", "21.00", "26.66", "M30", "STR/TD/HOUSING(G+6)/104", "MEDIUM", "Exact schedule on Sheet 104; 3.0m height assumed repeated across 7 levels"],
    ["SW4", "Shear Wall", "2925 x 230", 4, 7, 28, "3.00", "21.00", "56.51", "M30", "STR/TD/HOUSING(G+6)/104", "MEDIUM", "Exact schedule on Sheet 104; 3.0m height assumed repeated across 7 levels"],
    ["SW5", "Shear Wall", "5030 x 230", 4, 7, 28, "3.00", "21.00", "97.18", "M30", "STR/TD/HOUSING(G+6)/104", "MEDIUM", "Exact schedule on Sheet 104; 3.0m height assumed repeated across 7 levels"],
    ["SW6-SW10", "Core Shear Walls", "13890 x 230", 5, 7, 35, "3.00", "21.00", "67.09", "M30", "STR/TD/HOUSING(G+6)/104", "MEDIUM", "Lift and duct walls totaling 13.89m run length; 3.0m clear height assumed repeated"],
    ["PED-MUM", "Mumty Columns/Pedestals", "300 x 300 / 350 x 350", 8, 1, 8, "2.70", "2.70", "6.74", "M30", "STR/TD/HOUSING(G+6)/109", "MEDIUM", "Columns supporting mumty roof and water tank frame"]
]
write_csv("09_Calculation_Audit/column_wall_height_schedule.csv", col_headers, col_rows)

# 5. Update 09_Calculation_Audit/staircase_oht_schedule.csv
stair_headers = [
    "Element Description", "Level", "Number of Flights / Units", "Waist Slab / Wall Thick (mm)",
    "Flight Length / Plan Area (m/sq.m)", "Width / Height (m)", "Net Volume (m3)", "Concrete Grade",
    "Drawing Reference", "Confidence Status", "Audit Notes"
]
stair_rows = [
    ["Doglegged Staircase Cores (2 nos)", "Stilt to Terrace", 28, "150", "3.20m flight / 1.50m landing", "1.20m width", "26.60", "M30", "STR/TD/HOUSING(G+6)/110", "MEDIUM", "Flight geometry scheduled on Sheet 110; repeated flight multiplier across 28 flights"],
    ["Mumty Enclosure & Roof Slab", "Terrace to Mumty", 1, "125", "35.20 sq.m slab + walls", "2.70m ht", "10.03", "M30", "STR/TD/HOUSING(G+6)/109", "MEDIUM", "Mumty enclosure dimensions scheduled on Sheet 109"],
    ["Overhead Water Tank (OHT)", "Above Mumty Roof", 2, "150 (walls) / 200 (base)", "28.00 sq.m footprint", "2.20m ht", "16.50", "M30", "STR/TD/HOUSING(G+6)/109 & MEP", "ASSUMPTION_REQUIRED", "Twin compartment tank; wall/slab thickness estimated (ASM-010) without structural schedule"]
]
write_csv("09_Calculation_Audit/staircase_oht_schedule.csv", stair_headers, stair_rows)

print("Supplemental updates completed successfully.")

