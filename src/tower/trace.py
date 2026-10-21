"""Workflow trace: one use case's path from intake to escalation, step by step, with the evidence behind each step.

Steps: 1 intake and priority -> 2 risk tier and controls -> 3 sourcing -> 4 offline evaluation -> 5 pilot with human
review (weekly gate inputs) -> 6 stage gate, checks in order -> 7 actions and owned interventions -> 8 adoption by cohort
-> 9 value and cost -> 10 decision register and escalation -> 11 what would change the decision.
Everything is computed from the same context as the dashboard and memo, so the trace cannot disagree with them.
"""
from __future__ import annotations

from .gates import ACTIONS


def _pct(x: float) -> str:
    return f"{x:.0%}" if abs(x * 100 - round(x * 100)) < 1e-9 else f"{x:.1%}"


def _op(i: dict) -> str:
    return "=" if i["measure"] == "critical_incidents" else "<=" if i["measure"] == "override_rate" else ">="


def _usd(x: float) -> str:
    return f"-${-x:,.0f}" if x < 0 else f"${x:,.0f}"


def trace(ctx: dict, uc_id: str) -> list[dict]:
    pr = {u["id"]: u for u in ctx["portfolio"]}
    if uc_id not in pr:
        raise KeyError(f"unknown use case {uc_id}")
    u, pol = pr[uc_id], ctx["policy"]
    d = next((x for x in ctx["decisions"] if x["use_case"] == uc_id), None)
    steps: list[dict] = []

    def add(title: str, outcome: str, detail: list[str]) -> None:
        steps.append({"n": len(steps) + 1, "title": title, "outcome": outcome, "detail": detail})

    w = pol["scoring"]["weights"]
    add("Intake and priority", f"score {u['score']:.2f}, rank {u['rank']} of {len(pr)}",
        [f"{u['name']} ({u['function']}): {u['description']}",
         "input: data/use_cases.json (synthetic; 1-5 scores are assumptions)",
         "score = " + " + ".join(f"{w[k]:.2f} x {k} {u[k]}" for k in w) + f" = {u['score']:.2f}"])

    t = pol["scoring"]["risk_tier"]
    g = pol["gates"][u["tier"]]
    add("Risk tier and controls", f"{u['tier']} risk",
        [f"tier = worse of data sensitivity ({u['data_sensitivity']}) and model risk ({u['model_risk']}); "
         f"low <= {t['low_max']}, medium <= {t['medium_max']}, high above",
         f"{u['tier']}-risk bars: eval pass >= {_pct(g['min_eval_pass'])}, overrides <= {_pct(g['max_override'])}, "
         f"adoption >= {_pct(g['min_adoption'])}, no critical control incident",
         "human review on every output at every stage" if g.get("human_review_required")
         else "human review set per use case",
         f"thresholds: {pol['version']} in data/policy.json – illustrative assumptions, not validated requirements; "
         "in practice set and approved by the risk, compliance and model-risk owners"])

    add("Sourcing", u["sourcing"], [u["sourcing_reason"]])

    b = u.get("baseline_eval")
    if b:
        add("Offline evaluation", f"{b['passed']}/{b['cases'] * b['runs']} passed",
            [f"{b['cases']} cases x {b['runs']} runs; about ${b['cost_per_decision_usd']} per decision; source: {b['source']}",
             f"finding: {b['finding']}"])
    else:
        add("Offline evaluation", "no baseline in this dataset",
            ["the gate relies on the weekly evaluation pass rate only"]
            + (["gap: a high-risk use case should have a recorded offline baseline before it moves up a stage"]
               if u["tier"] == "high" else []))

    if d is None or d["decision"] == "NOT LIVE":
        add("Pilot", "not live", [f"stage: {u['stage'].replace('_', ' ')}; no telemetry, so no gate decision"])
        return steps

    win = d["series"][-pol["decision"]["window_weeks"]:]
    rows = [f"week {r['week']}: adoption {_pct(r['adoption'])}, eval pass {_pct(r['eval_pass_rate'])}, "
            f"overrides {_pct(r['override_rate'])}, critical incidents {r['incidents_critical']}" for r in win]
    reg = {m["id"]: m for m in ctx["metrics"]}
    lw = win[-1]
    raw = {"adoption": f"{lw['weekly_active_users']} active / {lw['eligible_users']} eligible",
           "eval_pass_rate": f"{_pct(lw['eval_pass_rate'])}", "override_rate": f"{_pct(lw['override_rate'])}",
           "critical_incidents": f"{sum(r['incidents_critical'] for r in win)} in the window"}
    prov = [f"metric {reg[k]['name']} = {reg[k]['numerator']} / {reg[k]['denominator']}; window {reg[k]['window']}; "
            f"source {reg[k]['source']}; owner {reg[k]['owner']}; provenance {reg[k]['provenance']}; week {lw['week']}: {raw[k]}"
            for k in ("adoption", "eval_pass_rate", "override_rate", "critical_incidents") if k in reg]
    add(f"Live use, weekly gate inputs ({u['stage'].replace('_', ' ')})", f"last {len(win)} weeks of telemetry (data/telemetry.csv, synthetic)",
        (["every output reviewed by a person before it is acted on"] if g.get("human_review_required") else []) + rows + prov)

    last = win[-1]
    crit = [r["week"] for r in win if r["incidents_critical"] > 0]
    checks = [f"1. critical control incident in window? {'YES, week ' + ', '.join(map(str, crit)) if crit else 'no'}"]
    if not crit:
        q_ok = last["eval_pass_rate"] >= g["min_eval_pass"] and last["override_rate"] <= g["max_override"]
        checks.append(f"2. quality within the {u['tier']}-risk bar? {'yes' if q_ok else 'NO'} "
                      f"(eval {_pct(last['eval_pass_rate'])} vs {_pct(g['min_eval_pass'])}, "
                      f"overrides {_pct(last['override_rate'])} vs {_pct(g['max_override'])})")
        if q_ok:
            a_ok = last["adoption"] >= g["min_adoption"]
            checks.append(f"3. adoption at or above the bar? {'yes' if a_ok else 'NO'} "
                          f"({_pct(last['adoption'])} vs {_pct(g['min_adoption'])})")
            if a_ok:
                checks.append(f"4. every bar met for {pol['decision']['consecutive_weeks_to_expand']}+ consecutive weeks? "
                              f"{'yes' if d['decision'] == 'EXPAND' else 'not yet'}")
    if d["decision"] in ("PAUSE", "FIX"):
        checks.append("later checks are not run: the first failing check decides")
    label = d["decision"] + (f" ({d['fix_type']})" if d.get("fix_type") else "")
    add("Stage gate (checks in order)", label, checks + [f"reason: {r}" for r in d["reasons"]]
        + [f"recorded in out/decision_log.json with policy {pol['version']} and inputs SHA-256 {ctx['fingerprint'][:16]}…"])

    key = d["decision"] + (f"_{d['fix_type']}" if d.get("fix_type") else "")
    ivs = [i for i in ctx["inputs"]["interventions"] if i["use_case"] == uc_id]
    add("Actions and owned interventions", f"{len(ivs)} intervention(s)",
        ACTIONS.get(key, []) + [f"{i['id']} {i['type']}: {i['action']} - owner {i['owner']}, due {i['due']}, "
                                f"success = {i['measure']} {_op(i)} {i['target']}"
                                for i in ivs])

    cs = [c for c in ctx["cohorts"] if c["use_case"] == uc_id]
    add("Adoption by cohort", f"{sum(c['below_bar'] for c in cs)} of {len(cs)} cohort(s) below the bar" if cs else "no cohort data",
        [f"{c['cohort']}: {c['active_users']}/{c['eligible_users']} active = {_pct(c['adoption'])} (bar {_pct(c['bar'])})"
         + (" BELOW" if c["below_bar"] else "") for c in cs]
        or [f"adoption {_pct(last['adoption'])} of {last['eligible_users']} eligible users"])

    tc = ctx["tco"][uc_id]
    add("Value and cost (assumed rates)", f"{tc['hours_saved']:,.0f} hours saved; net {_usd(tc['net_usd'])}",
        [f"hours range {tc['hours_low']:,.0f}-{tc['hours_high']:,.0f} (+/-{pol['costs']['minutes_saved_sensitivity']:.0%} on minutes saved)",
         f"total cost of ownership {_usd(tc['total_cost_usd'])}, of which one-off {_usd(tc['one_off_usd'])}; "
         f"net excluding one-off {_usd(tc['net_excl_one_off_usd'])}"])

    fs = [f for f in ctx["followup"] if f["use_case"] == uc_id]
    esc = any(f.get("escalate") for f in fs)
    need = pol["follow_up"]["escalate_after_consecutive_misses"]
    streak = 0
    for f in fs:
        streak = streak + 1 if f["status"] == "MISSED" else 0 if f["status"] == "MET" else streak
    cond = (f"escalation rule: {need} consecutive misses -> sponsor; misses in a row now: {streak} -> "
            + ("condition met: ESCALATED to the sponsor" if esc else
               f"not yet; one more miss at the next review escalates" if streak == need - 1 else "not met"))
    add("Decision register and escalation", "ESCALATED to sponsor" if esc else (f"{len(fs)} recorded decision(s)" if fs else "no earlier decision"),
        [f"{f['review']}: {f['decision']} decided by {f['decided_by']}, owner {f['owner']} - \"{f['rationale']}\"; expect "
         f"{f['expect']['metric']} {f['expect']['op']} {f['expect']['target']} by {f['review_by']}; "
         f"actual {f['actual'] if f['actual'] is not None else 'n/a'} -> {f['status']} (data/decision_register.json, {f['provenance']})" for f in fs]
        + [cond])

    flips = [s for s in ctx["scenarios"]["scenarios"] if uc_id in s["changed"]]
    add("What would change the decision", f"{len(flips)} scenario(s) flip it" if flips else "no scenario flips it",
        [f"{s['id']} {s['name']}: {s['changed'][uc_id][0]} -> {s['changed'][uc_id][1]}" for s in flips])
    return steps


def as_text(steps: list[dict], uc_id: str) -> str:
    out = [f"Workflow trace {uc_id} (synthetic data, illustrative policy)"]
    for s in steps:
        out.append(f"{s['n']:>2}. {s['title']}: {s['outcome']}")
        out += [f"      - {x}" for x in s["detail"]]
    return "\n".join(out)


def as_markdown(steps: list[dict], uc_id: str, name: str) -> str:
    out = [f"# Workflow trace – {uc_id} {name}", "",
           "> Personal prototype. Synthetic data, illustrative policy, simulated hedge-fund technology centre.", ""]
    for s in steps:
        out.append(f"**{s['n']}. {s['title']}** – {s['outcome']}")
        out += [f"- {x}" for x in s["detail"]] + [""]
    return "\n".join(out)
