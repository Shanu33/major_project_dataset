# Missing Document Recovery Report

**Project**: OIL/RITES Duliajan BQ Workmen Housing Complex  
**Tender**: `RITES/NERPO/OIL/BQ-HOUSING/25`  
**CPP Tender ID**: `2025_RITES_246752_1`  
**Selected Scope**: One typical Stilt+6 BQ Workmen Housing residential tower  
**Recovery Date**: September 17, 2026  

---

## 1. Executive Summary

> [!IMPORTANT]
> **One official tender document was recovered**: [`Corrigendum-Reply_to_Queries_pdf-2025-Sep-17-09-35-31.pdf`](file:///c:/Users/shahnawaz%20khan/OneDrive/Documents/DataRequirement/OIL-RITES-Duliajan-BQ-Housing/01_Tender_NIT_PreBid/Corrigendum-Reply_to_Queries_pdf-2025-Sep-17-09-35-31.pdf) (12 pages, 2.88 MB) from the RITES official repository.  
> However, **0 technical blockers were resolved**. All 10 active calculation blockers remain unresolved.
> - **Pile depth**: Still assumed (18.0 m from DBR range 15–20 m; no tabulated pile schedule found).
> - **Pile cap contradiction**: Still unresolved (54 cap entities on layout Sheet 101 vs. 84 caps in summary).
> - **Official BBS**: Still missing (structural drawings show bar marks/counts, but cut-lengths are derived; official BBS is a post-award contractor deliverable under IS 2502).
> - **Itemized BOQ / cost breakdown**: Still missing (contract is EPC Mode-II lump-sum component basis; official BOQ has area-based items only).
> - **Labour / duration modelling**: Still blocked (cannot proceed until quantities and schedules are validated).
> - **Final dataset readiness status**: Remains **`DRAWING_BASED_TAKEOFF_REQUIRES_RECONCILIATION`**.

---

## 2. Search Scope & Results

| Source | Method | Result |
| :--- | :--- | :--- |
| RITES tender portal (`rites.com/Upload/Tender/`) | Direct URL retrieval | **RECOVERED**: `Corrigendum-Reply_to_Queries_pdf-2025-Sep-17-09-35-31.pdf` (12 pages). `NIT_9` returned HTTP 404. |
| Local project folder (23 unique PDFs) | Full recursive scan | All 23 files cataloged and audited. |
| `99_Unverified_or_Related_References/` | 2 PDFs checked | 2020 tender (NIT CPI4685P21) — correctly quarantined. |
| eProcure / CPPP (`etenders.gov.in`) | Archive search by tender ID | No indexed results for `2025_RITES_246752_1` (session/CAPTCHA protected). |
| OIL eProcurement (`etender.srm.oilindia.in`) | Direct access | Requires registered bidder authentication. |
| Google web (10+ targeted queries) | Exact phrase + variant searches | Project confirmed; no technical schedules publicly hosted. |
| Tender aggregators (TenderShark, TenderTiger, ClassicTenders) | Project-matched searches | Metadata and commercial summaries only; no document downloads. |
| Contractor (Badri Rai & Company) corporate site | Profile search | Company overview; no project-specific engineering drawings. |

---

## 3. Post-Recovery Status Assessment

| # | Question | Status |
| :--- | :--- | :--- |
| **1** | Documents found | **1 official tender document recovered**: `Corrigendum-Reply_to_Queries_pdf-2025-Sep-17-09-35-31.pdf` (12 pages, 2.88 MB) saved in `01_Tender_NIT_PreBid/`. |
| **2** | Documents rejected | **2** (`NIT_CPI4685P21.pdf` and its precursor in `99_Unverified/` — belong to 2020 tender, correctly quarantined). |
| **3** | Documents quarantined | **0** new quarantines (existing quarantine folder unchanged). |
| **4** | Blockers resolved | **0 out of 10** (corrigendum clarifies contractual/software terms, not material takeoff schedules). |
| **5** | Blockers remaining | **10 out of 10** remain active. |
| **6** | Pile depth status | **Still assumed.** 18.0 m below cutoff (from DBR range 15–20 m). No tabulated pile schedule on drawings. |
| **7** | Pile cap contradiction status | **Still unresolved.** 54 cap entities on layout plan vs. 84 in summary. |
| **8** | Official BBS status | **Still missing.** Official BBS is an EPC contractor deliverable per IS 2502. |
| **9** | Itemized BOQ / cost breakdown status | **Still missing.** Contract is EPC Mode-II lump-sum; official BOQ has area-based items only. |
| **10** | Labour / duration modelling status | **Still blocked.** All technical prerequisites remain blocked. |
| **11** | Final dataset readiness status | **`DRAWING_BASED_TAKEOFF_REQUIRES_RECONCILIATION`** (unchanged). |

---

## 4. Why Technical Schedules Are Not Publicly Available

The recovered `Corrigendum-Reply_to_Queries` (Clause 1.9) provides official contractual confirmation of the **EPC Mode-II contractual structure**:

> *"A model, 3D view and walkthrough will be prepared & presented to RITES & Client within 15 days from award of work as per conceptual plan provided in tender. The latest software of design engineering including ETABS / STAAD PRO... AutoCAD etc. will be used for design & Engg. Purpose. In addition, the EPC Contractor shall provide licenses... Revit, ETABS/STAAD Pro, AutoCAD, Navisworks, Primavera..."*

Under **EPC Mode-II (Turnkey Component Basis)**:
1. **Pre-Tender Stage (Public)**: RITES issues conceptual architectural drawings, structural framing layouts, DBR, and geotechnical investigation. No detailed BBS or itemized material BOQ is prepared by the client.
2. **Post-Award Stage (Internal/Proprietary)**: The turnkey contractor (M/s Badri Rai & Company) carries out detailed structural engineering analysis (STAAD/ETABS), prepares working drawings, compiles official Bar Bending Schedules (BBS), and produces shop drawings for RITES approval.
3. **Pricing**: Awarded as a lump-sum component price (₹128.14 Cr excl. GST). Detailed internal rate analyses and cost sheets are confidential.

Therefore, the missing technical schedules **do not exist in the public domain**—they are post-award contractor deliverables.

---

## 5. 10 Unresolved Blockers & Acquisition Matrix

| # | Blocker | Required Document | Target Entity | Acquisition Path |
| :--- | :--- | :--- | :--- | :--- |
| 1 | Pile depth assumed (18m) | Tabulated pile schedule | RITES / Geo-consultant | Formal request to RITES PU-Guwahati |
| 2 | Pile cap count 54 vs 84 | Pile cap working drawing / schedule | RITES / Badri Rai | Structural working drawing request |
| 3 | Pile cap depth unverified (1.0m) | Pile cap schedule | RITES / Badri Rai | Structural working drawing request |
| 4 | 91 piles unaccounted in caps | Pile-to-cap allocation table | Badri Rai / RITES | Foundation shop drawings |
| 5 | No official BBS | BBS per IS 2502 | Badri Rai & Company | Post-award contractor submission |
| 6 | Beam/slab weighted averages | Detailed floor-wise schedules | Badri Rai / RITES | Structural calculation sheets |
| 7 | Masonry/plaster estimated deductions | Room-wise finishing schedule | Architect / Contractor | Architectural shop drawings |
| 8 | No itemized tower BOQ | Detailed priced material BOQ | OIL India Ltd / RITES | RTI application to Oil India Limited |
| 9 | No tower cost allocation | EPC contract component breakdown | OIL India Ltd | RTI / RITES Contract Cell |
| 10 | Labour/duration blocked | Approved construction programme | Badri Rai & Company | Primavera/MS Project baseline schedule |

