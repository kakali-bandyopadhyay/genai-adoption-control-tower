"""Value realised. Hours saved is the primary measure; money is an illustrative translation.

Total cost of ownership = model run cost + licences + infrastructure + support + one-off build and change effort,
all from the assumptions in policy.json["costs"] (labelled assumed). A +/- range on minutes saved shows sensitivity.
"""
from __future__ import annotations


def value(series: list[dict], policy: dict) -> dict:
    hours = round(sum(r["tasks_accepted"] * r["avg_minutes_saved"] for r in series) / 60, 1)
    cost = sum(r["cost_usd"] for r in series)
    rate = policy["value"]["loaded_cost_per_hour_usd"]
    tasks = sum(r["tasks"] for r in series)
    return {"hours_saved": hours, "run_cost_usd": round(cost, 2), "tasks": tasks,
            "cost_per_task_usd": round(cost / tasks, 4) if tasks else 0.0,
            "value_usd_illustrative": round(hours * rate), "net_usd_illustrative": round(hours * rate - cost)}


def tco(u: dict, series: list[dict], policy: dict) -> dict:
    c, rate = policy["costs"], policy["value"]["loaded_cost_per_hour_usd"]
    v = value(series, policy)
    months = c["horizon_weeks"] / 52 * 12
    avg_wau = sum(r["weekly_active_users"] for r in series) / len(series)
    src = u["sourcing"]
    lines = {
        "model run": v["run_cost_usd"],
        "licences": round(c["licence_usd_per_active_user_month"][src] * avg_wau * months, 2),
        "infrastructure": round(c["infrastructure_usd_per_month"][src] * months, 2),
        "support": round(c["support_hours_per_week"] * c["horizon_weeks"] * rate, 2),
        "build (one-off)": round(c["build_one_off_hours"][src] * rate, 2),
        "change (one-off)": round(c["change_enablement_one_off_hours"] * rate, 2),
    }
    total = round(sum(lines.values()), 2)
    s = c["minutes_saved_sensitivity"]
    gross = v["hours_saved"] * rate
    return {"use_case": u["id"], "sourcing": src, "hours_saved": v["hours_saved"],
            "hours_low": round(v["hours_saved"] * (1 - s), 1), "hours_high": round(v["hours_saved"] * (1 + s), 1),
            "cost_lines": lines, "total_cost_usd": total,
            "net_usd": round(gross - total), "net_low_usd": round(gross * (1 - s) - total), "net_high_usd": round(gross * (1 + s) - total),
            "one_off_usd": round(lines["build (one-off)"] + lines["change (one-off)"]),
            "net_excl_one_off_usd": round(gross - (total - lines["build (one-off)"] - lines["change (one-off)"]))}
