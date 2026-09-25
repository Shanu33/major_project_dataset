# Stage 17 Final Report — Multi-Project Engineering Ground-Truth Expansion

## 1. Executive Summary
**OUTCOME B: ACQUISITION BLOCKER (HARD STOP)**

Stage 17 attempted to scale the supervised engineering dataset from $N=3$ projects (Duliajan, Nalanda, TCIL-Azamgarh) to at least $N \ge 5$. An exhaustive corpus-wide scan was conducted to identify any remaining projects possessing **both** visual engineering geometry (Drawings) and ground-truth targets (BOQ).

The corpus is structurally blocked. No additional projects contain the necessary paired evidence to create valid $X \to Y$ supervised samples without fabricating data.

## 2. Dataset State
* **Starting Projects:** 3
* **Starting Elements:** 57
* **Ending Projects:** 3
* **Ending Elements:** 57

## 3. Findings from Corpus-Wide Discovery
The entire 30-project corpus was scanned for PDFs containing drawings, BOQs, schedules, or architectural layouts. Visual rendering and extraction were performed on the most promising candidates, yielding negative results:

1. **SBI-DN-Nagar-Andheri-122-Flats:** The file named `PART_E_Tender_Drawings.pdf` (65 pages) was visually rendered and found to be a misnamed Notice Inviting Tender (NIT) document, not structural blueprints.
2. **DFCCIL-Sarmatanr-Larabad:** The file named `Tender_Document_Quarter_KQR_HZB_RJ3Y.pdf` (197 pages) within the Architectural Drawings folder was visually rendered and found to be standard tender conditions, not drawings.
3. **SBI-GIFT-City-Twin-Towers:** Contains a massive, highly detailed 162-page BOQ, but completely lacks any associated structural or architectural drawings to extract geometric features ($X$) from.
4. **BMC-Deonar-600-Tenements:** Contains explicit engineering drawings (`ETH_7000022191_DRAWING-4.pdf`), but operates on an EPC framework lacking element-level BOQ target volumes ($Y$).
5. **EPI-Trimbakeshwar-EMRS:** A massive 503-page PDF was analyzed, but visual extraction revealed it to consist of furniture specs and general conditions, lacking structural blueprints.
6. **Other Projects:** Contained either generic CPWD rate files, audit stubs, or CA certificates, rather than primary engineering documents.

## 4. Conclusion & Next Steps
We have hit the fundamental limit of the current dataset corpus. The dataset architecture is fully proven and capable of executing multimodal $X \to Y$ matching (as demonstrated on Duliajan, Nalanda, and TCIL). However, we cannot proceed with further supervised data expansion because the primary visual documents simply do not exist in the remaining corpus directories.

**Recommendation:**
Halt dataset expansion. Do not proceed to ML training, as an $N=3$ independent project count is insufficient for testing a generalized construction-intelligence model. The corpus requires an injection of raw, complete architectural/structural drawing PDFs paired with BOQs from new projects before further dataset scaling can occur.

