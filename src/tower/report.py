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


def _pct(x):
    return "–" if x is None else f"{x:.0%}"


def dashboard(ctx: dict) -> str:
    e = html.escape
    prioritised, decisions, policy, fp = ctx["portfolio"], ctx["decisions"], ctx["policy"], ctx["fingerprint"]
    s = summary(decisions, policy)
    tc = ctx["tco"]
    tiles = [("Live use cases", s["live"]), ("Weekly active users", s["weekly_active_users"]),
             ("Hours saved (10 wks)", f"{s['hours_saved']:,.0f}"),
             ("Total cost of ownership (10 wks)", f"${sum(t['total_cost_usd'] for t in tc.values()):,.0f}"),
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
        label = d["decision"] + (f" · {d['fix_type']}" if d.get("fix_type") else "")
        cards.append(
            f'<section class="card"><div class="head"><div><b>{d["use_case"]} · {e(d["name"])}</b>'
            f'<div class="sub">{e(d["stage"].replace("_", " "))} · {d["tier"]} risk</div></div>'
            f'<span class="badge" style="background:{COLOURS[d["decision"]]}">{e(label)}</span></div>'
            f'<div class="row">{_spark([r["adoption"] for r in d["series"]], bar=d["gate"]["min_adoption"])}'
            f'<table class="mini"><tr><td>Adoption</td><td>{last["adoption"]:.0%}</td></tr>'
            f'<tr><td>Eval pass</td><td>{last["eval_pass_rate"]:.1%}</td></tr>'
            f'<tr><td>Override</td><td>{last["override_rate"]:.0%}</td></tr>'
            f'<tr><td>Hours saved</td><td>{v["hours_saved"]:,.0f}</td></tr>'
            f'<tr><td>Cost / task</td><td>${v["cost_per_task_usd"]:.4f}</td></tr></table></div>'
            f'<ul class="why">{reasons}</ul></section>')
    fu = "".join(
        f"<tr><td class='num'>{x['review']}</td><td>{x['use_case']}</td><td>{x['decision']}</td><td>{e(x['rationale'])}</td><td>{e(x['owner'])}</td>"
        f"<td>{x['expect']['metric']} {x['expect']['op']} {x['expect']['target']} by {x['review_by']}</td>"
        f"<td>{'' if x['actual'] is None else (x['actual'] if x['expect']['metric'] == 'critical_incidents' else _pct(x['actual']))}</td>"
        f"<td><b class='st {x['status'].lower()}'>{x['status']}</b>{' · <b class=st-esc>ESCALATE</b>' if x.get('escalate') else ''}</td></tr>"
        for x in ctx["followup"])
    sc = ctx["scenarios"]
    uc_cols = list(sc["baseline"])
    sc_head = "".join(f"<th>{k}</th>" for k in uc_cols)
    base_cells = "".join("<td>" + sc["baseline"][k] + "</td>" for k in uc_cols)
    base_net = sc["scenarios"][0]["base_net_usd"]
    sc_rows = f"<tr><td><b>Baseline</b></td>{base_cells}<td class='num'>${base_net:,.0f}</td><td></td></tr>"
    for x in sc["scenarios"]:
        cells = "".join("<td class='" + ("chg" if k in x["changed"] else "") + "'>" + x["decisions"][k] + "</td>" for k in uc_cols)
        drivers = "; ".join(f"{k}: {e(v)}" for k, v in x["drivers"].items()) or "no decision changes"
        sc_rows += (f"<tr><td><b>{x['id']}</b> {e(x['name'])}<div class='sub'>{e(x['question'])}</div></td>{cells}"
                    f"<td class='num'>{'unchanged' if x['net_usd'] == x['base_net_usd'] else '$' + format(x['net_usd'], ',.0f')}</td><td class='sub'>{drivers}</td></tr>")
    coh = "".join(
        f"<tr><td>{c['use_case']}</td><td>{e(c['cohort'])}</td><td class='num'>{c['active_users']}/{c['eligible_users']}</td>"
        f"<td class='num {'low' if c['below_bar'] else ''}'>{c['adoption']:.0%}</td><td class='num'>{_pct(c['bar'])}</td></tr>"
        for c in ctx["cohorts"])
    ivs = "".join(
        f"<tr><td>{x['id']}</td><td>{x['use_case']}</td><td>{e(x['cohort'])}</td><td>{e(x['type'])}</td><td>{e(x['action'])}</td>"
        f"<td>{e(x['owner'])}</td><td>{x['due']}</td><td>{x['measure']} → {x['target'] if x['measure'] == 'critical_incidents' else _pct(x['target'])}</td><td>{e(x['status'])}</td></tr>"
        for x in ctx["interventions"])
    lines = list(next(iter(tc.values()))["cost_lines"])
    def _cost_cells(t):
        return "".join("<td class='num'>$" + format(t["cost_lines"][l], ",.0f") + "</td>" for l in lines)
    tco_rows = "".join(
        f"<tr><td>{k}</td><td>{t['sourcing']}</td>{_cost_cells(t)}"
        f"<td class='num'><b>${t['total_cost_usd']:,.0f}</b></td><td class='num'>{t['hours_low']:,.0f}–{t['hours_high']:,.0f}</td>"
        f"<td class='num'>${t['net_low_usd']:,.0f} to ${t['net_high_usd']:,.0f}</td><td class='num'>${t['net_excl_one_off_usd']:,.0f}</td></tr>"
        for k, t in tc.items())
    tco_head = "".join(f"<th class='num'>{e(l)}</th>" for l in lines)
    reg = "".join(
        f"<tr><td><b>{e(m['name'])}</b></td><td>{e(m['definition'])}</td><td>{e(m['numerator'])} / {e(m['denominator'])}</td>"
        f"<td>{e(m['window'])}</td><td>{e(m['source'])}</td><td>{e(m['owner'])}</td><td><span class='prov'>{e(m['provenance'])}</span></td></tr>"
        for m in ctx["metrics"])
    gate_rows = "".join(f"<tr><td>{t}</td><td>{g['min_eval_pass']:.0%}</td><td>{g['max_override']:.0%}</td><td>{g['min_adoption']:.0%}</td>"
                        f"<td>{'yes' if g.get('human_review_required') else 'per use case'}</td></tr>" for t, g in policy["gates"].items())
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>GenAI Adoption Control Tower</title><style>
:root{{--bg:#ffffff;--fg:#1d2330;--muted:#5b6475;--line:#dde2ea;--card:#f7f9fc;--accent:#2f6fde;--warn:#b26a00;--bad:#c62828;--good:#2e7d32}}
@media (prefers-color-scheme:dark){{:root{{--bg:#12151b;--fg:#e7eaf0;--muted:#a3abba;--line:#2b313c;--card:#1a1e26;--accent:#7aa7ff;--warn:#e0a040;--bad:#ef6b6b;--good:#66bb6a}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}}
main{{max-width:1180px;margin:0 auto;padding:24px 16px}} h1{{font-size:22px;margin:0 0 4px}} h2{{font-size:16px;margin:30px 0 4px}} .lead{{color:var(--muted);margin:0 0 10px}}
.label{{color:var(--muted);font-size:12.5px;border-left:3px solid var(--accent);padding:6px 10px;background:var(--card);margin:10px 0 18px}}
nav{{display:flex;gap:14px;flex-wrap:wrap;font-size:13px;margin:6px 0 14px}} nav a{{color:var(--accent);text-decoration:none}}
.tiles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}}
.tile{{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px}} .k{{font-size:22px;font-weight:600}} .l{{color:var(--muted);font-size:12px}}
table{{border-collapse:collapse;width:100%}} th,td{{text-align:left;padding:7px 8px;border-bottom:1px solid var(--line);vertical-align:top}}
th{{font-size:12px;color:var(--muted);font-weight:600}} .num{{text-align:right;white-space:nowrap}} .sub{{color:var(--muted);font-size:12px}}
.tier{{padding:1px 8px;border-radius:10px;font-size:12px;border:1px solid var(--line)}} .tier.high{{border-color:var(--bad)}} .tier.medium{{border-color:var(--warn)}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:12px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px}} .head{{display:flex;justify-content:space-between;gap:8px}}
.badge{{color:#fff;font-weight:600;font-size:12px;padding:3px 10px;border-radius:12px;height:fit-content;white-space:nowrap}}
.row{{display:flex;gap:12px;align-items:center;margin:8px 0;flex-wrap:wrap}} .mini{{width:auto}} .mini td{{padding:2px 10px 2px 0;border:0;font-size:12.5px}}
.why{{margin:6px 0 0;padding-left:18px;font-size:13px}} svg .line{{fill:none;stroke:var(--accent);stroke-width:2}} svg .dot{{fill:var(--accent)}}
svg .bar{{stroke:var(--muted);stroke-dasharray:3 3}} .wrap{{overflow-x:auto}} footer{{color:var(--muted);font-size:12px;margin-top:28px}}
.st.met{{color:var(--good)}} .st.missed{{color:var(--bad)}} .st.open{{color:var(--muted)}} .st-esc{{color:var(--bad)}} td.chg{{font-weight:700;color:var(--accent)}} td.low{{color:var(--bad);font-weight:600}}
.prov{{font-size:12px;color:var(--muted)}}
</style></head><body><main>
<h1>GenAI Adoption Control Tower</h1><div class="sub">Week 10 portfolio review · policy {e(policy['version'])}</div>
<div class="label">{e(LABEL)}</div>
<nav><a href="#decisions">Decisions</a><a href="#followup">Follow-up</a><a href="#adoption">Adoption plan</a><a href="#scenarios">What if</a><a href="#value">Value</a><a href="#portfolio">Portfolio</a><a href="#metrics">Metric register</a></nav>
<div class="tiles">{tile_html}</div>
<h2 id="decisions">Decisions this review</h2><p class="lead">Checks run in order: control incidents, then quality, then adoption, then sustained performance.</p><div class="cards">{''.join(cards)}</div>
<h2 id="followup">Follow-up on earlier decisions</h2><p class="lead">What each recorded decision expected, and what happened. Two consecutive misses escalate to the sponsor.</p>
<div class="wrap"><table><tr><th>Review</th><th>ID</th><th>Decision</th><th>Rationale</th><th>Owner</th><th>Expected</th><th>Actual</th><th>Status</th></tr>{fu}</table></div>
<h2 id="adoption">Adoption by cohort and the plan to close gaps</h2><p class="lead">Cohorts below their tier's adoption bar are marked; every intervention has an owner, a due date and a success measure.</p>
<div class="wrap"><table><tr><th>ID</th><th>Cohort</th><th class="num">Active / eligible</th><th class="num">Adoption</th><th class="num">Bar</th></tr>{coh}</table></div>
<div class="wrap" style="margin-top:12px"><table><tr><th>#</th><th>Use case</th><th>Cohort</th><th>Type</th><th>Action</th><th>Owner</th><th>Due</th><th>Success measure</th><th>Status</th></tr>{ivs}</table></div>
<h2 id="scenarios">What if?</h2><p class="lead">Each scenario changes named inputs and re-runs the same gates. Changed decisions are highlighted; net value is the illustrative portfolio total.</p>
<div class="wrap"><table><tr><th>Scenario</th>{sc_head}<th class="num">Net value</th><th>What drove the change</th></tr>{sc_rows}</table></div>
<h2 id="value">Value case (assumed costs, illustrative)</h2><p class="lead">Total cost of ownership over 10 weeks. Hours shown as a ±{policy['costs']['minutes_saved_sensitivity']:.0%} range on minutes saved per task. One-off build and change costs are why builds take longer to pay back.</p>
<div class="wrap"><table><tr><th>ID</th><th>Sourcing</th>{tco_head}<th class="num">Total</th><th class="num">Hours saved (range)</th><th class="num">Net value (range)</th><th class="num">Net excl. one-off</th></tr>{tco_rows}</table></div>
<h2 id="portfolio">Prioritised portfolio</h2><div class="wrap"><table><tr><th>#</th><th>ID</th><th>Use case</th><th class="num">Score</th><th>Risk tier</th><th>Sourcing</th><th>Stage</th></tr>{port}</table></div>
<h2>Stage gates by risk tier</h2><div class="wrap"><table><tr><th>Tier</th><th>Min eval pass</th><th>Max override</th><th>Min adoption</th><th>Human review</th></tr>{gate_rows}</table></div>
<h2 id="metrics">Metric and assumption register</h2><p class="lead">How every number on this page is defined, where it comes from, who owns it, and whether it is synthetic, assumed or measured.</p>
<div class="wrap"><table><tr><th>Metric</th><th>Definition</th><th>Numerator / denominator</th><th>Window</th><th>Source</th><th>Owner</th><th>Provenance</th></tr>{reg}</table></div>
<footer>Generated {_now()} · inputs SHA-256 {fp[:16]}… · dashed line on each trend = the adoption bar for its risk tier.</footer>
</main></body></html>"""


def _target(x: dict) -> str:
    if x["measure"] == "critical_incidents":
        return "critical incidents = 0"
    op = "<=" if x["measure"] == "override_rate" else ">="
    return f"{x['measure']} {op} {x['target']:.0%}"


def memo(ctx: dict) -> str:
    from .gates import ACTIONS
    decisions, policy, fingerprint = ctx["decisions"], ctx["policy"], ctx["fingerprint"]
    s = summary(decisions, policy)
    tc = ctx["tco"]
    tot = sum(t["total_cost_usd"] for t in tc.values())
    L = ["# Decision memo – GenAI portfolio, week 10 review", "",
         f"*{LABEL}*", "",
         f"**Recommendation:** expand {s['decisions']['EXPAND']}, fix {s['decisions']['FIX']}, pause {s['decisions']['PAUSE']}. "
         f"{s['live']} live use cases, {s['weekly_active_users']} weekly active users, {s['hours_saved']:,.0f} hours saved over 10 weeks; "
         f"assumed total cost of ownership ${tot:,.0f} (model run cost ${s['run_cost_usd']:,.0f}); "
         f"{s['critical_incidents']} critical control incident.", ""]
    esc = [x for x in ctx["followup"] if x.get("escalate")]
    if esc:
        L += ["## Escalation", ""]
        L += [f"- **{x['use_case']}** missed its expected outcome at two consecutive reviews "
              f"(latest: {x['expect']['metric']} {x['expect']['op']} {x['expect']['target']}, actual "
              f"{x['actual']:.0%}). Owner {x['owner']}; sponsor to confirm the recovery plan or stop the use case." for x in esc]
        L.append("")
    for k in ("PAUSE", "FIX", "EXPAND", "CONTINUE"):
        ds = [d for d in decisions if d["decision"] == k]
        if not ds:
            continue
        L += [f"## {k.title()}", ""]
        for d in ds:
            t = tc[d["use_case"]]
            L.append(f"**{d['use_case']} {d['name']}** ({d['stage'].replace('_', ' ')}, {d['tier']} risk; "
                     f"{t['hours_low']:,.0f}–{t['hours_high']:,.0f} hours saved; assumed total cost ${t['total_cost_usd']:,.0f})")
            L += [f"- {r}" for r in d["reasons"]]
            L += [f"- Action: {a}" for a in ACTIONS[k if k != "FIX" else f"FIX_{d['fix_type']}"]]
            ivs = [x for x in ctx["interventions"] if x["use_case"] == d["use_case"]]
            L += [f"- Intervention {x['id']} ({x['type']}, {x['cohort']}): {x['action']} – owner {x['owner']}, due {x['due']}, "
                  f"success = {_target(x)}"
                  for x in ivs]
            L.append("")
    L += ["## What would change these decisions", ""]
    for x in ctx["scenarios"]["scenarios"]:
        ch = ", ".join(f"{k} {a} → {b}" for k, (a, b) in x["changed"].items()) or "no decision changes"
        val = "value unchanged" if x["net_usd"] == x["base_net_usd"] else f"illustrative portfolio net value ${x['net_usd']:,.0f} (baseline ${x['base_net_usd']:,.0f})"
        L.append(f"- **{x['id']} {x['name']}:** {ch}; {val}.")
    L += ["", "## Decisions needed from leadership", "",
          "1. Approve the expansions above, including support and run-cost budget for the larger user groups.",
          "2. Confirm the paused use case stays paused until Compliance signs off the root cause and the new control test.",
          "3. Accept the named owners, dates and success measures for each fix and intervention.",
          "4. Record each decision with an expected outcome and review date (`python -m tower record`), so the next review can check it.", "",
          f"Inputs fingerprint: `{fingerprint[:16]}…` · policy {policy['version']} · generated {_now()}", ""]
    return "\n".join(L)


def decision_log(decisions: list[dict], policy: dict, fingerprint: str) -> str:
    out = [{"use_case": d["use_case"], "decision": d["decision"], "stage": d["stage"], "next_stage": d["next_stage"],
            "tier": d["tier"], "reasons": d["reasons"], "last_week": d["series"][-1]["week"]} for d in decisions]
    return json.dumps({"generated": _now(), "policy": policy["version"], "inputs_sha256": fingerprint, "decisions": out}, indent=2)
