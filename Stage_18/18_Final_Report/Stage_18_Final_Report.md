# Stage 18 Final Report — External Project Acquisition & Dataset Expansion

## 1. Executive Summary
**STATUS: ACQUISITION BLOCKED**

Stage 18 attempted to acquire new, complete construction projects from external and public sources to increase the independent project count from $N=3$ to $N \ge 5$. The acquisition criteria strictly required the presence of BOTH primary architectural/structural drawings and corresponding Schedule of Quantities (BOQs) to establish the necessary Engineering Geometry ($X$) $\to$ BOQ Target ($Y$) linkage.

Despite executing programmatic searches across public domains (e.g., eprocure.gov.in, .ac.in, .gov.in domains), the automated acquisition of complete, un-gated project packages (Drawings + BOQ) failed. E-procurement portals in India secure tender documents behind CAPTCHAs, session tokens, and `.rar`/`.zip` archives that cannot be systematically bypassed or scraped via headless scripts without active human intervention or specialized access.

## 2. Projects Searched
* **Target Repositories:** eprocure.gov.in (CPPP), tenderwizard.com, state PWD portals, academic institutional sites (IITs, NITs), and public sector undertakings (CPWD, RITES, BHEL).
* **Queries Executed:**
  - `"schedule of quantities" "structural drawing" tender filetype:pdf site:in`
  - `"structural drawings" "BOQ" civil works filetype:pdf`
  - `tender "structural drawings" "bill of quantities" filetype:pdf`
  - Domain-specific constraints (`site:ac.in`, `site:gov.in`)

## 3. Sources Searched
* DuckDuckGo HTML Search (Failed due to bot protections / syntax limitations)
* Google Search via `googlesearch-python` (Failed due to 429 Too Many Requests / IP blocks)
* Direct cURL to `eprocure.gov.in` (Failed due to ASP.NET/JSP dynamic rendering and CAPTCHA requirements)
* Vertex AI semantic search (Confirmed documentation procedures but provided no direct, un-gated PDF links)

## 4. Why Candidates Failed
No complete candidate projects could be successfully downloaded because:
1. **Gated Access:** Tender documents containing engineering drawings and Excel BOQs are almost universally packed into `.rar`/`.zip` files that require passing a CAPTCHA to download.
2. **IP Blocks:** Programmatic search engines (Google/DuckDuckGo wrappers) actively block headless/automated queries attempting to bulk-download tender PDFs.
3. **Partial Public Data:** When loose PDFs are exposed on university or government domains, they are often just the NIT (Notice Inviting Tender) text or technical specifications, deliberately excluding the massive structural drawing sets.

## 5. Exact Documents Still Required
To break this blocker, human-assisted bulk download or an official data-sharing API is required to obtain:
* **2+ NEW independent projects**
* For each project: The unaltered `.pdf` of the Structural Drawings + the unaltered `.xls` or `.pdf` of the corresponding Schedule of Quantities.

## 6. Current State
* **Current $N_{projects}$:** 3 (OIL-RITES-Duliajan, NIT-Nalanda, TCIL-Azamgarh)
* **Current $N_{elements}$:** 57 verified elements
* **Exact ML Status:** **BLOCKED**. Training an ML model on $N=3$ projects is statistically invalid for evaluating out-of-distribution (OOD) generalization across new construction projects. 

## 7. Conclusion
As instructed, the acquisition stage is officially HALTED. Do not create Stage 19 to repeat this failure. The pipeline remains fully operational, but dataset expansion is starved of raw input data.

