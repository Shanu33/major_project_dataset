# Second Pilot Phase 2-B — Overclaim Cleanup and Evidence Verification Log

**Project**: Development of Permanent Campus (Phase-I) for Nalanda University, at Rajgir, Bihar  
**Package**: Package 1C (Residential Buildings Parcel, NIT No: `NU/ENGG/54/2016-17/Tender: 01 dated 25th March 2017`)  
**Scope**: Faculty Housing Apartment Type 1B Block (G+2 Floors)  
**Working Directory**: `C:\Users\shahnawaz khan\OneDrive\Documents\DataRequirement\NIT-Nalanda`  
**Output Directory**: `10_Controlled_Transcription\second_pilot_phase_2_controlled_transcription`  
**Current Status**: **`SECOND_PILOT_PHASE_2_B_CLEANUP_COMPLETE_FOUNDATION_EXECUTION_BLOCKED`**  
**Dataset Readiness**: **`DRAWING_BASED_TAKEOFF_REQUIRES_RECONCILIATION`**  
*(The project is strictly NOT `READY_FOR_TAKEOFF`)*

---

## 1. Files Reviewed

The following existing Phase 2 files were subjected to rigorous audit and verification:
1. `controlled_nalanda_drawing_register.csv`
2. `controlled_nalanda_room_register.csv`
3. `controlled_nalanda_opening_register.csv`
4. `controlled_nalanda_grid_register.csv`
5. `controlled_nalanda_pile_register.csv`
6. `controlled_nalanda_foundation_blocker_register.csv`
7. `controlled_nalanda_transcription_audit_trail.csv`
8. `phase_2_controlled_transcription_log.md`

Source drawings re-verified:
- `04_Architectural_Drawings\01_Faculty_Apartments\Type_1B\a.2.1-type-1b-ground-floor-plan.pdf` (Sheet `NUC(1)-FAH - A.2.1`)
- `05_Structural_Drawings\01_Faculty_Housing_Apartments\Type_1B\1.1-pile-layout-and-details-for-faculty-housing-appt-type-1b-.pdf` (Sheet `NUC- FAH(1B)-S-A.1`)

---

## 2. Files Edited & Created

### Files Edited:
1. [**`controlled_nalanda_pile_register.csv`**](file:///C:/Users/shahnawaz%20khan/OneDrive/Documents/DataRequirement/NIT-Nalanda/10_Controlled_Transcription/second_pilot_phase_2_controlled_transcription/controlled_nalanda_pile_register.csv)  
   - Relabeled `provenance_count` as `DIRECT_LAYOUT_COUNT`.
   - Reclassified `provenance_depth` to `DRAWING_DETAIL_DIMENSION_VISIBLE_BUT_NOT_FOUNDING_DEPTH`.
   - Updated `confidence_status` to `BLOCKED_FOR_QUANTITY_EXECUTION`.
   - Set `assumption_flag` to `PILE_FOUNDING_DEPTH_NOT_CONFIRMED`.
   - Added explicit note prohibiting use of 12.700 m for pile running metres or concrete volume until confirmed by geotechnical investigation.
2. [**`controlled_nalanda_foundation_blocker_register.csv`**](file:///C:/Users/shahnawaz%20khan/OneDrive/Documents/DataRequirement/NIT-Nalanda/10_Controlled_Transcription/second_pilot_phase_2_controlled_transcription/controlled_nalanda_foundation_blocker_register.csv)  
   - Added explicit blocker `PILE_RUNNING_METRE_BLOCKED`.
   - Added explicit blocker for Lean Concrete Sub-Base footprint boundaries (`FND_BLK_07`).
   - Expanded geotechnical borehole and pile cap blockers.
3. [**`controlled_nalanda_transcription_audit_trail.csv`**](file:///C:/Users/shahnawaz%20khan/OneDrive/Documents/DataRequirement/NIT-Nalanda/10_Controlled_Transcription/second_pilot_phase_2_controlled_transcription/controlled_nalanda_transcription_audit_trail.csv)  
   - Updated row `AUD_NAL_0162` to record `transcription_method = DIRECT_LAYOUT_COUNT`.
   - Corrected row `AUD_NAL_0163` (`pile_depth_m`) to `evidence_type = SCHEMATIC_DETAIL_DIMENSION`, `transcription_method = DRAWING_DETAIL_DIMENSION_VISIBLE_BUT_NOT_FOUNDING_DEPTH`, and `status = BLOCKED_FOR_QUANTITY_EXECUTION`.
   - Added record `AUD_NAL_0164` explicitly logging pile linear running metres as `BLOCKED_FOR_QUANTITY_EXECUTION`.
4. [**`phase_2_controlled_transcription_log.md`**](file:///C:/Users/shahnawaz%20khan/OneDrive/Documents/DataRequirement/NIT-Nalanda/10_Controlled_Transcription/second_pilot_phase_2_controlled_transcription/phase_2_controlled_transcription_log.md)  
   - Removed all references suggesting pile linear running metres were allowed for calculation.
   - Clarified that 12.700 m is a schematic detail dimension, not an executable founding depth.
   - Updated Phase 3 recommendation from "sample execution of pile running metres" to "Formula Setup and Blocked Dependency Mapping".

### Files Created:
1. [**`phase_2_b_pile_evidence_verification.csv`**](file:///C:/Users/shahnawaz%20khan/OneDrive/Documents/DataRequirement/NIT-Nalanda/10_Controlled_Transcription/second_pilot_phase_2_controlled_transcription/phase_2_b_pile_evidence_verification.csv)  
   12-item evidence verification matrix evaluating pile type, mark, diameter, count, depth claim, concrete grade, steel grade, cover, lap length, pile cap details, lean concrete, and pile running metres.
2. [**`phase_2_b_overclaim_cleanup_log.md`**](file:///C:/Users/shahnawaz%20khan/OneDrive/Documents/DataRequirement/NIT-Nalanda/10_Controlled_Transcription/second_pilot_phase_2_controlled_transcription/phase_2_b_overclaim_cleanup_log.md)  
   This cleanup and governance report.
3. [**`phase_2_b_final_guardrail_check.md`**](file:///C:/Users/shahnawaz%20khan/OneDrive/Documents/DataRequirement/NIT-Nalanda/10_Controlled_Transcription/second_pilot_phase_2_controlled_transcription/phase_2_b_final_guardrail_check.md)  
   Exhaustive guardrail verification audit proving zero unauthorized quantities, zero costs, and zero unverified execution claims.

---

## 3. Pile Claims Checked & Audit Findings

| Evidence Item | Claimed Value | Audit Status | Finding / Evidence Grounding |
| :--- | :--- | :--- | :--- |
| **Pile Type** | Bored Cast-In-Situ RCC Pile | `DIRECT_SHEET_OBSERVATION` | Confirmed by sheet title and Note: "PILING WORK TO BE DONE AS PER IS 2911-2010". |
| **Pile Mark** | P1 | `DIRECT_SHEET_OBSERVATION` | Confirmed by layout tags and typical detail labels `P1`. |
| **Pile Diameter** | 600 mm | `DIRECT_SHEET_OBSERVATION` | Explicitly scheduled as `600Φ` on typical detail and `600 DIA` on Section X-X. |
| **Pile Count** | 189 | `DIRECT_LAYOUT_COUNT` | Audited count of 189 circular markers across the GA layout. |
| **Pile Depth (12.7m)**| 12.700 m (12700 mm) | `DRAWING_DETAIL_DIMENSION_VISIBLE_BUT_NOT_FOUNDING_DEPTH` | Dimension `12700` is drawn with a break line on a typical detail. Geotechnical termination criteria, strata depths, and borehole logs are absent. **Must NOT be used as executable founding depth.** |
| **Concrete Grade** | M25 | `DIRECT_SHEET_OBSERVATION` | Directly stated in general note: "ALL CONCRETE MIX M25 UNLESS OTHERWISE SPECIFIED". |
| **Steel Grade** | Fe 500D | `DIRECT_SHEET_OBSERVATION` | Directly stated in general note: "INDICATES TMT STEEL (Fe 500D) OF YIELD STRENGTH 500 N/mm²". |
| **Clear Cover** | 50 mm | `DIRECT_SHEET_OBSERVATION` | Confirmed in cover table: "PILES : 50 mm". |
| **Lap Length** | 50d | `DIRECT_SHEET_OBSERVATION` | Confirmed in lap note: "LAP LENGTH IS FIFTY TIMES BAR DIAMETER". |
| **Pile Cap Detail** | Thickness 450/600 mm | `NOT_SCHEDULED` | Wall section notes "GRADE BEAM, RAFT SLAB OR PILE CAP", but no discrete pile cap schedule or cap markings exist. |
| **Lean Concrete** | 100 mm thick 1:4:8 | `DIRECT_SHEET_OBSERVATION` | Visible on wall section detail as sub-base, but spatial boundary is not delineated. |
| **Running Metres** | 2,400.30 m ($189 \times 12.7$) | `BLOCKED_FOR_QUANTITY_EXECUTION` | Strictly blocked. Multiplying layout count by schematic detail dimension violates engineering evidence controls. |

---

## 4. Pile Claims Corrected

1. **Pile Depth De-weaponization**: In the previous run, $12.700\text{ m}$ was transcribed with status `DIRECT_SHEET_OBSERVATION` under `provenance_depth`. This created a risk that subsequent phases would treat 12.7 m as an executable founding depth. This has been reclassified to **`DRAWING_DETAIL_DIMENSION_VISIBLE_BUT_NOT_FOUNDING_DEPTH`** with status **`BLOCKED_FOR_QUANTITY_EXECUTION`** and assumption flag **`PILE_FOUNDING_DEPTH_NOT_CONFIRMED`**.
2. **Pile Running Metres Blockade**: Any implication that pile linear running metres ($189 \times 12.7\text{ m} = 2,400.30\text{ m}$) could be computed as a sample quantity has been completely eradicated and explicitly blocked.
3. **Pile Reinforcement Clarification**: Explicitly documented that Section X-X on Sheet `NUC- FAH(1B)-S-A.1` is a plain concrete section showing no longitudinal rebar, no stirrup/spiral ties, and no bar marks. Reinforcement takeoff is 100% blocked.

---

## 5. Unsafe Formula / Execution Language Removed

The following corrections were applied to `phase_2_controlled_transcription_log.md`:
- **Removed**: "pile linear running metres allowed" $\rightarrow$ **Replaced with**: "pile linear running metres remain blocked".
- **Removed**: "scheduled length 12.700 m" / "pile depth 12.700 m" $\rightarrow$ **Replaced with**: "12.700 m is a visible drawing-detail dimension but not validated as executable founding depth".
- **Removed**: "can proceed to foundation sample formulas" $\rightarrow$ **Replaced with**: "foundation sample formulas may be defined but not executed".
- **Updated Next Step**: "Second Pilot Phase 3 — Formula Setup and Blocked Dependency Mapping" (preventing premature execution of pile quantities).

---

## 6. Remaining Allowed Facts

The following facts are verified and remain allowed for coordination and non-executable documentation:
1. Ground floor room clear dimensions ($L, W$), derived floor areas, and perimeters for all 23 spaces on Sheet `NUC(1)-FAH - A.2.1`.
2. Door and window schedule dimensions ($W, H$), sill heights, lintel heights, and derived face areas for all 17 opening types on Sheet `NUC(1)-FAH - A.2.1`.
3. Visible ground-floor opening layout counts.
4. Structural gridlines X1–X17 and Y1–Y19 with bay spacings on Sheet `NUC- FAH(1B)-S-A.1`.
5. Bored cast-in-situ pile diameter of $600\text{ mm}$ on Sheet `NUC- FAH(1B)-S-A.1`.
6. Pile layout marker count of 189 piles across the GA layout.
7. Material specification labels: M25 concrete, Fe 500D steel, $50\text{ mm}$ pile clear cover, $50d$ lap length, 100 mm lean concrete 1:4:8 sub-base.

---

## 7. Remaining Blocked Foundation Scopes

1. Pile linear running metres ($m$).
2. Pile concrete volume ($m^3$).
3. Pile reinforcement tonnage ($MT$).
4. Pile cap excavation, lean concrete bed, concrete volume, formwork, and reinforcement.
5. Grade beam / plinth tie beam civil and structural takeoff.
6. Column starter bars and pedestal concrete.
7. Borehole strata confirmation and geotechnical cut-off validation.
8. BOQ Schedule B line-item validation.

---

## 8. Mandatory Guardrail Certifications

- [x] **No final quantities were calculated** ($0.0\text{ m}^3$ concrete, $0.0\text{ MT}$ steel, $0.0\text{ m}^3$ masonry, $0.0\text{ m}$ pile length).
- [x] **No costs were calculated** (`Cost accuracy: NOT_CALCULATED`).
- [x] **No BOQ validation was performed** (`Quantity accuracy: NOT_CALCULATED`).
- [x] **No labour/duration modelling was performed** (`Labour/Duration: BLOCKED`).
- [x] **No upper-floor multiplication was applied** (`GROUND_FLOOR_ONLY`).
- [x] **No pile running metres were calculated**.
- [x] **No pile concrete volume was calculated**.
- [x] **The project remains `DRAWING_BASED_TAKEOFF_REQUIRES_RECONCILIATION`**.
- [x] **The project is strictly NOT `READY_FOR_TAKEOFF`**.

