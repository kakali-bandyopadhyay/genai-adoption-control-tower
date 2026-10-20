"""CLI: python -m tower [portfolio|gates|build] [--out out]"""
from __future__ import annotations

import argparse
from pathlib import Path

from . import data, gates, portfolio, report
from .value import value


def run(out: Path) -> dict:
    pol, ucs, rows = data.load_policy(), data.load_use_cases(), data.load_telemetry()
    fp = data.fingerprint()
    pr = portfolio.prioritise(ucs, pol)
    ds = gates.decide_all(pr, rows, pol)
    out.mkdir(parents=True, exist_ok=True)
    (out / "dashboard.html").write_text(report.dashboard(pr, ds, pol, fp), encoding="utf-8")
    (out / "decision_memo.md").write_text(report.memo(ds, pol, fp), encoding="utf-8")
    (out / "decision_log.json").write_text(report.decision_log(ds, pol, fp), encoding="utf-8")
    return {"portfolio": pr, "decisions": ds, "policy": pol, "fingerprint": fp}


def main() -> None:
    p = argparse.ArgumentParser(prog="python -m tower")
    p.add_argument("cmd", choices=["portfolio", "gates", "build"])
    p.add_argument("--out", default="out")
    a = p.parse_args()
    res = run(Path(a.out))
    if a.cmd == "portfolio":
        for u in res["portfolio"]:
            print(f"{u['rank']:>2} {u['id']} {u['score']:.2f} {u['tier']:<6} {u['sourcing']:<6} {u['stage']:<18} {u['name']}")
    elif a.cmd == "gates":
        for d in res["decisions"]:
            v = value(d["series"], res["policy"])
            print(f"{d['use_case']} {d['decision']:<8} {d['stage']:<18} -> {d['next_stage']:<18} hours {v['hours_saved']:>7,.0f}  {d['name']}")
            for r in d["reasons"]:
                print(f"      - {r}")
    else:
        print(f"Wrote {a.out}/dashboard.html, decision_memo.md, decision_log.json (inputs {res['fingerprint'][:16]}…)")


if __name__ == "__main__":
    main()
