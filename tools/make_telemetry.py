"""Generate the synthetic weekly telemetry in data/telemetry.csv.

Deterministic (no randomness): each pilot follows a written trajectory with conditions planted on purpose,
so every decision in the dashboard can be checked by hand. Run: python tools/make_telemetry.py
"""
import csv
from datetime import date, timedelta
from pathlib import Path

START = date(2026, 8, 3)          # Monday of week 1 (synthetic programme)
WEEKS = 10

def lerp(a, b, w, n=WEEKS):
    return a + (b - a) * (w - 1) / (n - 1)

def rows():
    out = []
    for w in range(1, WEEKS + 1):
        wk = (START + timedelta(weeks=w - 1)).isoformat()
        # UC04 policy Q&A (low risk): strong, steady growth -> EXPAND
        e = 300; a = round(lerp(0.10, 0.62, w), 3); wau = round(e * a); tasks = wau * 6
        out.append(dict(week=w, week_start=wk, use_case="UC04", eligible_users=e, weekly_active_users=wau, tasks=tasks,
                        tasks_accepted=round(tasks * 0.94), avg_minutes_saved=6.0, override_rate=0.06,
                        eval_pass_rate=0.97 if w < 5 else 0.98, cost_usd=round(tasks * 0.004, 2), incidents_critical=0, incidents_minor=1 if w == 3 else 0))
        # UC02 trade-break triage (high risk): adoption plateaus at ~0.55, quality below the high-tier bar -> FIX (quality)
        e = 40; a = round(min(lerp(0.15, 0.75, w), 0.55), 3); wau = round(e * a); tasks = wau * 14
        out.append(dict(week=w, week_start=wk, use_case="UC02", eligible_users=e, weekly_active_users=wau, tasks=tasks,
                        tasks_accepted=round(tasks * 0.80), avg_minutes_saved=11.0, override_rate=0.20 if w < 7 else 0.18,
                        eval_pass_rate=0.95 if w < 7 else 0.96, cost_usd=round(tasks * 0.0018, 2), incidents_critical=0, incidents_minor=1 if w in (4, 8) else 0))
        # UC03 surveillance triage (high risk): good numbers, but a critical control incident in week 8 -> PAUSE
        e = 15; a = round(lerp(0.20, 0.67, w), 3); wau = round(e * a); tasks = wau * 30
        out.append(dict(week=w, week_start=wk, use_case="UC03", eligible_users=e, weekly_active_users=wau, tasks=tasks,
                        tasks_accepted=round(tasks * 0.91), avg_minutes_saved=4.0, override_rate=0.08,
                        eval_pass_rate=0.985, cost_usd=round(tasks * 0.006, 2), incidents_critical=1 if w == 8 else 0, incidents_minor=0))
        # UC01 research summaries (medium risk, limited production): quality fine, adoption stuck near 0.22 -> FIX (adoption)
        e = 60; a = round(min(lerp(0.12, 0.40, w), 0.22), 3); wau = round(e * a); tasks = wau * 5
        out.append(dict(week=w, week_start=wk, use_case="UC01", eligible_users=e, weekly_active_users=wau, tasks=tasks,
                        tasks_accepted=round(tasks * 0.90), avg_minutes_saved=25.0, override_rate=0.09,
                        eval_pass_rate=0.96, cost_usd=round(tasks * 0.03, 2), incidents_critical=0, incidents_minor=0))
        # UC05 DDQ drafting (medium risk, limited production): meets scale gates for the last 4 weeks -> EXPAND
        e = 25; a = round(lerp(0.40, 0.72, w), 3); wau = round(e * a); tasks = wau * 8
        out.append(dict(week=w, week_start=wk, use_case="UC05", eligible_users=e, weekly_active_users=wau, tasks=tasks,
                        tasks_accepted=round(tasks * 0.88), avg_minutes_saved=35.0, override_rate=0.08,
                        eval_pass_rate=0.97, cost_usd=round(tasks * 0.05, 2), incidents_critical=0, incidents_minor=0))
    return out

if __name__ == "__main__":
    p = Path(__file__).resolve().parents[1] / "data" / "telemetry.csv"
    rs = rows()
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rs[0]))
        w.writeheader(); w.writerows(rs)
    print(f"wrote {len(rs)} rows to {p}")
