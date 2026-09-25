# Quality gates

## Gate 1 — Project identity

Every document must match the same project through tender/reference number, client, location, entity scope, document title, or authenticated cross-reference. Documents from another project are quarantined.

## Gate 2 — Entity boundary

Inputs and targets must refer to the same unit of scope. A total-complex cost cannot label one tower. A typical-floor quantity cannot label the whole building unless a documented aggregation rule exists.

## Gate 3 — Feature evidence

Each feature needs a source path and locator. Estimated or assumed values are retained only with their status and assumption id.

## Gate 4 — Label evidence

Targets enter supervised training only with independent project-specific ground truth. A source used to create an estimate cannot also serve as the only evidence that the estimate is correct.

## Gate 5 — Leakage prevention

Split train, validation, and test sets by `project_id`, never by random work-item row. Otherwise nearly identical elements from one project can appear in both training and testing.

## Gate 6 — Domain control

Version 1 admits only reinforced-concrete residential building entities. Road, bridge, industrial, and infrastructure packages remain out of scope until separate domain schemas and label standards are approved.
