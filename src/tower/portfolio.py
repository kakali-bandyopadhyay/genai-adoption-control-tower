"""Prioritise the use-case portfolio: attractiveness score, risk tier and a sourcing call (build / buy / hybrid)."""
from __future__ import annotations


def risk_tier(u: dict, policy: dict) -> str:
    worst = max(u["data_sensitivity"], u["model_risk"])
    t = policy["scoring"]["risk_tier"]
    return "low" if worst <= t["low_max"] else "medium" if worst <= t["medium_max"] else "high"


def sourcing(u: dict) -> tuple[str, str]:
    """Rule in policy.json: commodity + not sensitive -> buy; differentiating or most sensitive -> build; else hybrid."""
    if u["differentiation"] >= 4 or u["data_sensitivity"] == 5:
        return "build", ("differentiating workflow" if u["differentiation"] >= 4 else "most sensitive data stays in-house")
    if u["differentiation"] <= 2 and u["data_sensitivity"] <= 3:
        return "buy", "commodity capability, vendor tool with enterprise controls"
    return "hybrid", "buy the model, build the workflow, data access and controls"


def score(u: dict, policy: dict) -> float:
    w = policy["scoring"]["weights"]
    return round(sum(w[k] * u[k] for k in w), 2)


def prioritise(ucs: list[dict], policy: dict) -> list[dict]:
    out = []
    for u in ucs:
        src, why = sourcing(u)
        out.append({**u, "score": score(u, policy), "tier": risk_tier(u, policy), "sourcing": src, "sourcing_reason": why})
    out.sort(key=lambda x: (-x["score"], x["id"]))
    for i, u in enumerate(out, 1):
        u["rank"] = i
    return out
