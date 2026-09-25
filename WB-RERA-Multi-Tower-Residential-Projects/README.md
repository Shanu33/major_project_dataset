# WB RERA Multi-Tower Residential Projects (TKD Series and Other Private Developer Projects)

## 1. Project Identity & Verification Summary

- **Official Project Title:** WB RERA Multi-Tower Residential Projects (TKD Series and Other Private Developer Projects)
- **Tender Reference / ID:** `Multiple (WBRERA / HIRA ProCode & Registration Numbers)`
- **Client / Authority:** West Bengal Real Estate Regulatory Authority (WBRERA / HIRA)
- **Official / Public Status:** Official (rera.wb.gov.in)
- **Document Date / Period:** 2019-2025
- **Dataset Classification:** **Reference only**

### Official Public Sources & Download Links
- **WBRERA Official Portal:** [https://rera.wb.gov.in](https://rera.wb.gov.in)

## 2. Selected Single-Building Model Scope

```text
Selected model scope:
Building / Tower / Block / Type: Tarang Tower 6 (Sanctioned High-Rise Tower)
Number of floors: G+10 Floors
Drawing reference: Sanctioned building plans, floor plates, elevation sheets & TKD structural series
Matching BOQ section: Promoter audited financial declarations
Reason selected: Sanctioned municipal building plan, floor plates, elevation sheets & structural series.
```

## 3. Same-Project Dataset Audit Table

| Dataset requirement | Status | Exact file(s) present | Same-project verified | Action required |
| :--- | :---: | :--- | :---: | :--- |
| Tender/NIT | **Missing** | None | No | Private residential projects - no public tender via WBRERA |
| Project scope | **Present** | WBRERA_Project_Summaries.md | Yes | 1-7 towers per project scope |
| Architectural drawings | **Present** | Sanctioned_Building_Plans.md | Yes | Sanctioned floor and elevation plans |
| Structural drawings | **Partial** | TKD_Structural_Series.md | Yes | Foundation & column drawings for JKN/TKD |
| Civil specifications | **Partial** | Promoter_Specifications.md | Yes | Pile foundation parameters in filings |
| BOQ with quantities | **Missing** | None | No | Private projects without contractor BOQ |
| Cost/rates | **Partial** | Audited_Financial_Declarations.md | Yes | Declared project costs in audited filings |
| Time schedule | **Partial** | Statutory_Completion_Dates.md | Yes | Completion targets declared in filings |
| Soil/geotechnical report | **Missing** | None | No | Geotechnical data missing |
| MEP drawings | **Present** | Services_and_Sanitary_Notes.md | Yes | Sanctioned services outline |
| Actual execution records | **Partial** | Handover_Milestones_Log.md | Yes | WBRERA registration & CC milestones |

## 4. Final Classification & Suitability

### **Classification: Reference only**
*Useful private multi-tower benchmark (Sanctioned plans, typical floor plates, TKD structural series)*

## 5. Canonical Directory Hierarchy

```text
WB-RERA-Multi-Tower-Residential-Projects/
│
├── 00_Core_Intelligence_Dataset/
├── 01_Tender_NIT_PreBid/
├── 02_Cost_BOQ_Makes/
├── 03_Technical_Specifications_Reports/
├── 04_Architectural_Drawings/
├── 05_Structural_Drawings/
├── 06_MEP_Services/
├── 07_Landscape_Infrastructure/
├── 08_Execution_Actuals/
├── 99_Unverified_or_Related_References/
├── file_manifest.csv
└── README.md
```

Total cataloged entries: **13 files**. Refer to [`file_manifest.csv`](file_manifest.csv) for full provenance and duplicate tags.
