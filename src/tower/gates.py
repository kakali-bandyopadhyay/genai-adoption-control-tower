"""Stage gates: for each live use case, decide EXPAND, FIX or PAUSE (or CONTINUE) from the last weeks of telemetry.

Order matters and is deliberate: a control incident outranks good numbers; quality outranks adoption; only a use case
that passes every bar for several consecutive weeks moves to the next stage.
"""
from __future__ import annotations

NEXT = {"pilot": "limited_production", "limited_production": "scale", "scale": "scale"}


def _series(rows: list[dict], uc: str) -> list[dict]:
    s = sorted((r for r in rows if r["use_case"] == uc), key=lambda r: r["week"])
    for r in s:
        r["adoption"] = round(r["weekly_active_users"] / r["eligible_users"], 3)
        r["acceptance"] = round(r["tasks_accepted"] / r["tasks"], 3) if r["tasks"] else 0.0
    return s


def _meets(r: dict, g: dict) -> bool:
    return (r["eval_pass_rate"] >= g["min_eval_pass"] and r["override_rate"] <= g["max_override"]
            and r["adoption"] >= g["min_adoption"] and r["incidents_critical"] == 0)


def decide(u: dict, rows: list[dict], policy: dict) -> dict:
    s = _series(rows, u["id"])
    if not s:
        return {"use_case": u["id"], "decision": "NOT LIVE", "reasons": ["no telemetry"], "stage": u["stage"]}
    g = policy["gates"][u["tier"]]
    p = policy["decision"]
    win = s[-p["window_weeks"]:]
    last = s[-1]
    reasons, decision, kind = [], None, None
    crit = [r["week"] for r in win if r["incidents_critical"] > 0]
    if crit:
        decision = "PAUSE"
        reasons.append(f"critical control incident in week {', '.join(map(str, crit))}: stop new usage until root cause, "
                       f"fix and re-test are signed off")
    elif last["eval_pass_rate"] < g["min_eval_pass"] or last["override_rate"] > g["max_override"]:
        decision, kind = "FIX", "quality"
        if last["eval_pass_rate"] < g["min_eval_pass"]:
            reasons.append(f"quality: eval pass {last['eval_pass_rate']:.1%} below the {u['tier']}-risk bar of {g['min_eval_pass']:.0%}")
        if last["override_rate"] > g["max_override"]:
            reasons.append(f"quality: users override {last['override_rate']:.0%} of outputs (max {g['max_override']:.0%})")
        b = u.get("baseline_eval")
        if b:
            reasons.append(f"offline evaluation passed {b['passed']}/{b['cases'] * b['runs']} but production passes "
                           f"{last['eval_pass_rate']:.0%}: the evaluation set under-represents live cases; add sampled production cases")
    elif last["adoption"] < g["min_adoption"]:
        decision, kind = "FIX", "adoption"
        change = win[-1]["adoption"] - win[0]["adoption"]
        reasons.append(f"adoption: {last['adoption']:.0%} of eligible users active (bar {g['min_adoption']:.0%})"
                       + (f", flat over {len(win)} weeks ({change:+.0%})" if change < p["adoption_plateau_delta"] else ""))
    else:
        streak = 0
        for r in reversed(s):
            if not _meets(r, g):
                break
            streak += 1
        if streak >= p["consecutive_weeks_to_expand"] and u["stage"] != "scale":
            decision = "EXPAND"
            reasons.append(f"all {u['tier']}-risk gates met for {streak} consecutive weeks: move to {NEXT[u['stage']].replace('_', ' ')}")
        else:
            decision = "CONTINUE"
            reasons.append(f"gates met for {streak} week(s); {p['consecutive_weeks_to_expand']} needed before expanding")
    if g.get("human_review_required"):
        reasons.append("high risk tier: every output stays behind human review at any stage")
    return {"use_case": u["id"], "name": u["name"], "tier": u["tier"], "stage": u["stage"],
            "next_stage": NEXT[u["stage"]] if decision == "EXPAND" else u["stage"],
            "decision": decision, "fix_type": kind, "reasons": reasons, "series": s, "gate": g}


ACTIONS = {
    "PAUSE": ["Suspend new usage; keep read-only access for the review", "Root-cause the incident with Compliance and the control owner",
              "Add a control test that would have caught it; re-run the evaluation set", "Resume only on written sign-off"],
    "FIX_quality": ["Error analysis by break type on the overridden outputs; owner and date named",
                    "Add sampled production cases to the evaluation set; re-test before the next review",
                    "Keep the use case at its current stage and behind the approval gate"],
    "FIX_adoption": ["Name a champion in each team and embed the tool in the existing workflow (no separate screen)",
                     "Run short role-based enablement sessions; share two worked examples from early users",
                     "Weekly feedback loop: collect blockers, fix the top two, report back to users",
                     "Keep the use case at its current stage until adoption clears the bar"],
    "EXPAND": ["Widen access to the next user group", "Confirm support, training and run-cost budget for the larger group",
               "Keep the same gates; review again after four weeks"],
    "CONTINUE": ["Keep the pilot running; review again next week"],
}


def decide_all(prioritised: list[dict], rows: list[dict], policy: dict) -> list[dict]:
    live = [u for u in prioritised if u["stage"] != "backlog"]
    order = {"PAUSE": 0, "FIX": 1, "EXPAND": 2, "CONTINUE": 3, "NOT LIVE": 4}
    return sorted((decide(u, rows, policy) for u in live), key=lambda d: (order[d["decision"]], d["use_case"]))
