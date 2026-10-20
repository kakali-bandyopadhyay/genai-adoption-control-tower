"""Load and validate the inputs (stdlib only). Bad inputs fail loudly with the row that is wrong."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[2] / "data"
USE_CASE_FIELDS = ("value", "feasibility", "readiness", "differentiation", "data_sensitivity", "model_risk")
STAGES = ("backlog", "pilot", "limited_production", "scale")
NUMERIC = ("week", "eligible_users", "weekly_active_users", "tasks", "tasks_accepted", "avg_minutes_saved",
           "override_rate", "eval_pass_rate", "cost_usd", "incidents_critical", "incidents_minor")


def load_policy(d: Path = DATA) -> dict:
    return json.loads((d / "policy.json").read_text(encoding="utf-8"))


def load_use_cases(d: Path = DATA) -> list[dict]:
    ucs = json.loads((d / "use_cases.json").read_text(encoding="utf-8"))
    seen = set()
    for u in ucs:
        if u["id"] in seen:
            raise ValueError(f"duplicate use case id {u['id']}")
        seen.add(u["id"])
        for f in USE_CASE_FIELDS:
            if not (isinstance(u[f], int) and 1 <= u[f] <= 5):
                raise ValueError(f"{u['id']}: {f} must be an integer 1-5 (got {u[f]!r})")
        if u["stage"] not in STAGES:
            raise ValueError(f"{u['id']}: unknown stage {u['stage']!r}")
    return ucs


def load_telemetry(d: Path = DATA) -> list[dict]:
    rows = []
    with (d / "telemetry.csv").open(encoding="utf-8") as f:
        for i, r in enumerate(csv.DictReader(f), start=2):
            for k in NUMERIC:
                r[k] = float(r[k]) if "." in r[k] or k.endswith("rate") else int(r[k])
            if r["weekly_active_users"] > r["eligible_users"] or r["tasks_accepted"] > r["tasks"]:
                raise ValueError(f"telemetry line {i}: impossible counts for {r['use_case']} week {r['week']}")
            for k in ("override_rate", "eval_pass_rate"):
                if not 0 <= r[k] <= 1:
                    raise ValueError(f"telemetry line {i}: {k} out of range")
            rows.append(r)
    return rows


def fingerprint(d: Path = DATA) -> str:
    """SHA-256 over the three input files, so every decision can be tied to the exact inputs it used."""
    h = hashlib.sha256()
    for name in ("policy.json", "use_cases.json", "telemetry.csv"):
        h.update((d / name).read_bytes().replace(b"\r\n", b"\n"))   # line-ending independent (Windows / Linux)
    return h.hexdigest()


def load_json(name: str, d: Path = DATA):
    return json.loads((d / name).read_text(encoding="utf-8"))


def load_all(d: Path = DATA) -> dict:
    """Everything the tower reads, validated together (cross-file checks live here)."""
    pol, ucs, rows = load_policy(d), load_use_cases(d), load_telemetry(d)
    metrics = load_json("metrics.json", d)
    cohorts = load_json("cohorts.json", d)
    interventions = load_json("interventions.json", d)
    register = load_json("decision_register.json", d)
    scenarios = load_json("scenarios.json", d)
    ids = {u["id"] for u in ucs}
    metric_ids = {m["id"] for m in metrics}
    for m in metrics:
        for k in ("definition", "numerator", "denominator", "window", "source", "owner", "provenance"):
            if not m.get(k):
                raise ValueError(f"metric {m['id']}: {k} missing")
    for x in interventions:
        if x["use_case"] not in ids:
            raise ValueError(f"intervention {x['id']}: unknown use case {x['use_case']}")
        if x["measure"] not in metric_ids:
            raise ValueError(f"intervention {x['id']}: measure {x['measure']} not in the metric register")
        for k in ("owner", "due", "action"):
            if not x.get(k):
                raise ValueError(f"intervention {x['id']}: {k} missing")
    for e in register:
        if e["use_case"] not in ids or e["expect"]["metric"] not in metric_ids:
            raise ValueError(f"decision register entry {e['use_case']} {e['review']}: unknown use case or metric")
    last_week = max(r["week"] for r in rows)
    for uc in {c["use_case"] for c in cohorts}:
        cs = [c for c in cohorts if c["use_case"] == uc]
        last = next(r for r in rows if r["use_case"] == uc and r["week"] == last_week)
        if sum(c["eligible_users"] for c in cs) != last["eligible_users"] or sum(c["active_users"] for c in cs) != last["weekly_active_users"]:
            raise ValueError(f"cohorts for {uc} do not add up to the week-{last_week} telemetry")
    return {"policy": pol, "use_cases": ucs, "telemetry": rows, "metrics": metrics, "cohorts": cohorts,
            "interventions": interventions, "register": register, "scenarios": scenarios}


def fingerprint_all(d: Path = DATA) -> str:
    h = hashlib.sha256()
    for name in ("policy.json", "use_cases.json", "telemetry.csv", "metrics.json", "cohorts.json",
                 "interventions.json", "decision_register.json", "scenarios.json"):
        h.update((d / name).read_bytes().replace(b"\r\n", b"\n"))   # line-ending independent (Windows / Linux)
    return h.hexdigest()
