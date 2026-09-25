# Acquisition Waiting

Pipeline is waiting for user-provided complete project packages.

## Required Package Specification
To proceed, please supply at least 2 genuinely independent project packages in the following directory:
`/home/shahnawaz/Documents/DataRequirement/Stage_19/04_User_Provided_Projects/`

### Minimum Useful Package Structure
```text
PROJECT_ID/
├── drawings/
│   ├── architectural PDFs
│   └── structural PDFs
├── boq/
│   ├── BOQ PDF/XLSX
│   └── measurement sheets if available
└── metadata.json
```

### Ideal Package Contents
The package should ideally contain at least:
1. Structural drawings
2. Architectural drawings where relevant
3. BOQ (Bill of Quantities / Schedule of Quantities)
4. Measurement/takeoff sheets where available
5. Project/tender identification
6. Source information

Once packages are provided, re-trigger the pipeline to parse, extract, map, and assess ML readiness.

