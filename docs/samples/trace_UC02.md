# Workflow trace – UC02 Trade-break triage assistant

> Personal prototype. Synthetic data, illustrative policy, simulated hedge-fund technology centre.

**1. Intake and priority** – score 4.40, rank 1 of 9
- Trade-break triage assistant (Operations): Classify settlement and reconciliation breaks, propose the next action and route to the owner; actions behind an approval gate.
- input: data/use_cases.json (synthetic; 1-5 scores are assumptions)
- score = 0.40 x value 5 + 0.25 x feasibility 4 + 0.20 x readiness 4 + 0.15 x differentiation 4 = 4.40

**2. Risk tier and controls** – high risk
- tier = worse of data sensitivity (4) and model risk (4); low <= 2, medium <= 3, high above
- high-risk bars: eval pass >= 98%, overrides <= 10%, adoption >= 50%, no critical control incident
- human review on every output at every stage
- thresholds: policy-v2 in data/policy.json – illustrative assumptions, not validated requirements; in practice set and approved by the risk, compliance and model-risk owners

**3. Sourcing** – build
- differentiating workflow

**4. Offline evaluation** – 54/54 passed
- 18 cases x 3 runs; about $0.0018 per decision; source: personal prototype ops-exception-agent (offline evaluation)
- finding: 15 of 54 runs (28%) claimed an action the system had not recorded before the fix; the execution log became the system of record

**5. Live use, weekly gate inputs (pilot)** – last 4 weeks of telemetry (data/telemetry.csv, synthetic)
- every output reviewed by a person before it is acted on
- week 7: adoption 55%, eval pass 96%, overrides 18%, critical incidents 0
- week 8: adoption 55%, eval pass 96%, overrides 18%, critical incidents 0
- week 9: adoption 55%, eval pass 96%, overrides 18%, critical incidents 0
- week 10: adoption 55%, eval pass 96%, overrides 18%, critical incidents 0
- metric Adoption = weekly active users / eligible users (named access list); window calendar week; gate reads the latest week, trend over 4 weeks; source tool usage log; owner Use-case product owner; provenance synthetic; week 10: 22 active / 40 eligible
- metric Evaluation pass rate = cases passed / cases run (offline set plus sampled production cases); window weekly evaluation run; source evaluation harness; owner AI engineering lead; provenance synthetic (UC02 offline baseline: measured on a personal prototype); week 10: 96%
- metric Override rate = outputs edited or rejected / outputs presented for review; window calendar week; source review / approval log; owner Business process owner; provenance synthetic; week 10: 18%
- metric Critical control incidents = count / n/a; window last 4 weeks for the gate; source incident register (Risk / Compliance); owner Control owner; provenance synthetic; week 10: 0 in the window

**6. Stage gate (checks in order)** – FIX (quality)
- 1. critical control incident in window? no
- 2. quality within the high-risk bar? NO (eval 96% vs 98%, overrides 18% vs 10%)
- later checks are not run: the first failing check decides
- reason: quality: eval pass 96.0% below the high-risk bar of 98%
- reason: quality: users override 18% of outputs (max 10%)
- reason: offline evaluation passed 54/54 but production passes 96%: the evaluation set under-represents live cases; add sampled production cases
- reason: high risk tier: every output stays behind human review at any stage
- recorded in out/decision_log.json with policy policy-v2 and inputs SHA-256 5e8e163cf5d5b6a7…

**7. Actions and owned interventions** – 2 intervention(s)
- Error analysis by break type on the overridden outputs; owner and date named
- Add sampled production cases to the evaluation set; re-test before the next review
- Keep the use case at its current stage and behind the approval gate
- IV05 quality fix: Error analysis of overridden outputs by break type; add 40 sampled production cases to the evaluation set - owner AI engineering lead, due 2026-10-30, success = eval_pass_rate >= 0.98
- IV06 training: Walk-through of the approval gate and override reasons with the reconciliations team - owner Operations process owner, due 2026-10-27, success = override_rate <= 0.1

**8. Adoption by cohort** – 1 of 3 cohort(s) below the bar
- Settlements – EMEA: 11/15 active = 73.3% (bar 50%)
- Settlements – Americas: 9/15 active = 60% (bar 50%)
- Reconciliations: 2/10 active = 20% (bar 50%) BELOW

**9. Value and cost (assumed rates)** – 336 hours saved; net -$7,574
- hours range 236-437 (+/-30% on minutes saved)
- total cost of ownership $37,850, of which one-off $32,400; net excluding one-off $24,826

**10. Decision register and escalation** – 1 recorded decision(s)
- week 6: FIX decided by GenAI steering group, owner AI engineering lead - "Eval pass 95% against a 98% high-risk bar; overrides 20%"; expect eval_pass_rate >= 0.98 by week 10; actual 0.96 -> MISSED (data/decision_register.json, synthetic)
- escalation rule: 2 consecutive misses -> sponsor; misses in a row now: 1 -> not yet; one more miss at the next review escalates

**11. What would change the decision** – 1 scenario(s) flip it
- S1 UC02 quality fixed: FIX (quality) -> EXPAND
