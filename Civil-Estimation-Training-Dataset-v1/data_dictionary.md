# Data dictionary

## Unit of learning

The model learns at two levels:

1. **Entity level**: one tower, block, building, road segment, bridge package, or other explicitly bounded scope.
2. **Work-item level**: one measurable output such as pile concrete, slab concrete, reinforcement steel, masonry, labour mandays, cost, or duration.

Never mix full-complex targets with a single-tower input entity.

## Input eligibility

`ELIGIBLE_MODEL_INPUT` means the field may be used as a model feature because it has direct, source-linked project evidence. It does not mean it is a target label or a validated estimate.

## Training-label eligibility

Use `ELIGIBLE` only if the target has one of these source types:

- approved itemized BOQ or certified measurement;
- approved cost breakdown, certified RA bill, or equivalent project-specific cost record;
- verified timesheet, muster roll, or site productivity record for labour;
- approved baseline schedule plus actual progress/completion evidence for duration.

Use `NOT_ELIGIBLE` for estimates, generic rates, pro-rata allocations, uncontrolled benchmark values, and quarantined calculations.

## Required target fields

Every target row needs a value, unit, entity id, work item, source type, source reference, target status, and training-label eligibility.

## Minimum target families

- Material quantity: concrete, reinforcement, masonry, formwork, finishes, MEP materials.
- Cost: work-item cost, trade cost, building cost, and total project cost.
- Labour: work-item mandays, trade mandays, crew size, and productivity.
- Duration: work-item duration, milestone duration, critical-path duration, and completion date.

## Valid statuses

- `VERIFIED_ACCEPTED`
- `NOT_VALIDATED`
- `NOT_CALCULATED`
- `ESTIMATED`
- `ASSUMPTION_REQUIRED`
- `UNRESOLVED_CONTRADICTION`
- `QUARANTINED_LEGACY`
