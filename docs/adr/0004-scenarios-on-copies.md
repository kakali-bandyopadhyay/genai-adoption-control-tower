# ADR 0004 – What-if scenarios run the same gates on copies of the inputs

**Status:** Accepted (20 Oct 2026)

## Context
Leaders want to challenge a recommendation ("what if overrides drop?", "what if we lowered the bar?"). A separate scenario model would drift from the real logic.

## Decision
Scenarios are data (`data/scenarios.json`): named changes to policy values or telemetry fields. Each is applied to deep copies and run through the same engine; the output lists only the decisions that changed and the first reason the gate gave. Scenarios are static and versioned so results are reproducible; a change that matches nothing fails loudly.

## Consequences
- The scenario table cannot disagree with the gates (same code path, tested).
- It shows where the conclusion is fragile: here the value case (minutes saved), not the gating.
- An interactive panel is left as a next step; reproducibility was chosen over interactivity.
