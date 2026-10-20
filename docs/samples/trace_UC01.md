# Workflow trace – UC01 Research document summaries

> Personal prototype. Synthetic data, illustrative policy, fictional hedge-fund technology centre.

**1. Intake and priority** – score 3.50, rank 6 of 9
- Research document summaries (Research): Summarise filings and earnings-call transcripts into a standard research note template with citations.
- input: data/use_cases.json (synthetic; 1-5 scores are assumptions)
- score = 0.40 x value 4 + 0.25 x feasibility 4 + 0.20 x readiness 3 + 0.15 x differentiation 2 = 3.50

**2. Risk tier and controls** – medium risk
- tier = worse of data sensitivity (2) and model risk (3); low <= 2, medium <= 3, high above
- medium-risk bars: eval pass >= 95%, overrides <= 15%, adoption >= 45%, no critical control incident
- human review set per use case
- thresholds: policy-v2 in data/policy.json – illustrative assumptions, not validated requirements; in practice set and approved by the risk, compliance and model-risk owners

**3. Sourcing** – buy
- commodity capability, vendor tool with enterprise controls

**4. Offline evaluation** – no baseline in this dataset
- the gate relies on the weekly evaluation pass rate only

**5. Live use, weekly gate inputs (limited production)** – last 4 weeks of telemetry (data/telemetry.csv, synthetic)
- week 7: adoption 21.7%, eval pass 96%, overrides 9%, critical incidents 0
- week 8: adoption 21.7%, eval pass 96%, overrides 9%, critical incidents 0
- week 9: adoption 21.7%, eval pass 96%, overrides 9%, critical incidents 0
- week 10: adoption 21.7%, eval pass 96%, overrides 9%, critical incidents 0
- metric Adoption = weekly active users / eligible users (named access list); window calendar week; gate reads the latest week, trend over 4 weeks; source tool usage log; owner Use-case product owner; provenance synthetic; week 10: 13 active / 60 eligible
- metric Evaluation pass rate = cases passed / cases run (offline set plus sampled production cases); window weekly evaluation run; source evaluation harness; owner AI engineering lead; provenance synthetic (UC02 offline baseline: measured on a personal prototype); week 10: 96%
- metric Override rate = outputs edited or rejected / outputs presented for review; window calendar week; source review / approval log; owner Business process owner; provenance synthetic; week 10: 9%
- metric Critical control incidents = count / n/a; window last 4 weeks for the gate; source incident register (Risk / Compliance); owner Control owner; provenance synthetic; week 10: 0 in the window

**6. Stage gate (checks in order)** – FIX (adoption)
- 1. critical control incident in window? no
- 2. quality within the medium-risk bar? yes (eval 96% vs 95%, overrides 9% vs 15%)
- 3. adoption at or above the bar? NO (21.7% vs 45%)
- later checks are not run: the first failing check decides
- reason: adoption: 22% of eligible users active (bar 45%), flat over 4 weeks (+0%)
- recorded in out/decision_log.json with policy policy-v2 and inputs SHA-256 5e8e163cf5d5b6a7…

**7. Actions and owned interventions** – 4 intervention(s)
- Name a champion in each team and embed the tool in the existing workflow (no separate screen)
- Run short role-based enablement sessions; share two worked examples from early users
- Weekly feedback loop: collect blockers, fix the top two, report back to users
- Keep the use case at its current stage until adoption clears the bar
- IV01 champion: Name one champion per credit desk; weekly 15-minute show-and-tell of a real summary - owner Head of credit research (sponsor), due 2026-10-23, success = adoption >= 0.35
- IV02 workflow: Embed the summary in the existing research-note template instead of a separate screen - owner Research tooling lead, due 2026-10-30, success = adoption >= 0.3
- IV03 training: Two 30-minute role-based sessions with worked examples from Equity research - owner AI enablement lead, due 2026-10-23, success = adoption >= 0.45
- IV04 feedback loop: Weekly blocker survey; fix the top two blockers and report back to users - owner Use-case product owner, due 2026-11-06, success = adoption >= 0.45

**8. Adoption by cohort** – 3 of 3 cohort(s) below the bar
- Equity research: 10/25 active = 40% (bar 45%) BELOW
- Credit research: 2/20 active = 10% (bar 45%) BELOW
- Macro research: 1/15 active = 6.7% (bar 45%) BELOW

**9. Value and cost (assumed rates)** – 220 hours saved; net $11,765
- hours range 154-286 (+/-30% on minutes saved)
- total cost of ownership $8,035, of which one-off $3,600; net excluding one-off $15,365

**10. Decision register and escalation** – ESCALATED to sponsor
- week 2: FIX decided by GenAI steering group, owner Research tooling lead - "Adoption 15% after launch"; expect adoption >= 0.25 by week 6; actual 0.217 -> MISSED (data/decision_register.json, synthetic)
- week 6: FIX decided by GenAI steering group, owner Research tooling lead - "Adoption 22% and flat; quality fine"; expect adoption >= 0.3 by week 10; actual 0.217 -> MISSED (data/decision_register.json, synthetic)
- escalation rule: 2 consecutive misses -> sponsor; misses in a row now: 2 -> condition met: ESCALATED to the sponsor

**11. What would change the decision** – 2 scenario(s) flip it
- S3 Medium-risk adoption bar lowered to 20%: FIX (adoption) -> EXPAND
- S4 Medium-risk eval bar raised to 97%: FIX (adoption) -> FIX (quality)
