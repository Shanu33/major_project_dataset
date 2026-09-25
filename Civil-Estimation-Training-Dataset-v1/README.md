# Civil Estimation Training Dataset v1

This dataset is the reusable foundation for models that estimate residential RCC building quantities, cost, labour, and duration.

The initial model domain is deliberately narrow:

- reinforced-concrete residential buildings in India;
- multi-storey housing towers and staff/workmen housing; and
- element-level civil trades: foundations, RCC frame, masonry, finishes, and building services.

It is not yet a general estimator for roads, bridges, industrial plants, or every civil project type. Those domains require separate schemas, ground-truth labels, and validation cohorts.

## Dataset logic

```text
Project identity + approved documents
  -> structured element inputs
  -> verified target labels
  -> project-held-out validation
  -> estimation model with confidence and provenance
```

Raw PDFs are retained in each project directory. This release stores only structured, source-linked records that a training pipeline can read.

## Files

- `projects.csv` — one row per project package.
- `building_entities.csv` — modelled building/tower/block within a project.
- `element_inputs.csv` — physical and design inputs with source provenance.
- `estimation_targets.csv` — supervised targets for quantity, cost, labour, and duration. Only `VERIFIED_ACCEPTED` rows may become training labels.
- `document_provenance.csv` — source documents and identity/scope checks.
- `project_intake_template.csv` — blank template for every future project.
- `data_dictionary.md` — definitions and valid statuses.
- `quality_gates.md` — admission rules for inputs and labels.
- `model_task_spec.md` — the first modelling tasks and validation design.

## Seed project

`OIL-RITES-DULIAJAN-BQ-HOUSING-2025` is Project 001. It provides a schema and evidence-control pilot. Its material, cost, labour, and duration estimates are not supervised labels because the item-wise material BOQ validation coverage is 0%.

## Non-negotiable rule

Never train a model on a calculated estimate merely because it is available in a project folder. A training target needs independent project-specific evidence such as an approved itemized BOQ, certified bill/measurement, approved cost breakdown, verified labour record, or approved/actual schedule.
