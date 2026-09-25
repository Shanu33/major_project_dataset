import os, shutil

base_dir = r"c:\Users\shahnawaz khan\OneDrive\Documents\DataRequirement\SBI-GIFT-City-Twin-Towers"

# Distribute primary PDFs to respective technical directories
revised_tb = os.path.join(base_dir, "01_Tender_NIT_PreBid", "Technical_Bid_Revised_Corrigendum.pdf")
revised_pb = os.path.join(base_dir, "02_Cost_BOQ_Makes", "Price_Bid_BOQ_Revised_Corrigendum.pdf")
prebid_pdf = os.path.join(base_dir, "01_Tender_NIT_PreBid", "PreBid_Replies_and_Required_Docs.pdf")

# Copy master docs to 00_Core_Intelligence_Dataset
shutil.copy2(revised_tb, os.path.join(base_dir, "00_Core_Intelligence_Dataset", "Technical_Bid_Revised_Corrigendum.pdf"))
shutil.copy2(revised_pb, os.path.join(base_dir, "00_Core_Intelligence_Dataset", "Price_Bid_BOQ_Revised_Corrigendum.pdf"))
shutil.copy2(prebid_pdf, os.path.join(base_dir, "00_Core_Intelligence_Dataset", "PreBid_Replies_and_Required_Docs.pdf"))

# Copy relevant files to specialized technical directories
shutil.copy2(revised_tb, os.path.join(base_dir, "03_Technical_Specifications_Reports", "Technical_Bid_Revised_Corrigendum.pdf"))
shutil.copy2(revised_tb, os.path.join(base_dir, "04_Architectural_Drawings", "Technical_Bid_Revised_Corrigendum.pdf"))
shutil.copy2(revised_tb, os.path.join(base_dir, "05_Structural_Drawings", "Technical_Bid_Revised_Corrigendum.pdf"))
shutil.copy2(prebid_pdf, os.path.join(base_dir, "05_Structural_Drawings", "PreBid_Replies_and_Required_Docs.pdf"))
shutil.copy2(revised_tb, os.path.join(base_dir, "06_MEP_Services", "Technical_Bid_Revised_Corrigendum.pdf"))
shutil.copy2(revised_pb, os.path.join(base_dir, "06_MEP_Services", "Price_Bid_BOQ_Revised_Corrigendum.pdf"))
shutil.copy2(revised_tb, os.path.join(base_dir, "07_Landscape_Infrastructure", "Technical_Bid_Revised_Corrigendum.pdf"))

# 1. 00_Core_Intelligence_Dataset/Project_Executive_Summary_and_Data_Extraction.md
f00 = """# Project Executive Summary & Technical Intelligence: SBI Residential Twin Towers, GIFT City

## 1. Project Master Identification
- **Official Project Title:** Composite Construction works of Civil, Plumbing, Sanitary, Electrical, Firefighting, HVAC, SECURITY EQUIPMENTS, LIFTS, IBMS, Landscaping, and Allied Services, etc. Proposed Construction of Residential Twin Towers at Block No 41 A & B, GIFT City, Gandhinagar, Gujarat
- **Tender Reference / ID:** `SBI/GNR/26-27/02` (Revised Corrigendum); Earlier: `SBI/GNR/25-26/03`
- **Client / Authority:** State Bank of India (SBI) - Premises & Estate Department, Local Head Office, Plot No-53A, SBI Tower, 2nd Floor, GIFT City, Gandhinagar - 382355, Gujarat
- **Architect & APMC:** M/s VK:a architecture, Pune (5th Floor, Next Gen Avenue, Off Senapati Bapat Road, near ICC Trade Tower, Pune - 411016)
- **Project Site Location:** Block No. 41 (Plots 41 A & B), GIFT City, Gandhinagar, Gujarat - 382355
- **Tender Estimated Cost:** **Rs 2,53,32,55,034.00** (~Rs 253.33 Crores, Excluding GST)
- **Earnest Money Deposit (EMD):** **Rs 2,53,33,000.00** (Rs 2.5333 Crores)
- **Contract Duration:** **39 Calendar Months** (including monsoon and holidays) + 15 Days Mobilisation
- **Defects Liability Period (DLP):** 18 Months from date of virtual completion

## 2. Verified Building Scope & Geometric Metrics
All parameters verified directly from Clause 3.0 (Page 13) and Pre-Bid Minutes:
- **Tower Configuration:** High-Rise Residential Twin Towers comprising **3 Common Basements + Ground Floor + 25 Floors (A-Wing) & 26 Floors (B-Wing)**.
- **Skip / Amenity Floor:** The **20th Floor** in both Tower A and Tower B is designated as a specialized Skip / Amenity / Refuge Floor (as per Architectural Drawings 313, 314, 315, 316, 318, 325).
- **Approximate Total Construction Area:** **51,588.00 m2** (5,55,288 sq.ft.).
- **Total Built-Up Area (BUA):** **22,472.00 m2** (2,41,886 sq.ft.).
- **Basement Deep Retention:** **600 mm thick continuous Diaphragm Wall** retaining 3 common basements with corner/end wall structures and anchoring.
- **Foundation System:** Heavy RCC Raft foundation on diaphragm wall perimeter (Structural Drawing `23-38-STR-1001`).
- **Inter-Tower Connectivity:** Connecting Bridge between towers at upper levels.
- **Parking Facility:** Multi-level basement parking with automated **96-Car Puzzle Parking System**.

## 3. High-Technology & Modern Construction Mandates
- **BIM Revit Delivery:** Contractor is mandated to submit all Shop Drawings and As-Built Drawings in Building Information Modeling (BIM) **REVIT format** without extra cost.
- **Integrated Building Management System (IBMS):** Comprehensive PLC/BMS controlling HVAC, ventilation, fire systems, lifts, and access control.
- **Smart City Compliance:** Strict adherence to GIFT City infrastructure norms, utility tunnels, district cooling / ventilation coordination, and waste management.
"""

with open(os.path.join(base_dir, "00_Core_Intelligence_Dataset", "Project_Executive_Summary_and_Data_Extraction.md"), "w", encoding="utf-8") as f:
    f.write(f00)

# 2. 01_Tender_NIT_PreBid/Tender_NIT_Key_Terms_and_Eligibility_Criteria.md
f01 = """# Tender Notice & Commercial Framework: SBI GIFT City Twin Towers

## 1. Notice Inviting Tender (NIT) Parameters
- **Tender Reference:** `SBI/GNR/26-27/02` (Corrigendum / Revised Bid); Original `SBI/GNR/25-26/03`
- **Bidding Mode:** Single Stage Two Envelope System (Online Technical Bid + Online Price Bid via `https://www.tenderwizard.com/SBIETENDER`)
- **Tender Fee:** NIL
- **EMD Amount:** Rs 2,53,33,000.00 via Demand Draft / Banker's Cheque payable at GIFT City Gandhinagar
- **Tender Availability Window:** 07.04.2026 to 29.04.2026 up to 5:00 PM
- **Pre-Bid Meeting:** 17.04.2026 at 12:30 PM (LHO SBI Tower, GIFT City)
- **Technical Bid Opening:** 30.04.2026 at 12:30 PM

## 2. Prequalification Criteria (Clause 5.0)
1. **Multi-Storied Building Experience:**
   - Completed composite construction of RCC framed multi-storied building with similar complexity for PSUs, Banks, Central/State Governments, or listed public companies.
2. **MEPF Composite Experience:**
   - Mandated experience executing composite MEPF works including at least 4 out of: Plumbing, Electrical, Fire Fighting, HVAC, Security Equipment, Lifts, and IBMS.
3. **Financial Solvency & Turnover:**
   - Established average annual financial turnover criteria and positive net worth over consecutive audited financial years.

## 3. Commercial Terms & Progress Billing
- **Interim Payment Certificates (RA Bills):**
  - Minimum **Rs 4.0 Crores** each for first 3 RA bills.
  - Minimum **Rs 7.0 Crores** each from 4th RA bill onward.
  - Frequency: Maximum one bill per calendar month.
- **Advances:** Strictly **NO mobilization advance** or advance on materials/machinery.
- **Additional Security Deposit (ASD) / APG:** Applicable if the contractor's quoted price is more than 10% below the estimated cost.
"""

with open(os.path.join(base_dir, "01_Tender_NIT_PreBid", "Tender_NIT_Key_Terms_and_Eligibility_Criteria.md"), "w", encoding="utf-8") as f:
    f.write(f01)

# 3. 02_Cost_BOQ_Makes/Cost_Abstract_and_BOQ_Schedule_Intelligence.md
f02 = """# Cost Abstract & BOQ Intelligence: SBI GIFT City Twin Towers

## 1. Master BOQ Cost Summary (162-Page Revised Price Bid)
The comprehensive project estimate of **Rs 253,32,55,034.00** (Plus GST) is structured across 8 core packages:

| Section Code | Trade / Work Description | Major Scope & Inclusions |
| :--- | :--- | :--- |
| **Section A(i)** | **Civil Works** | Earthwork excavation, diaphragm wall (600mm), RCC raft & frame (G+25/26), AAC block masonry, internal/external plaster, waterproofing, flooring, painting |
| **Section A(ii)**| **Plumbing Works (Internal & External)** | Water supply piping (CPVC/DI), soil/waste/rainwater drainage (UPVC/SWR), sanitary fixtures, hydro-pneumatic pumping, solar water heating |
| **Section B** | **Fire Fighting, Fire Alarm & PA System** | External hydrant ring, wet risers, automatic sprinklers, UL-listed fire pumps, addressable fire alarm, public address system (PAS) |
| **Section C** | **Electrical, Lifts, Data & Telephone** | High-tension/low-tension panels, bus ducts, transformers, cabling, wiring, LED lighting, high-speed passenger/service lifts, IT/telecom infrastructure |
| **Section D** | **Security System & IBMS** | CCTV surveillance, access control, automatic boom barriers, Integrated Building Management System (BMS software, DDC controllers, sensors) |
| **Section E** | **Garbage Chute** | Stainless steel centralized garbage chute system with intake hoppers and automated sanitation/brush cleaning |
| **Section F** | **Automated Parking System** | Automated multi-tier **Puzzle Car Parking System for 96 cars** in basements |
| **Section G** | **HVAC System** | Basement mechanical ventilation, jet fans, fire smoke extraction, lift lobby motorized fire dampers (UL555), VRF air conditioning, copper piping |
| **Total** | **Grand Total (Excluding GST)** | **Rs 2,53,32,55,034.00** (~Rs 253.33 Crores) |

## 2. Key BOQ Preambles
- Rates are comprehensive and inclusive of cup-lock type double scaffolding, tower cranes, passenger/material hoists, aerial lifts, site lab, and statutory GIFT City utility coordination.
"""

with open(os.path.join(base_dir, "02_Cost_BOQ_Makes", "Cost_Abstract_and_BOQ_Schedule_Intelligence.md"), "w", encoding="utf-8") as f:
    f.write(f02)

# 4. 03_Technical_Specifications_Reports/Technical_Specifications_and_Standards_Summary.md
f03 = """# Technical Specifications & Engineering Standards Summary

## 1. Structural Concrete & Masonry
- **Concrete Grades:** High-performance design mix concrete (M30, M40, M50) with fly ash / GGBS mineral admixtures conforming to IS 456 & IS 10262.
- **Reinforcement:** Thermo-mechanically treated (TMT) Fe 500D / Fe 550D conforming to IS 1786.
- **Masonry:** Autoclaved Aerated Concrete (AAC) blocks conforming to IS 2185 (Part 3) with thin-bed polymer adhesive mortars.

## 2. Specialized Technical Specifications (Sections 33 to 37 of Technical Bid)
- **Section 33: Fire Alarm & Public Address System (FA & PAS):** Fully addressable microprocessor-based fire detection with multi-sensor smoke/heat detectors, manual call points, response indicators, voice evacuation speakers, and integration with BMS.
- **Section 34: Security Equipment:** IP-based HD CCTV surveillance covering all public areas, basements, and elevator cars; RFID vehicle tags and automatic boom barriers at entrance gates.
- **Section 35: Lifts / Elevators:** High-speed gearless passenger elevators with regenerative drives, ARD (Automatic Rescue Device), fire-rated landing doors, and group supervisory controls.
- **Section 36: Heating, Ventilation & Air Conditioning (HVAC):** Basement ventilation via dual-speed induction/jet fans, stairwell and lift lobby pressurization fans, motorized fire dampers with 1.5-hour rating (UL 555), and VRF systems.
- **Section 37: Integrated Building Management System (IBMS):** BACnet/IP open-protocol BMS integrating HVAC, electrical meters, diesel generator sets, water pumping, fire alarms, and STP monitoring.
"""

with open(os.path.join(base_dir, "03_Technical_Specifications_Reports", "Technical_Specifications_and_Standards_Summary.md"), "w", encoding="utf-8") as f:
    f.write(f03)

# 5. 04_Architectural_Drawings/Architectural_Design_Basis_and_Drawings_Catalog.md
f04 = """# Architectural Design Basis & Drawings Catalog

## 1. Architectural Design Scheme
- **Concept:** High-density, sustainable luxury high-rise twin towers designed for SBI executive residency within the international financial tech-city (GIFT City).
- **Wing A:** Ground + 25 Floors + 3 Common Basements.
- **Wing B:** Ground + 26 Floors + 3 Common Basements.
- **Skip Floor Design:** 20th Floor in both towers features a double-height skip area accommodating refuge terraces, community sky lounges, and service zones (Drawings 313, 314, 315, 316, 318, 325).
- **Connecting Bridge:** Upper-level pedestrian skybridge linking Tower A and Tower B.

## 2. Public Drawings Access & Google Drive Repository
As officially confirmed in Item 59 & Page 38 of the Pre-Bid Clarifications, architectural drawings, diaphragm wall profiles, and electrical layouts are hosted at:
- **Public Google Drive Folder:** [https://drive.google.com/drive/folders/1-dJkPVTwNNXJMZWjMMk6Wa3tmlQ9wzCH?usp=sharing](https://drive.google.com/drive/folders/1-dJkPVTwNNXJMZWjMMk6Wa3tmlQ9wzCH?usp=sharing)
- **Drawing Sheet References:**
  - `Drawing No. 304`: Ground Floor Site Development, vehicular circulation, and landscape drop-off.
  - `Drawing No. 313-316, 318`: Architectural elevation profiles, cross-sections, and core layouts.
  - `Drawing No. 322`: Typical Even Floor Plan (Residential Units).
  - `Drawing No. 325`: 20th Floor Skip Floor Plan.
  - `Drawing No. 23-38-STR-1001`: Diaphragm wall and RCC raft foundation details.
"""

with open(os.path.join(base_dir, "04_Architectural_Drawings", "Architectural_Design_Basis_and_Drawings_Catalog.md"), "w", encoding="utf-8") as f:
    f.write(f04)

# 6. 05_Structural_Drawings/Structural_Design_Basis_and_Diaphragm_Wall_Notes.md
f05 = """# Structural Design Basis & Diaphragm Wall Engineering Notes

## 1. Substructure & Deep Excavation Retention
- **Retention Scheme:** Continuous **600 mm thick reinforced concrete Diaphragm Wall** retaining 3 common basements.
- **Waterproofing:** Diaphragm wall constructed water-tight; inside face finished directly to receive paint without plaster (Price Bid Item 59 C).
- **Raft Foundation:** Monolithic thick RCC raft foundation resting on dense silty-sand / alluvial strata of Gandhinagar.

## 2. Superstructure Design Standards
- **Structural System:** RCC shear wall and moment-resisting frame structure designed for Seismic Zone III with high ductility detailing conforming to IS 13920:2016 and wind loads conforming to IS 875 (Part 3).
- **BIM & Rebar Detailing:** Complete 3D Building Information Modeling (BIM) in Revit format with bar bending schedules and clash detection.
- **Geotechnical Report Status:** Site investigation conducted by SBI; official soil investigation report and borehole logs released to the finalized execution contractor as confirmed in Pre-Bid Item 58.
"""

with open(os.path.join(base_dir, "05_Structural_Drawings", "Structural_Design_Basis_and_Diaphragm_Wall_Notes.md"), "w", encoding="utf-8") as f:
    f.write(f05)

# 7. 06_MEP_Services/MEP_Engineering_Specifications_and_Services_Schedule.md
f06 = """# MEP Engineering Services & Smart City Utility Schedule

## 1. Electrical & Power Infrastructure
- **Grid Supply:** High-tension connection from GIFT City power distribution utility.
- **Sub-Station & Switchgear:** Common basement electrical room with HT vacuum circuit breakers, transformers, and automated LT panels.
- **Single Line Diagrams (SLD):** Electrical Work SLD Layout (Common) and SLD Layout (LT Consumer) shared via Google Drive link.

## 2. Public Health, Plumbing & Environmental Systems
- **Water Network:** Dual plumbing system (potable water and treated recycled water for flushing/landscaping).
- **GIFT City Utility Corridor:** Direct tie-in of water supply, district cooling/chilled water, and sewerage discharge into GIFT City's underground utility tunnels.
- **Solid Waste:** Centralized automated stainless steel garbage chute discharging to sealed waste compactors.

## 3. Vertical Transportation
- **Elevator Package:** High-speed passenger elevators serving basements to 26th floor with group control and dedicated service/fireman elevators.

## 4. Automated Puzzle Car Parking
- **System Capacity:** 96-car automated puzzle parking mechanism installed in basement levels to maximize space utilization.
"""

with open(os.path.join(base_dir, "06_MEP_Services", "MEP_Engineering_Specifications_and_Services_Schedule.md"), "w", encoding="utf-8") as f:
    f.write(f06)

# 8. 07_Landscape_Infrastructure/Site_Development_and_External_Infrastructure_Schedule.md
f07 = """# Site Development, External Amenities & GIFT City Urban Integration

## 1. Plot & Site Planning
- **Site Designation:** Block No. 41 (Plots 41 A & B), GIFT City, Gandhinagar.
- **Site Development (Drawing 304):** Pedestrian plaza, vehicular drop-offs, security check posts, external lighting, stormwater drainage, and peripheral fire tender roadway.
- **Internal Roads & Paving:** Heavy-duty interlocking concrete pavers and asphalt bitumen internal circulation roads designed for axle loads of municipal fire tenders.

## 2. Hardscape & Softscape Landscaping
- **Landscape Architecture:** Native drought-resistant planting, manicured turf, drip irrigation, water features, aesthetic outdoor lighting, and pergola seating.
- **Connecting Skybridge:** Structural connecting skybridge linking Tower A and Tower B at upper levels.
"""

with open(os.path.join(base_dir, "07_Landscape_Infrastructure", "Site_Development_and_External_Infrastructure_Schedule.md"), "w", encoding="utf-8") as f:
    f.write(f07)

# 9. 08_Execution_Actuals/Construction_Milestones_and_Execution_Charter.md
f08 = """# Construction Milestones & Fast-Track Execution Charter

## 1. Contract Schedule & Execution Timeline
- **Contract Period:** **39 Calendar Months** including monsoon and holidays + 15 Days Mobilisation.
- **Execution Mode:** Fast-Track Turnkey Composite Delivery.
- **Stage of Project:** Active bidding and tender evaluation stage (April 2026 Corrigendum).

## 2. Major Critical Path Milestones
1. **Milestone 1 (Months 1–6):** Mobilization, installation of 600mm continuous diaphragm wall around perimeter, deep excavation for 3 common basements (51,588 m2 total construction footprint), dewatering.
2. **Milestone 2 (Months 7–12):** Construction of monolithic RCC raft foundation and completion of 3 basement slabs.
3. **Milestone 3 (Months 13–24):** Superstructure RCC framing of Tower A (G+25) and Tower B (G+26), including 20th floor skip/amenity deck and structural connecting skybridge.
4. **Milestone 4 (Months 25–33):** External masonry (AAC blocks), waterproofing, external plaster, fenestrations, and concurrent rough-in of MEP services (Plumbing, Electrical, HVAC, Fire fighting).
5. **Milestone 5 (Months 34–39):** Internal finishes, elevator installation, IBMS integration, testing and commissioning of 96-car puzzle parking, landscape development, GIFT City NOCs, and handover.
"""

with open(os.path.join(base_dir, "08_Execution_Actuals", "Construction_Milestones_and_Execution_Charter.md"), "w", encoding="utf-8") as f:
    f.write(f08)

print("Successfully generated all 9 domain intelligence markdown documents for SBI GIFT City Twin Towers!")

