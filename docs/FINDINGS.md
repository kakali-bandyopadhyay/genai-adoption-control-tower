# FINDINGS – week-10 portfolio review (synthetic data)

All numbers come from `python -m tower build` on the committed inputs. Telemetry is synthetic with conditions planted on purpose; the UC02 offline baseline is a real evaluation of the author's own prototype.

## Portfolio (9 use cases, policy-v1)

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

**Finding 6 – value is counted in hours first.** 1,860 hours saved over ten weeks against $115 of model run cost. Money values (an illustrative $90 an hour) are shown only as a translation; people, licences and infrastructure are not included, so the ratio flatters GenAI and is labelled as such.

## Tests

24 passed: input validation (bad scores, impossible counts), score formula, risk tiers, sourcing rule, the five planted decisions, incident precedence, consecutive-week rule, incident window, human review on high tier, baseline gap, value reconciliation, outputs tied to the input hash, determinism.

## Limitations and next steps

| Limitation | Next step |
|---|---|
| Synthetic telemetry with planted conditions | Feed from real usage logs (events per user, task outcome, override reason) |
| Minutes saved per task are assumptions | Time-and-motion sample per use case before and after |
| Thresholds illustrative | Set with risk, compliance and model-risk owners; version them in policy.json |
| Model run cost only | Add licences, infrastructure and support for total cost of ownership |
| One review week | Trend view across reviews and a decision history per use case |
