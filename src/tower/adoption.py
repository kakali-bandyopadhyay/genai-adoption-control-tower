"""Adoption by cohort and the interventions planned against each gap."""
from __future__ import annotations


def cohorts(cohort_rows: list[dict], decisions: list[dict]) -> list[dict]:
    gate = {d["use_case"]: d["gate"]["min_adoption"] for d in decisions}
    out = []
    for c in cohort_rows:
        a = c["active_users"] / c["eligible_users"]
        bar = gate.get(c["use_case"])
        out.append({**c, "adoption": round(a, 3), "bar": bar, "below_bar": bar is not None and a < bar})
    return out


def plan(interventions: list[dict], decisions: list[dict]) -> list[dict]:
    dec = {d["use_case"]: d["decision"] for d in decisions}
    return sorted(({**x, "decision": dec.get(x["use_case"], "–")} for x in interventions), key=lambda x: (x["due"], x["id"]))
