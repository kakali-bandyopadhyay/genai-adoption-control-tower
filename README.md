# genai-adoption-control-tower

A working prototype of how a hedge-fund technology centre can run a **GenAI portfolio from pilot to production**: prioritise use cases, choose build, buy or hybrid, put risk-tiered stage gates in front of every expansion, track adoption and value weekly, and turn the numbers into an **expand, fix or pause** decision that leadership can act on – then **check at the next review whether each decision delivered**.

> **Disclaimer.** Personal prototype. All use cases, telemetry and thresholds are **synthetic and illustrative**, written for a fictional hedge-fund technology centre. Nothing here represents any firm's use cases, metrics, policies or views. One input is real: the offline evaluation baseline for UC02 comes from the author's own ops-exception agent prototype (18 cases × 3 runs, 54/54, about $0.0018 per decision).

**Python 3.11+ · standard library only · pytest (35 tests) · no external services**

![Dashboard](docs/dashboard.png)

## How it works

```mermaid
flowchart LR
    subgraph IN["Inputs (data/)"]
        direction TB
        U["use_cases.json<br/>9 use cases, scored 1-5"]
        P["policy.json<br/>weights, risk tiers, gates"]
        T["telemetry.csv<br/>10 weeks x 5 live pilots"]
    end
    U --> PR["1. Prioritise<br/>score, risk tier,<br/>build / buy / hybrid"]
    P --> PR
    PR --> G{"2. Stage gate<br/>per live use case"}
    T --> G
    G -- "critical incident in window" --> PA["PAUSE"]
    G -- "quality below tier bar" --> FQ["FIX: quality"]
    G -- "adoption below bar" --> FA["FIX: adoption"]
    G -- "all gates met 3+ weeks" --> EX["EXPAND"]
    PA --> OUT["3. Outputs<br/>dashboard, decision memo,<br/>decision log + input hash"]
    FQ --> OUT
    FA --> OUT
    EX --> OUT
```

1. **Prioritise.** Score = 0.40 value + 0.25 feasibility + 0.20 readiness + 0.15 differentiation. Risk tier = the worse of data sensitivity and model risk. Sourcing: commodity and not sensitive → buy; differentiating or most sensitive → build; otherwise hybrid (buy the model, build the workflow and controls).
2. **Gate.** Checks run in a fixed order: a **control incident outranks good numbers**, quality outranks adoption, and only a use case that clears every bar for three consecutive weeks moves up a stage. High-risk use cases keep human review at every stage.
3. **Report.** A self-contained HTML dashboard, a leadership decision memo with actions, and a JSON decision log tied to a SHA-256 of the inputs.

**Built to be trusted, challenged and acted on (B02):**

| Feature | What it answers | Command |
|---|---|---|
| **Metric and assumption register** | How is each number defined (numerator, denominator, window), where does it come from, who owns it – and is it synthetic, assumed or measured? | `python -m tower metrics` |
| **What-if scenarios** | Which input or threshold drives each expand / fix / pause? (6 named scenarios on copies of the inputs) | `python -m tower scenarios` |
| **Total cost of ownership** | Model run cost + licences + infrastructure + support + one-off build and change effort, with a ±30% range on minutes saved | `python -m tower value` |
| **Adoption by cohort + interventions** | Which teams are behind, and who does what by when to close the gap (owner, due date, success measure) | dashboard / memo |
| **Decision register + follow-up** | Did last review's decision deliver what it promised? Two consecutive misses escalate to the sponsor | `python -m tower followup`, `python -m tower record` |

## Quickstart (Windows PowerShell; on macOS/Linux use `source .venv/bin/activate`)

```
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
pytest                          # 35 passed
python -m tower portfolio       # ranked portfolio with tier and sourcing
python -m tower gates           # this week's decisions and the reasons
python -m tower scenarios       # what changes each decision
python -m tower followup        # earlier decisions: expected vs actual
python -m tower value           # total cost of ownership, net value ranges (assumed)
python -m tower metrics         # metric and assumption register
python -m tower build           # out/dashboard.html, out/decision_memo.md, out/decision_log.json

# record a leadership decision with an expected outcome (appends to data/decision_register.json)
python -m tower record --use-case UC04 --decision EXPAND --rationale "gates met 4 weeks" --owner "Use-case product owner" --by "GenAI steering group" --review-by "week 14" --expect "adoption >= 0.55"
```

## Week-10 result (synthetic)

| Use case | Stage | Risk | Decision | Why |
|---|---|---|---|---|
| UC03 Surveillance alert triage | pilot | high | **PAUSE** | Critical control incident in week 8, although quality and adoption looked good |
| UC01 Research document summaries | limited production | medium | **FIX (adoption)** | 22% of eligible users active against a 45% bar, flat for four weeks |
| UC02 Trade-break triage | pilot | high | **FIX (quality)** | 96% eval pass against a 98% bar; 18% overrides; offline 54/54 did not carry into production |
| UC04 Policy and procedures Q&A | pilot | low | **EXPAND** | All low-risk gates met for 4 weeks → limited production |
| UC05 DDQ and RFP drafting | limited production | medium | **EXPAND** | All medium-risk gates met for 8 weeks → scale |

**Also from B02:** UC01's adoption miss is the second in a row, so it is escalated to the sponsor; three of eight cohorts are below their bar and each has a named intervention. Lowering the medium-risk adoption bar to 20% would flip UC01 to EXPAND – the scenario shows why that would be the wrong fix. A 30% weaker time saving turns the portfolio's illustrative net value from about $46k to about −$4k without changing a single decision: the value case is the fragile part, not the gating.

Details, numbers and limitations: [docs/FINDINGS.md](docs/FINDINGS.md). Design decisions: [docs/adr](docs/adr). Build guides: [B01](docs/B01_GUIDE.md) · [B02](docs/B02_GUIDE.md).

## Repository

```
src/tower/   validation, portfolio scoring, stage gates, value and TCO, scenarios, follow-up, adoption, reports, CLI
data/        synthetic use cases, policy, telemetry, metric register, cohorts, interventions, decision register, scenarios
tools/       deterministic telemetry generator
tests/       35 tests: scoring, gates, scenarios, TCO, cohorts, follow-up and escalation, register validation, outputs
docs/        SPEC, FINDINGS, B01 and B02 build guides, ADRs, dashboard screenshot
```

## Limitations

Synthetic telemetry, cohorts and decision history with planted conditions; one evaluation baseline from a personal prototype. Hours saved rely on an assumed minutes-per-task (shown with a ±30% range); costs and the hourly rate are assumptions in `policy.json`, labelled as such. Thresholds are illustrative and would be set with the risk, compliance and model-risk owners.

## Licence

MIT – see [LICENSE](LICENSE).
