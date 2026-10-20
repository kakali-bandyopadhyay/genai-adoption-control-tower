"""Value realised: hours saved (primary measure), run cost, and an illustrative money value."""
from __future__ import annotations


def value(series: list[dict], policy: dict) -> dict:
    hours = round(sum(r["tasks_accepted"] * r["avg_minutes_saved"] for r in series) / 60, 1)
    cost = sum(r["cost_usd"] for r in series)
    rate = policy["value"]["loaded_cost_per_hour_usd"]
    tasks = sum(r["tasks"] for r in series)
    return {"hours_saved": round(hours, 1), "run_cost_usd": round(cost, 2), "tasks": tasks,
            "cost_per_task_usd": round(cost / tasks, 4) if tasks else 0.0,
            "value_usd_illustrative": round(hours * rate), "net_usd_illustrative": round(hours * rate - cost)}
