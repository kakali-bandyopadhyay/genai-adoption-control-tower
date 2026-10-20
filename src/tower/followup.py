"""Decision follow-up: check what each recorded decision expected against what happened, and escalate repeat misses."""
from __future__ import annotations

import json
import operator
from datetime import datetime, timezone
from pathlib import Path

OPS = {">=": operator.ge, "<=": operator.le, "==": operator.eq}


def _week(label: str) -> int:
    return int(label.split()[-1])


def metric_at(series: list[dict], metric: str, from_week: int, to_week: int):
    rows = [r for r in series if from_week < r["week"] <= to_week]
    if metric == "critical_incidents":
        return sum(r["incidents_critical"] for r in rows)
    last = next(r for r in series if r["week"] == to_week)
    return last["adoption"] if metric == "adoption" else last[metric]


def check(register: list[dict], decisions: list[dict], policy: dict) -> list[dict]:
    series = {d["use_case"]: d["series"] for d in decisions}
    max_week = max(r["week"] for s in series.values() for r in s)
    out = []
    for e in sorted(register, key=lambda x: (_week(x["review"]), x["use_case"])):
        due = _week(e["review_by"])
        if due > max_week or e["use_case"] not in series:
            out.append({**e, "status": "OPEN", "actual": None})
            continue
        actual = metric_at(series[e["use_case"]], e["expect"]["metric"], _week(e["review"]), due)
        ok = OPS[e["expect"]["op"]](round(actual, 3), e["expect"]["target"])
        out.append({**e, "status": "MET" if ok else "MISSED", "actual": actual})
    n = policy["follow_up"]["escalate_after_consecutive_misses"]
    for uc in {x["use_case"] for x in out}:
        streak = 0
        for x in [y for y in out if y["use_case"] == uc]:
            streak = streak + 1 if x["status"] == "MISSED" else 0
            x["escalate"] = streak >= n
    return out


def record(path: Path, entry: dict, fingerprint: str) -> dict:
    """Append a leadership decision to the register (append-only; existing entries are never rewritten)."""
    for k in ("review", "use_case", "decision", "rationale", "owner", "decided_by", "review_by", "expect"):
        if not entry.get(k):
            raise ValueError(f"a recorded decision needs {k}")
    if entry["expect"]["op"] not in OPS:
        raise ValueError("expect.op must be one of >=, <=, ==")
    reg = json.loads(path.read_text(encoding="utf-8"))
    entry = {**entry, "date": datetime.now(timezone.utc).date().isoformat(), "provenance": "recorded",
             "inputs_sha256": fingerprint}
    reg.append(entry)
    path.write_text(json.dumps(reg, indent=2) + "\n", encoding="utf-8")
    return entry
