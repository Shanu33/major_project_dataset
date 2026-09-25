# User Provided Projects Ingestion Route

Because programmatic access to public e-procurement portals and institutional repositories is blocked by CAPTCHAs, paywalls, and incomplete file uploads (e.g., missing drawings or missing BOQs), the pipeline relies on manual data provision to expand the dataset beyond $N=3$.

## How to Provide a Project

To inject a new project into the dataset, create a folder for it in this directory using the format:
`Stage_19/04_User_Provided_Projects/PROJECT_ID/`

Inside that folder, you must provide:

1. **`drawings/`** directory: Contains the structural (and architectural if necessary) drawings in `.pdf` format.
2. **`boq/`** directory: Contains the Schedule of Quantities / BOQ in `.xls`, `.xlsx`, or `.pdf` format.
3. **`metadata.json`**: A file specifying the project details (Client, Location, Type) and linking the BOQ to the drawings.

## Minimum Requirements

The project will only be accepted if it has **BOTH**:
- Verifiable visual engineering geometry (Drawings)
- Corresponding BOQ Target values (Schedule of Quantities)

Do NOT upload generic CPWD specifications, agreement-to-sale documents, or tender conditions without actual structural drawings.

Once you have placed the files here, the pipeline will automatically detect, validate, extract engineering elements, map them to the BOQ, and append them to the ML feature matrices.

