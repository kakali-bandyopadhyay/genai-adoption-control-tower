"""What-if scenarios: apply named changes to copies of the policy or telemetry, re-run, compare with the baseline."""
from __future__ import annotations

import copy

from . import engine
from .value import tco


def _apply(policy: dict, rows: list[dict], changes: list[dict]) -> tuple[dict, list[dict]]:
    pol, rs = copy.deepcopy(policy), copy.deepcopy(rows)
    for ch in changes:
        if ch["target"] == "policy":
            node = pol
            for k in ch["path"][:-1]:
                node = node[k]
            last = ch["path"][-1]
            if last not in node:
                raise KeyError(f"policy path {ch['path']} not found")
            node[last] = ch["value"] if ch["op"] == "set" else node[last] * ch["value"]
        elif ch["target"] == "telemetry":
            hit = 0
            for r in rs:
                if (ch["use_case"] in ("*", r["use_case"])) and r["week"] >= ch["from_week"]:
                    r[ch["field"]] = ch["value"] if ch["op"] == "set" else round(r[ch["field"]] * ch["value"], 6)
                    hit += 1
            if not hit:
                raise ValueError(f"scenario change matched no telemetry rows: {ch}")
        else:
            raise ValueError(f"unknown scenario target {ch['target']}")
    return pol, rs


def run(inputs: dict) -> dict:
    base_pr, base_ds = engine.evaluate(inputs["policy"], inputs["use_cases"], inputs["telemetry"])
    base = {d["use_case"]: d for d in base_ds}

    def label(d):
        return d["decision"] + (f" ({d['fix_type']})" if d.get("fix_type") else "")
    by_id = {u["id"]: u for u in base_pr}

    def total_net(pol, ds):
        return sum(tco(by_id[d["use_case"]], d["series"], pol)["net_usd"] for d in ds)

    out = []
    for sc in inputs["scenarios"]:
        pol, rs = _apply(inputs["policy"], inputs["telemetry"], sc["changes"])
        _, ds = engine.evaluate(pol, inputs["use_cases"], rs)
        res = {d["use_case"]: d for d in ds}
        changed = {k: (label(base[k]), label(res[k])) for k in base if label(base[k]) != label(res[k])}
        out.append({"id": sc["id"], "name": sc["name"], "question": sc["question"],
                    "decisions": {k: label(res[k]) for k in sorted(res)}, "changed": changed,
                    "drivers": {k: res[k]["reasons"][0] for k in changed},
                    "net_usd": total_net(pol, ds), "base_net_usd": total_net(inputs["policy"], base_ds),
                    "changes": sc["changes"]})
    return {"baseline": {k: label(base[k]) for k in sorted(base)}, "scenarios": out}
