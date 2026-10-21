# Workflow trace – UC03 Surveillance alert triage

> Personal prototype. Synthetic data, illustrative policy, simulated hedge-fund technology centre.

**1. Intake and priority** – score 3.55, rank 5 of 9
- Surveillance alert triage (Compliance): Pre-sort trade and communications surveillance alerts, draft a disposition rationale for an analyst to approve.
- input: data/use_cases.json (synthetic; 1-5 scores are assumptions)
- score = 0.40 x value 4 + 0.25 x feasibility 3 + 0.20 x readiness 3 + 0.15 x differentiation 4 = 3.55

**2. Risk tier and controls** – high risk
- tier = worse of data sensitivity (5) and model risk (5); low <= 2, medium <= 3, high above
- high-risk bars: eval pass >= 98%, overrides <= 10%, adoption >= 50%, no critical control incident
- human review on every output at every stage
- thresholds: policy-v2 in data/policy.json – illustrative assumptions, not validated requirements; in practice set and approved by the risk, compliance and model-risk owners

**3. Sourcing** – build
- differentiating workflow

**4. Offline evaluation** – no baseline in this dataset
- the gate relies on the weekly evaluation pass rate only
- gap: a high-risk use case should have a recorded offline baseline before it moves up a stage

**5. Live use, weekly gate inputs (pilot)** – last 4 weeks of telemetry (data/telemetry.csv, synthetic)
- every output reviewed by a person before it is acted on
- week 7: adoption 53.3%, eval pass 98.5%, overrides 8%, critical incidents 0
- week 8: adoption 53.3%, eval pass 98.5%, overrides 8%, critical incidents 1
- week 9: adoption 60%, eval pass 98.5%, overrides 8%, critical incidents 0
- week 10: adoption 66.7%, eval pass 98.5%, overrides 8%, critical incidents 0
- metric Adoption = weekly active users / eligible users (named access list); window calendar week; gate reads the latest week, trend over 4 weeks; source tool usage log; owner Use-case product owner; provenance synthetic; week 10: 10 active / 15 eligible
- metric Evaluation pass rate = cases passed / cases run (offline set plus sampled production cases); window weekly evaluation run; source evaluation harness; owner AI engineering lead; provenance synthetic (UC02 offline baseline: measured on a personal prototype); week 10: 98.5%
- metric Override rate = outputs edited or rejected / outputs presented for review; window calendar week; source review / approval log; owner Business process owner; provenance synthetic; week 10: 8%
- metric Critical control incidents = count / n/a; window last 4 weeks for the gate; source incident register (Risk / Compliance); owner Control owner; provenance synthetic; week 10: 1 in the window

**6. Stage gate (checks in order)** – PAUSE
- 1. critical control incident in window? YES, week 8
- later checks are not run: the first failing check decides
- reason: critical control incident in week 8: stop new usage until root cause, fix and re-test are signed off
- reason: high risk tier: every output stays behind human review at any stage
- recorded in out/decision_log.json with policy policy-v2 and inputs SHA-256 5e8e163cf5d5b6a7…

**7. Actions and owned interventions** – 1 intervention(s)
- Suspend new usage; keep read-only access for the review
- Root-cause the incident with Compliance and the control owner
- Add a control test that would have caught it; re-run the evaluation set
- Resume only on written sign-off
- IV07 control fix: Root-cause the week-8 unapproved closure; add a control test that blocks closure without analyst approval; re-run evaluations - owner Compliance control owner, due 2026-10-23, success = critical_incidents = 0

**8. Adoption by cohort** – no cohort data
- adoption 66.7% of 15 eligible users

**9. Value and cost (assumed rates)** – 118 hours saved; net -$27,220
- hours range 83-154 (+/-30% on minutes saved)
- total cost of ownership $37,858, of which one-off $32,400; net excluding one-off $5,180

**10. Decision register and escalation** – 1 recorded decision(s)
- week 6: CONTINUE decided by GenAI steering group, owner Compliance control owner - "Quality strong; adoption 47% below the 50% high-risk bar"; expect critical_incidents == 0 by week 10; actual 1 -> MISSED (data/decision_register.json, synthetic)
- escalation rule: 2 consecutive misses -> sponsor; misses in a row now: 1 -> not yet; one more miss at the next review escalates

**11. What would change the decision** – 1 scenario(s) flip it
- S2 UC03 without the week-8 incident (counterfactual): PAUSE -> EXPAND
