# GenAI Adoption Control Tower – specification v0.2

**Purpose:** show, end to end, how a technology centre can move GenAI from pilots to embedded use with measurable value and risk controls built in from the start.

**Labelling rule:** personal prototype; synthetic data; illustrative policy; no claim to represent any firm. One real input (UC02 offline baseline from the author's prototype), labelled as such.

## Requirements

| # | Requirement | Where |
|---|---|---|
| R1 | Prioritise use cases on value, feasibility, readiness and differentiation | `portfolio.score`, `policy.json` weights |
| R2 | Classify risk from data sensitivity and model risk | `portfolio.risk_tier` |
| R3 | Recommend build, buy or hybrid with a stated reason | `portfolio.sourcing` |
| R4 | Stage gates per risk tier; human review mandatory for high tier | `policy.json` gates, `gates.decide` |
| R5 | Weekly decision: pause on control incidents, fix quality, fix adoption, expand on sustained performance | `gates.decide` |
| R6 | Value realisation in hours saved, run cost, cost per task | `value.value` |
| R7 | Outputs leadership can act on: dashboard, decision memo with actions, decision log | `report` |
| R8 | Every output tied to the exact inputs | SHA-256 input fingerprint |
| R9 | Bad inputs fail loudly | `data` validation |
| R10 | Metric and assumption register: definition, numerator, denominator, window, source, owner, provenance | `data/metrics.json`, dashboard, `metrics` |
| R11 | What-if scenarios on copies of the inputs, showing which decisions change and why | `scenarios`, `data/scenarios.json` |
| R12 | Total cost of ownership with a sensitivity range on minutes saved | `value.tco`, `policy.json` costs |
| R13 | Adoption by cohort and interventions with owner, due date and success measure | `adoption`, `data/cohorts.json`, `data/interventions.json` |
| R14 | Decision register with expected outcomes; follow-up and escalation after repeat misses | `followup`, `data/decision_register.json`, `record` |

## Definition of done (gate before the repo goes public)

- [ ] Runs end to end from a clean GitHub checkout; README steps verified
- [x] pytest passes (35), no hard-coded results
- [x] Data labelled synthetic; policy labelled illustrative; no firm named
- [x] Diagram, ADRs, FINDINGS with numbers from actual runs
- [ ] Every commit scanned for firm or application terms, contact details and secrets; `.env` never committed
- [ ] Independent review passed
