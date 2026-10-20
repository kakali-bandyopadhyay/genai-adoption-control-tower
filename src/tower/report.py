"""Outputs: a self-contained HTML dashboard, a leadership decision memo (Markdown) and a decision log (JSON)."""
from __future__ import annotations

import html
import json
from datetime import datetime, timezone

from .value import value

LABEL = ("Personal prototype. Synthetic data and an illustrative policy for a fictional hedge-fund technology centre; "
         "not any firm's use cases, metrics or policy. One baseline (UC02) is a real offline evaluation of the author's own prototype.")
COLOURS = {"EXPAND": "#2e7d32", "FIX": "#b26a00", "PAUSE": "#c62828", "CONTINUE": "#546e7a", "NOT LIVE": "#546e7a"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def summary(decisions: list[dict], policy: dict) -> dict:
    vals = [value(d["series"], policy) for d in decisions]
    last = [d["series"][-1] for d in decisions]
    return {"live": len(decisions),
            "weekly_active_users": sum(r["weekly_active_users"] for r in last),
            "hours_saved": round(sum(v["hours_saved"] for v in vals), 1),
            "run_cost_usd": round(sum(v["run_cost_usd"] for v in vals), 2),
            "critical_incidents": sum(r["incidents_critical"] for d in decisions for r in d["series"]),
            "decisions": {k: sum(d["decision"] == k for d in decisions) for k in ("EXPAND", "FIX", "PAUSE", "CONTINUE")}}


def _spark(values: list[float], w: int = 180, h: int = 56, bar: float | None = None) -> str:
    lo, hi = 0.0, max(1.0, max(values))
    pts = [(i * (w - 8) / (len(values) - 1) + 4, h - 4 - (v - lo) / (hi - lo) * (h - 8)) for i, v in enumerate(values)]
    path = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}" for i, (x, y) in enumerate(pts))
    ref = ""
    if bar is not None:
        y = h - 4 - bar * (h - 8)
        ref = f'<line x1="4" x2="{w-4}" y1="{y:.1f}" y2="{y:.1f}" class="bar"/>'
    return (f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="weekly adoption trend">{ref}'
            f'<path d="{path}" class="line"/><circle cx="{pts[-1][0]:.1f}" cy="{pts[-1][1]:.1f}" r="3" class="dot"/></svg>')


def dashboard(prioritised: list[dict], decisions: list[dict], policy: dict, fingerprint: str) -> str:
    e = html.escape
    s = summary(decisions, policy)
    tiles = [("Live use cases", s["live"]), ("Weekly active users", s["weekly_active_users"]),
             ("Hours saved (10 wks)", f"{s['hours_saved']:,.0f}"), ("Model run cost (10 wks)", f"${s['run_cost_usd']:,.0f}"),
             ("Critical incidents", s["critical_incidents"])]
    tile_html = "".join(f'<div class="tile"><div class="k">{e(str(v))}</div><div class="l">{e(k)}</div></div>' for k, v in tiles)
    port = "".join(
        f"<tr><td>{u['rank']}</td><td>{u['id']}</td><td>{e(u['name'])}<div class='sub'>{e(u['function'])}</div></td>"
        f"<td class='num'>{u['score']:.2f}</td><td><span class='tier {u['tier']}'>{u['tier']}</span></td>"
        f"<td>{u['sourcing']}<div class='sub'>{e(u['sourcing_reason'])}</div></td><td>{e(u['stage'].replace('_', ' '))}</td></tr>"
        for u in prioritised)
    cards = []
    for d in decisions:
        v = value(d["series"], policy)
        last = d["series"][-1]
        reasons = "".join(f"<li>{e(r)}</li>" for r in d["reasons"])
        cards.append(
            f'<section class="card"><div class="head"><div><b>{d["use_case"]} · {e(d["name"])}</b>'
            f'<div class="sub">{e(d["stage"].replace("_", " "))} · {d["tier"]} risk</div></div>'
            f'<span class="badge" style="background:{COLOURS[d["decision"]]}">{d["decision"]}</span></div>'
            f'<div class="row">{_spark([r["adoption"] for r in d["series"]], bar=d["gate"]["min_adoption"])}'
            f'<table class="mini"><tr><td>Adoption</td><td>{last["adoption"]:.0%}</td></tr>'
            f'<tr><td>Eval pass</td><td>{last["eval_pass_rate"]:.1%}</td></tr>'
            f'<tr><td>Override</td><td>{last["override_rate"]:.0%}</td></tr>'
            f'<tr><td>Hours saved</td><td>{v["hours_saved"]:,.0f}</td></tr>'
            f'<tr><td>Cost / task</td><td>${v["cost_per_task_usd"]:.4f}</td></tr></table></div>'
            f'<ul class="why">{reasons}</ul></section>')
    gate_rows = "".join(f"<tr><td>{t}</td><td>{g['min_eval_pass']:.0%}</td><td>{g['max_override']:.0%}</td><td>{g['min_adoption']:.0%}</td>"
                        f"<td>{'yes' if g.get('human_review_required') else 'per use case'}</td></tr>" for t, g in policy["gates"].items())
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>GenAI Adoption Control Tower</title><style>
:root{{--bg:#ffffff;--fg:#1d2330;--muted:#5b6475;--line:#dde2ea;--card:#f7f9fc;--accent:#2f6fde}}
@media (prefers-color-scheme:dark){{:root{{--bg:#12151b;--fg:#e7eaf0;--muted:#a3abba;--line:#2b313c;--card:#1a1e26;--accent:#7aa7ff}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}}
main{{max-width:1100px;margin:0 auto;padding:24px 16px}} h1{{font-size:22px;margin:0 0 4px}} h2{{font-size:16px;margin:28px 0 10px}}
.label{{color:var(--muted);font-size:12.5px;border-left:3px solid var(--accent);padding:6px 10px;background:var(--card);margin:10px 0 18px}}
.tiles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}}
.tile{{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px}} .k{{font-size:22px;font-weight:600}} .l{{color:var(--muted);font-size:12px}}
table{{border-collapse:collapse;width:100%}} th,td{{text-align:left;padding:7px 8px;border-bottom:1px solid var(--line);vertical-align:top}}
th{{font-size:12px;color:var(--muted);font-weight:600}} .num{{text-align:right}} .sub{{color:var(--muted);font-size:12px}}
.tier{{padding:1px 8px;border-radius:10px;font-size:12px;border:1px solid var(--line)}} .tier.high{{border-color:#c62828}} .tier.medium{{border-color:#b26a00}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:12px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px}} .head{{display:flex;justify-content:space-between;gap:8px}}
.badge{{color:#fff;font-weight:600;font-size:12px;padding:3px 10px;border-radius:12px;height:fit-content}}
.row{{display:flex;gap:12px;align-items:center;margin:8px 0;flex-wrap:wrap}} .mini{{width:auto}} .mini td{{padding:2px 10px 2px 0;border:0;font-size:12.5px}}
.why{{margin:6px 0 0;padding-left:18px;font-size:13px}} svg .line{{fill:none;stroke:var(--accent);stroke-width:2}} svg .dot{{fill:var(--accent)}}
svg .bar{{stroke:var(--muted);stroke-dasharray:3 3}} .wrap{{overflow-x:auto}} footer{{color:var(--muted);font-size:12px;margin-top:28px}}
</style></head><body><main>
<h1>GenAI Adoption Control Tower</h1><div class="sub">Week 10 portfolio review · policy {e(policy['version'])}</div>
<div class="label">{e(LABEL)}</div>
<div class="tiles">{tile_html}</div>
<h2>Decisions this review</h2><div class="cards">{''.join(cards)}</div>
<h2>Prioritised portfolio</h2><div class="wrap"><table><tr><th>#</th><th>ID</th><th>Use case</th><th class="num">Score</th><th>Risk tier</th><th>Sourcing</th><th>Stage</th></tr>{port}</table></div>
<h2>Stage gates by risk tier</h2><div class="wrap"><table><tr><th>Tier</th><th>Min eval pass</th><th>Max override</th><th>Min adoption</th><th>Human review</th></tr>{gate_rows}</table></div>
<footer>Generated {_now()} · inputs SHA-256 {fingerprint[:16]}… · dashed line on each trend = the adoption bar for its risk tier.</footer>
</main></body></html>"""


def memo(decisions: list[dict], policy: dict, fingerprint: str) -> str:
    from .gates import ACTIONS
    s = summary(decisions, policy)
    L = ["# Decision memo – GenAI portfolio, week 10 review", "",
         f"*{LABEL}*", "",
         f"**Recommendation:** expand {s['decisions']['EXPAND']}, fix {s['decisions']['FIX']}, pause {s['decisions']['PAUSE']}. "
         f"{s['live']} live use cases, {s['weekly_active_users']} weekly active users, {s['hours_saved']:,.0f} hours saved over 10 weeks "
         f"for ${s['run_cost_usd']:,.0f} model run cost; {s['critical_incidents']} critical control incident.", ""]
    for k in ("PAUSE", "FIX", "EXPAND", "CONTINUE"):
        ds = [d for d in decisions if d["decision"] == k]
        if not ds:
            continue
        L += [f"## {k.title()}", ""]
        for d in ds:
            v = value(d["series"], policy)
            L.append(f"**{d['use_case']} {d['name']}** ({d['stage'].replace('_', ' ')}, {d['tier']} risk; "
                     f"{v['hours_saved']:,.0f} hours saved, ${v['run_cost_usd']:,.0f} run cost)")
            L += [f"- {r}" for r in d["reasons"]]
            L += [f"- Action: {a}" for a in ACTIONS[k if k != "FIX" else f"FIX_{d['fix_type']}"]]
            L.append("")
    L += ["## Decisions needed from leadership", "",
          "1. Approve the expansions above, including support and run-cost budget for the larger user groups.",
          "2. Confirm the paused use case stays paused until Compliance signs off the root cause and the new control test.",
          "3. Accept the named owners and dates for each fix, reviewed at the next portfolio meeting.", "",
          f"Inputs fingerprint: `{fingerprint[:16]}…` · policy {policy['version']} · generated {_now()}", ""]
    return "\n".join(L)


def decision_log(decisions: list[dict], policy: dict, fingerprint: str) -> str:
    out = [{"use_case": d["use_case"], "decision": d["decision"], "stage": d["stage"], "next_stage": d["next_stage"],
            "tier": d["tier"], "reasons": d["reasons"], "last_week": d["series"][-1]["week"]} for d in decisions]
    return json.dumps({"generated": _now(), "policy": policy["version"], "inputs_sha256": fingerprint, "decisions": out}, indent=2)
