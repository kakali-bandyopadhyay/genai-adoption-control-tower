"""Workflow trace: steps agree with the gate decisions and the follow-up, and the build writes one trace per live use case."""
from pathlib import Path

from tower import trace
from tower.__main__ import build, context


def _steps(uc):
    ctx = context()
    return ctx, {s["title"].split(" (")[0]: s for s in trace.trace(ctx, uc)}


def test_trade_break_trace_shows_quality_fix_and_offline_gap():
    ctx, s = _steps("UC02")
    assert s["Risk tier and controls"]["outcome"] == "high risk"
    assert s["Offline evaluation"]["outcome"] == "54/54 passed"
    gate = s["Stage gate"]
    assert gate["outcome"] == "FIX (quality)"
    assert any(x.startswith("2. quality") and "NO" in x for x in gate["detail"])
    assert not any(x.startswith("3. adoption") for x in gate["detail"])          # first failing check decides
    assert any("IV05" in x for x in s["Actions and owned interventions"]["detail"])


def test_surveillance_trace_pauses_on_incident_before_quality():
    ctx, s = _steps("UC03")
    gate = s["Stage gate"]
    assert gate["outcome"] == "PAUSE"
    assert gate["detail"][0] == "1. critical control incident in window? YES, week 8"
    assert not any(x.startswith("2. quality") for x in gate["detail"])
    assert any("gap: a high-risk use case" in x for x in s["Offline evaluation"]["detail"])
    assert "MISSED" in " ".join(s["Decision register and escalation"]["detail"])
    assert any("S2" in x for x in s["What would change the decision"]["detail"])


def test_trace_matches_gate_decision_for_every_live_use_case():
    ctx = context()
    for d in ctx["decisions"]:
        gate = next(x for x in trace.trace(ctx, d["use_case"]) if x["title"].startswith("Stage gate"))
        assert gate["outcome"] == d["decision"] + (f" ({d['fix_type']})" if d.get("fix_type") else "")


def test_escalation_shown_only_where_follow_up_escalates():
    ctx = context()
    esc = {f["use_case"] for f in ctx["followup"] if f.get("escalate")}
    for d in ctx["decisions"]:
        reg = next(x for x in trace.trace(ctx, d["use_case"]) if x["title"].startswith("Decision register"))
        assert (reg["outcome"] == "ESCALATED to sponsor") == (d["use_case"] in esc)


def test_backlog_use_case_stops_before_the_gate():
    ctx = context()
    steps = trace.trace(ctx, "UC06")
    assert steps[-1]["outcome"] == "not live" and not any(x["title"].startswith("Stage gate") for x in steps)


def test_build_writes_traces_and_dashboard_section(tmp_path: Path):
    ctx = build(tmp_path)
    for d in ctx["decisions"]:
        assert (tmp_path / f"trace_{d['use_case']}.md").exists()
    html = (tmp_path / "dashboard.html").read_text(encoding="utf-8")
    assert 'id="trace"' in html and html.count("<details class='trace' open>") == 2


def test_gate_inputs_carry_metric_provenance_and_policy_status():
    ctx, s = _steps("UC02")
    live = " ".join(s["Live use, weekly gate inputs"]["detail"])
    for name in ("Adoption", "Evaluation pass rate", "Override rate", "Critical control incidents"):
        assert f"metric {name} =" in live
    assert "22 active / 40 eligible" in live and "provenance synthetic" in live
    assert any("not validated requirements" in x for x in s["Risk tier and controls"]["detail"])
    assert any("inputs SHA-256" in x for x in s["Stage gate"]["detail"])


def test_escalation_condition_is_stated():
    _, s = _steps("UC01")
    assert "condition met: ESCALATED to the sponsor" in s["Decision register and escalation"]["detail"][-1]
    _, s = _steps("UC02")
    assert "one more miss at the next review escalates" in s["Decision register and escalation"]["detail"][-1]


def test_input_fingerprint_ignores_line_endings(tmp_path: Path):
    from tower import data
    for f in data.DATA.iterdir():
        if f.is_file():
            b = f.read_bytes().replace(b"\r\n", b"\n")
            (tmp_path / f.name).write_bytes(b.replace(b"\n", b"\r\n") if f.suffix == ".csv" else b)
    assert data.fingerprint_all(tmp_path) == data.fingerprint_all()
