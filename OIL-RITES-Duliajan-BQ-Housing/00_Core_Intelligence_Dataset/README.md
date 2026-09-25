# 00 - Core Intelligence Benchmark Dataset (OIL / RITES Duliajan Workmen Housing)

This directory houses the foundational core dataset for the **Construction of Workman Housing Complex (BQ Area) on EPC Mode-II at OIL Duliajan, Assam** (`RITES/NERPO/OIL/BQ-HOUSING/25`).

Unlike standard DSR unit-rate tenders with hundreds of separate sheets, this is an **EPC Mode-II design-build tender** where comprehensive technical parameters, engineering calculations, and contractual obligations are concentrated into **7 key benchmark volumes**:

---

## The 7 Core Benchmark Files

| # | Benchmark Item | Original File Name | Description | Key Technical Scope | Direct Download Link |
|---|---|---|---|---|---|
| **1** | **Notice Inviting Tender (NIT)** | `NIT_9_pdf-2025-Aug-28-17-28-23.pdf` | Official NIT conditions, eligibility criteria, EMD (₹80.01 Lakhs), and key milestone schedule. | Estimate ₹160.02 Cr, 24–30 months completion | [Download NIT PDF](https://www.rites.com/Upload/Tender/NIT_9_pdf-2025-Aug-28-17-28-23.pdf) |
| **2** | **Technical Bid Volume** | `Technical_Bid_pdf-2025-Aug-28-19-39-38.pdf` | Comprehensive technical specification volume, GCC, SCC, NBC, and IS code mandates. | CPWD/IS standards, turnkey EPC obligations | [Download Technical Bid](https://www.rites.com/Upload/Tender/Technical_Bid_pdf-2025-Aug-28-19-39-38.pdf) |
| **3** | **Design Basis Report (DBR)** | `DBR_pdf-2025-Aug-28-17-46-57.pdf` | Primary engineering design pack covering Architectural, Structural, and MEP systems. | 192 units, Stilt+6, 3.15m flr ht, GRIHA 3-star, 600mm dia pile criteria | [Download DBR](https://www.rites.com/Upload/Tender/DBR_pdf-2025-Aug-28-17-46-57.pdf) |
| **4** | **BOQ Part 1 (Lump-Sum EPC)** | `BoQ_1_pdf-2025-Aug-28-17-27-34.pdf` | Primary EPC lump-sum schedule of prices and payment stages for the 8 housing towers. | Built-up area breakdown & milestone stages | [Download BOQ Part 1](https://www.rites.com/Upload/Tender/BoQ_1_pdf-2025-Aug-28-17-27-34.pdf) |
| **5** | **Tender Drawing 3 — Structural** | `Tender_drawing_3_pdf-2025-Aug-28-17-39-16.pdf` | Multi-sheet structural volume for Stilt+6 housing towers and G+3 Guest House. | Pile layout (`…/100`), pile cap (`…/101`), beams, Guest House (`…/120–128`) | [Download Drawing 3](https://www.rites.com/Upload/Tender/Tender_drawing_3_pdf-2025-Aug-28-17-39-16.pdf) |
| **6** | **Tender Drawing 4 — Structural & Electrical** | `Tender_drawing_4_pdf-2025-Aug-28-17-39-32.pdf` | Structural drawings for Community Centre (`…/135–142`), Substation ESS (`…/144`), and Electrical MEP (`…/201–209`). | Foundation, columns, beams, lighting, rising mains, SLD & street lighting | [Download Drawing 4](https://www.rites.com/Upload/Tender/Tender_drawing_4_pdf-2025-Aug-28-17-39-32.pdf) |
| **7** | **Geotechnical Investigation Report** | `GT_report_pdf-2025-Aug-28-17-46-44.pdf` | Comprehensive 310-page geotechnical report detailing soil strata and borehole logs. | Sub-surface investigation, N-values, and 600mm pile load capacities | [Download GT Report](https://www.rites.com/Upload/Tender/GT_report_pdf-2025-Aug-28-17-46-44.pdf) |

---

## ⚡ Quick Download Commands

To trigger automated download of these 7 benchmark files into this folder:

```powershell
python ..\scripts\download_core.py
```
*or directly via PowerShell:*
```powershell
..\scripts\download_core.ps1
```
