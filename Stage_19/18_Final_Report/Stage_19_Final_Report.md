# Stage 19 Final Report — External Engineering Dataset Acquisition & Recovery

## 1. Executive Summary
**ACQUISITION BLOCKED (AUTOMATED)**
Stage 19 executed a multi-channel acquisition strategy targeting open institutional repositories, public construction documentation, and open datasets (Channels A, B, C, D) globally. Automated and headless acquisition mechanisms failed to produce complete project packages containing both Structural Drawings and Bills of Quantities (BOQs). 

To prevent the pipeline from permanently stalling, **Channel E (User-Provided Project Packages)** has been successfully initialized. The system is now awaiting manual data ingestion to proceed.

## 2. Acquisition Channel Audit
* **Channel A & B (Institutional & Government Portals):** Searched `.edu`, `.ac.in`, and `.gov.in`. Findings were limited to academic course syllabi, standard CPWD specifications, or incomplete tender notices without accompanying blueprint PDFs.
* **Channel C (Contractor / Consultant Documentation):** No open-source, non-proprietary complete building packages were located.
* **Channel D (Alternative Geographic Sources):** Explored open BIM/IFC datasets and GitHub repositories. While quantity takeoff code repositories exist, they lack raw PDF structural drawings mapped to standardized BOQ schedules.
* **Channel E (User-Provided Projects):** Fully initialized. Directory structure and ingestion protocols are established at `Stage_19/04_User_Provided_Projects/`.

## 3. Dataset ML Readiness Metrics
* **N_projects:** 3 (OIL-RITES-Duliajan, NIT-Nalanda, TCIL-Azamgarh)
* **N_elements:** 57
* **N_projects_with_geometry:** 3
* **N_projects_with_BOQ:** 3
* **N_projects_with_geometry_and_BOQ:** 3
* **N_projects_with_verified_XY_mapping:** 3

**Current ML Status:** `NOT_TRAINABLE`
The dataset has not yet reached the critical $N \ge 5$ threshold required for basic grouped cross-validation, nor the preferred $N \ge 10$ for robust out-of-distribution (OOD) generalization testing. 

## 4. Immediate Blockers & Next Steps
**Blocker:**
No additional legitimate projects can be programmatically acquired from open channels due to CAPTCHAs, paywalls, and proprietary data silos.

**Next Action (Human-in-the-Loop required):**
1. Procure 2+ new construction projects (e.g., from personal archives, unlocked institutional access, or manual CAPTCHA bypass).
2. Place the complete packages (Drawings + BOQs + `metadata.json`) into `Stage_19/04_User_Provided_Projects/PROJECT_ID/`.
3. Re-trigger the pipeline to automatically validate the geometry-to-BOQ linkage, populate the CSVs, and update the dataset readiness to `TRAINABLE`.

