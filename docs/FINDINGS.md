# FINDINGS – week-10 portfolio review (synthetic data)

All numbers come from `python -m tower build` on the committed inputs. Telemetry is synthetic with conditions planted on purpose; the UC02 offline baseline is a real evaluation of the author's own prototype.

## Portfolio (9 use cases, policy-v2)

| Rank | Use case | Score | Risk tier | Sourcing | Stage |
|---|---|---|---|---|---|
| 1 | UC02 Trade-break triage assistant | 4.40 | high | build | pilot |
| 2 | UC05 DDQ and RFP drafting | 3.85 | medium | hybrid | limited production |
| 3 | UC06 Code assistant for quant developers | 3.80 | high | hybrid | backlog |
| 4 | UC04 Policy and procedures Q&A | 3.75 | low | buy | pilot |
| 5 | UC03 Surveillance alert triage | 3.55 | high | build | pilot |
| 6 | UC01 Research document summaries | 3.50 | medium | buy | limited production |
| 7 | UC08 Meeting notes and actions | 3.20 | medium | buy | backlog |
| 8 | UC07 Reconciliation exception explanations | 2.80 | high | hybrid | backlog |
| 9 | UC09 Pre-trade restriction lookup | 2.80 | high | build | backlog |

**Finding 1 – the highest-value ideas are the riskiest.** Three of the top five are high risk tier. Ranking on value alone would push them first; the tier sets the bar they must clear (98% eval pass, at most 10% overrides, human review at every stage).

**Finding 2 – sourcing follows sensitivity, not novelty.** The code assistant (UC06) is a commodity capability, but repository code is sensitive, so it is hybrid (vendor model, in-house controls), not a plain purchase.

## Decisions (last week of 10)

| Use case | Adoption | Eval pass | Override | Hours saved | Model run cost | Decision |
|---|---|---|---|---|---|---|
| UC03 Surveillance alert triage | 67% | 98.5% | 8% | 118 | $12 | **PAUSE** |
| UC01 Research document summaries | 22% | 96.0% | 9% | 220 | $18 | **FIX – adoption** |
| UC02 Trade-break triage | 55% | 96.0% | 18% | 336 | $4 | **FIX – quality** |
| UC04 Policy and procedures Q&A | 62% | 98.0% | 6% | 609 | $26 | **EXPAND → limited production** |
| UC05 DDQ and RFP drafting | 72% | 97.0% | 8% | 576 | $56 | **EXPAND → scale** |
| **Total** | 249 weekly active users | | | **1,860** | **$115** | expand 2 · fix 2 · pause 1 |

**Finding 3 – a control incident outranks good numbers.** UC03 had the best quality in the portfolio (98.5%) and healthy adoption, but an alert was closed without analyst approval in week 8. The gate pauses it until the root cause, a new control test and a re-run of the evaluation set are signed off. A dashboard that ranked on averages would have expanded it.

**Finding 4 – offline evaluation is not production quality.** UC02's offline evaluation passed 54/54 (the author's prototype). In production its pass rate is 96% with 18% of outputs overridden: the evaluation set under-represents live break types. The fix is quality work (error analysis by break type, production samples added to the evaluation set), not more users.

**Finding 5 – low adoption needs adoption work, not model work.** UC01's quality clears its bar; usage has been flat at 22% for four weeks. The actions are champions per team, the tool embedded in the existing workflow, short role-based sessions and a weekly feedback loop.

**Finding 6 – value is counted in hours first.** 1,860 hours saved over ten weeks against $115 of model run cost. Money values (an illustrative $90 an hour) are shown only as a translation. Model run cost alone flatters GenAI, so B02 adds total cost of ownership (Finding 9).

## B02 – trust, challenge, act

**Finding 7 – every number now has a definition, an owner and a provenance.** The register lists numerator, denominator, window, source and owner for 9 metrics, and marks each as synthetic, assumed or measured. Only two values are measured: UC02's offline evaluation and cost per task, both from the author's prototype.

**Finding 8 – scenarios show what drives each decision.**

| Scenario | Decision change | Illustrative portfolio net value |
|---|---|---|
| S1 UC02 quality fixed (eval 98.5%, overrides 8% from week 7) | UC02 FIX (quality) → EXPAND | unchanged |
| S2 UC03 without the week-8 incident (counterfactual) | UC03 PAUSE → EXPAND: the incident is the only blocker | unchanged |
| S3 Medium-risk adoption bar lowered to 20% | UC01 FIX (adoption) → EXPAND: would expand a tool 78% of research does not use | unchanged |
| S4 Medium-risk eval bar raised to 97% | UC01 FIX (adoption) → FIX (quality) | unchanged |
| S5 Minutes saved 30% lower | none | $45,845 → −$4,366 |
| S6 Model prices triple | none | $45,845 → $45,614 |

The gates are robust to cost and time-saving assumptions; the value case is not. Model price barely matters next to people time.

**Finding 9 – with total cost of ownership, builds do not pay back in 10 weeks.** Assumed total cost over 10 weeks is about $121.5k across the five live use cases. The two builds (UC02, UC03) each carry $28,800 of one-off build effort and are net negative over 10 weeks, but UC02 is positive excluding one-off costs ($24,826): it needs a longer horizon, not a different decision. The bought policy Q&A (UC04) has the best net value ($23,670 to $56,562 across the ±30% range).

**Finding 10 – adoption gaps are concentrated in cohorts.** UC01 is at 22% overall, but Equity research is at 40% while Credit (10%) and Macro (7%) research barely use it. UC02's Reconciliations team is at 20% while both Settlements teams are above the bar. Each lagging cohort has a named intervention (champion, workflow embedding, training, feedback loop) with owner, due date and success measure.

**Finding 11 – decisions are followed up, and repeat misses escalate.** Of six recorded expectations, two were met (UC04 adoption, UC05 overrides) and four missed. UC01 missed its adoption target at weeks 6 and 10, so it is escalated to the sponsor. UC03's "no critical incidents" expectation was missed by the week-8 incident – the follow-up and the pause agree.

**Finding 12 – the workflow trace makes the order of checks visible.** Trade-break triage (UC02) stops at check 2: quality fails (96% vs 98%, 18% overrides), so its Reconciliations adoption gap (20%) is not the next problem to solve. Surveillance alert triage (UC03) stops at check 1: one critical incident outranks the best quality in the portfolio (98.5%). The trace also flags that UC03, a high-risk use case, has no recorded offline evaluation baseline. Walkthrough: [WORKFLOW_TRACE.md](WORKFLOW_TRACE.md).

## Tests

44 passed. B01: input validation, score formula, risk tiers, sourcing rule, the five planted decisions, incident precedence, consecutive-week rule, incident window, human review on high tier, baseline gap, value reconciliation, outputs tied to the input hash, determinism. B02: metric register coverage and provenance, unregistered measures rejected, cohorts reconcile to telemetry, the six scenario outcomes, scenarios never modify inputs, a scenario that matches nothing fails, cost lines add up, one-off build costs, cohorts below bar have interventions, follow-up statuses and escalation, record validation and append-only, new dashboard and memo sections. Trace: trade-break and surveillance paths, the first failing check decides, trace agrees with every gate decision and with escalation, backlog stops before the gate, build writes traces and the dashboard section.

## Limitations and next steps

| Limitation | Next step |
|---|---|
| Synthetic telemetry with planted conditions | Feed from real usage logs (events per user, task outcome, override reason) |
| Minutes saved per task are assumptions (±30% shown) | Time-and-motion sample per use case before and after |
| Thresholds illustrative | Set with risk, compliance and model-risk owners; version them in policy.json |
| Costs are assumptions in policy.json | Replace with finance actuals per use case |
| Cohort and decision history are snapshots | Weekly cohort telemetry and a full decision history across reviews |
| Scenarios are pre-defined | An interactive scenario panel (kept static here so results are reproducible) |
