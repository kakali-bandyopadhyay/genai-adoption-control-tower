"""CLI: python -m tower <command>

  portfolio   ranked portfolio with risk tier and sourcing
  gates       this review's decisions and the reasons
  scenarios   what-if scenarios: which decisions change and why
  followup    earlier decisions: expected vs actual, escalations
  metrics     the metric and assumption register
  value       total cost of ownership and net value ranges (assumed costs)
  record      append a leadership decision to the decision register
  trace       one use case step by step: intake, risk tier, evaluation, gate checks, actions, adoption, value, escalation
  build       write out/dashboard.html, out/decision_memo.md, out/decision_log.json
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import adoption, data, engine, followup, report, scenarios, trace
from .value import tco


def context() -> dict:
    inp = data.load_all()
    fp = data.fingerprint_all()
    pr, ds = engine.evaluate(inp["policy"], inp["use_cases"], inp["telemetry"])
    by_id = {u["id"]: u for u in pr}
    return {"portfolio": pr, "decisions": ds, "policy": inp["policy"], "fingerprint": fp, "inputs": inp,
            "metrics": inp["metrics"],
            "tco": {d["use_case"]: tco(by_id[d["use_case"]], d["series"], inp["policy"]) for d in ds},
            "scenarios": scenarios.run(inp),
            "followup": followup.check(inp["register"], ds, inp["policy"]),
            "cohorts": adoption.cohorts(inp["cohorts"], ds),
            "interventions": adoption.plan(inp["interventions"], ds)}


def build(out: Path) -> dict:
    ctx = context()
    out.mkdir(parents=True, exist_ok=True)
    (out / "dashboard.html").write_text(report.dashboard(ctx), encoding="utf-8")
    (out / "decision_memo.md").write_text(report.memo(ctx), encoding="utf-8")
    (out / "decision_log.json").write_text(report.decision_log(ctx["decisions"], ctx["policy"], ctx["fingerprint"]), encoding="utf-8")
    for d in ctx["decisions"]:
        steps = trace.trace(ctx, d["use_case"])
        (out / f"trace_{d['use_case']}.md").write_text(trace.as_markdown(steps, d["use_case"], d["name"]), encoding="utf-8")
    return ctx


run = build   # backwards-compatible name used by B01 tests


def main() -> None:
    for stream in (sys.stdout, sys.stderr):            # Windows consoles default to a legacy code page
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    p = argparse.ArgumentParser(prog="python -m tower", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("cmd", choices=["portfolio", "gates", "scenarios", "followup", "metrics", "value", "record", "trace", "build"])
    p.add_argument("--out", default="out")
    p.add_argument("--use-case"); p.add_argument("--decision"); p.add_argument("--rationale"); p.add_argument("--owner")
    p.add_argument("--by", dest="decided_by"); p.add_argument("--review", default="week 10"); p.add_argument("--review-by")
    p.add_argument("--expect", help="metric op target, e.g. \"adoption >= 0.45\"")
    a = p.parse_args()
    if a.cmd == "record":
        m, op, t = a.expect.split()
        e = followup.record(data.DATA / "decision_register.json",
                            {"review": a.review, "use_case": a.use_case, "decision": a.decision, "rationale": a.rationale,
                             "owner": a.owner, "decided_by": a.decided_by, "review_by": a.review_by,
                             "expect": {"metric": m, "op": op, "target": float(t)}}, data.fingerprint_all())
        print(f"Recorded {e['use_case']} {e['decision']} ({e['review']}) – expect {a.expect} by {e['review_by']}")
        return
    ctx = build(Path(a.out)) if a.cmd == "build" else context()
    if a.cmd == "trace":
        ids = [a.use_case] if a.use_case else [d["use_case"] for d in ctx["decisions"]]
        print("\n\n".join(trace.as_text(trace.trace(ctx, i), i) for i in ids))
        return
    if a.cmd == "portfolio":
        for u in ctx["portfolio"]:
            print(f"{u['rank']:>2} {u['id']} {u['score']:.2f} {u['tier']:<6} {u['sourcing']:<6} {u['stage']:<18} {u['name']}")
    elif a.cmd == "gates":
        for d in ctx["decisions"]:
            t = ctx["tco"][d["use_case"]]
            kind = f" ({d['fix_type']})" if d.get("fix_type") else ""
            print(f"{d['use_case']} {d['decision'] + kind:<18} {d['stage']:<18} -> {d['next_stage']:<18} hours {t['hours_saved']:>7,.0f}  {d['name']}")
            for r in d["reasons"]:
                print(f"      - {r}")
    elif a.cmd == "scenarios":
        sc = ctx["scenarios"]
        print("baseline  " + "  ".join(f"{k}:{v}" for k, v in sc["baseline"].items()))
        for x in sc["scenarios"]:
            ch = ", ".join(f"{k} {b0}->{b1}" for k, (b0, b1) in x["changed"].items()) or "no decision changes"
            print(f"{x['id']} {x['name']}: {ch}; net ${x['net_usd']:,.0f} (baseline ${x['base_net_usd']:,.0f})")
    elif a.cmd == "followup":
        for x in ctx["followup"]:
            act = "" if x["actual"] is None else f" actual {x['actual']}"
            print(f"{x['review']:<8} {x['use_case']} {x['decision']:<8} expect {x['expect']['metric']} {x['expect']['op']} "
                  f"{x['expect']['target']} by {x['review_by']}:{act} -> {x['status']}{'  ESCALATE' if x.get('escalate') else ''}")
    elif a.cmd == "metrics":
        for m in ctx["metrics"]:
            print(f"{m['name']:<28} {m['numerator']} / {m['denominator']}  [{m['provenance']}]  owner: {m['owner']}")
    elif a.cmd == "value":
        for k, t in ctx["tco"].items():
            print(f"{k} {t['sourcing']:<6} total cost ${t['total_cost_usd']:>9,.0f}  hours {t['hours_low']:,.0f}-{t['hours_high']:,.0f}  "
                  f"net ${t['net_low_usd']:,.0f} to ${t['net_high_usd']:,.0f}  (excl. one-off ${t['net_excl_one_off_usd']:,.0f})")
    else:
        print(f"Wrote {a.out}/dashboard.html, decision_memo.md, decision_log.json, trace_<use case>.md (inputs {ctx['fingerprint'][:16]}…)")


if __name__ == "__main__":
    main()
