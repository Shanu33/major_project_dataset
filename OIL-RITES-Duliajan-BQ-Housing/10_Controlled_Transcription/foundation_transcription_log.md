# Foundation Transcription Log (Priority A)
## OIL/RITES Duliajan BQ Workmen Housing (Typical Tower Pilot)

**Target Folder**: `10_Controlled_Transcription/`  
**Execution Date**: September 17, 2026  
**Status**: `FOUNDATION_TRANSCRIPTION_PARTIAL`  

---

## 1. Source Sheets Inspected

| Sheet ID | Sheet Title | PDF Source & Page | Revision & Date | Scale |
| :--- | :--- | :--- | :--- | :--- |
| `RITES/BLD/STR/TD/HOUSING(G+6)/100` | PILE LAYOUT PLAN | `Tender_drawing_3_TypicalFloor_StructuralHousing.pdf` (Page 16) | Rev R0, July 2025 | NTS (Title block) / 1:100 |
| `RITES/BLD/STR/TD/HOUSING(G+6)/101` | PILE CAP LAYOUT PLAN AND REINFORCEMENT DETAILS | `Tender_drawing_3_TypicalFloor_StructuralHousing.pdf` (Page 17) | Rev R0, July 2025 | NTS (Title block) / 1:100 |

---

## 2. What Was Directly Transcribed (Direct Sheet Observation)

### From Sheet 100 (Pile Layout Plan):
- **Total Pile Count**: Exactly **207 pile marker positions** ('P') verified directly from layout coordinate grid and PDF vector objects.
- **Pile Diameter**: **600 mm** directly visible in drawing title (`TYPICAL ELEVATION OF PILE (600MM DIA)`), Section A-A diagram, and General Note 16.
- **Longitudinal Reinforcement**: **10-T20** bars directly shown in Section A-A and elevation callout.
- **Confining Spiral / Ties**: **T8 @ 125 mm c/c** for 9,000 mm top and bottom ductility zones; **T8 @ 150 mm c/c** for middle zone.
- **Master Rings**: **T16 @ 1,500 mm c/c** (`MASTER RING`).
- **Safe Bearing Capacity**: **68 MT/pile** directly stated in General Note 16.
- **Concrete & Steel Specifications**: **M30** design mix (Note 5) and **Fe 550 D** TMT bars (Note 7).
- **Indicative Elevation Dimension**: **20,000 mm** (20.0 m) dimension printed alongside typical pile elevation diagram.

### From Sheet 101 (Pile Cap Layout Plan & Reinforcement Details):
- **Pile Cap Thickness**: **750 mm** directly observed as printed label `750 THK PC` across multiple cap outlines on the plan (notably the core wall combined cap and adjacent strip caps).
- **Core Wall Combined Cap**: Large rectangular combined raft cap under lift core and shear walls SW6–SW10 visibly enclosing **20 piles** in a 4×5 grid.
- **Bottom Reinforcement Schedule**: `BAR MARKED A: DIA & SPACING T25@100c/c(THROUGH)`.
- **Top Reinforcement Schedule**: `BAR MARKED B: DIA & SPACING T25@150c/c(THROUGH)`.
- **Distribution Reinforcement**: `ALL DISTRIBUTION STEEL SHALL BE T16 @ 100c/c WHEREVER REQUIRED`.
- **Concrete & Steel Specifications**: **M30** design mix (Note 5), **Fe 550 D** (Note 7), and **75 mm** clear cover for foundations (Note 9).

---

## 3. What Remains Assumed

1. **Pile Termination Depth / Length**:
   - Tabulated pile schedule showing individual pile founding depths, cut-off levels, and strata socketing is **NOT present on Sheet 100**.
   - Model depth of **18.0 m** below cut-off is an engineering assumption derived from DBR p.35 and Geotechnical Report recommended range (15 m to 20 m).
   - Although typical elevation diagram shows an indicative 20.0 m dimension line, individual pile lengths remain an **assumption**.

2. **Historical Pile Cap Depth (1000 mm)**:
   - The earlier preliminary takeoff assumed a 1,000 mm uniform depth across all caps.
   - Drawing evidence now reveals `750 THK PC` callouts. Reconciling whether 1000 mm applies to isolated caps or if 750 mm applies universally remains an engineering assumption until working drawings are obtained.

---

## 4. What Remains Unresolved

1. **Pile Cap Entity Contradiction (54 vs. 84 Caps)**:
   - The preliminary summary claimed 84 discrete caps.
   - Visual inspection of Sheet 101 shows continuous strip caps and large combined raft entities, resulting in 54 or fewer discrete geometric outlines.
2. **Pile Allocation to Caps**:
   - Approximately **91 piles** are enclosed under continuous multi-element strip caps without individual pile group marks. A detailed pile-to-cap allocation schedule was never issued in the tender package.

---

## 5. Summary Evaluation Checklist

| Question | Answer | Details |
| :--- | :--- | :--- |
| **Is pile depth direct or assumed?** | **ASSUMED** | Assumed 18.0 m from DBR range (15–20 m); not scheduled per pile on drawing. |
| **Is pile cap count reconciled?** | **NO** | 54 visual entities vs. 84 preliminary summary count remains an active contradiction. |
| **Does official BBS exist?** | **NO** | Bar marks and spacing are visible; official cut-length schedules were never issued. |
| **Were any quantities/cost/duration calculated?** | **NO** | Evidence transcription only; zero new quantities or validation numbers produced. |

---

## 6. Final Foundation Transcription Status

```
Status: FOUNDATION_TRANSCRIPTION_PARTIAL
Readiness: DRAWING_BASED_TAKEOFF_REQUIRES_RECONCILIATION
Next Step: Priority B Structural Frame Transcription (Columns, Shear Walls, Beams, Slabs)
```

