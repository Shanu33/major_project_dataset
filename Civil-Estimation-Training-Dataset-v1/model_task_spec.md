# Model task specification

## v1 domain

Estimate work-item quantities, cost, labour, and duration for reinforced-concrete residential buildings from structured, source-linked design and scope inputs.

## Separate tasks

Train separate models rather than one opaque all-purpose model:

1. Quantity model: element inputs -> material quantity by work item and unit.
2. Cost model: validated quantities plus project conditions -> work-item or entity cost.
3. Labour model: validated quantities plus method and crew evidence -> trade mandays.
4. Duration model: work packages, dependency logic, resources, and productivity -> activity duration or milestone duration.

Every prediction must return:

- prediction value and unit;
- confidence interval or calibrated uncertainty band;
- comparable projects used by the model;
- feature provenance;
- warning when the input project falls outside the trained domain.

## Dataset growth sequence

1. Finish Duliajan evidence recovery and add labels only when verified.
2. Add comparable residential tower packages through `project_intake_template.csv`.
3. Normalize entities and work items into the shared CSV tables.
4. Build a project-held-out validation cohort.
5. Train only after enough independently labelled projects exist for each target family.

## Success criterion

The first release should estimate one clearly defined work item for a comparable residential tower with an evidence trace and uncertainty range. It should not claim to replace a civil engineer or estimate unrelated civil domains.
