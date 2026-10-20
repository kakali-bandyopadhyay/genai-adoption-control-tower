import json
import shutil

import pytest

from tower import data, followup, scenarios
from tower.__main__ import build, context


@pytest.fixture(scope="module")
def ctx():
    return context()


# ---------- 1. metric and assumption register
def test_every_metric_the_gates_and_value_use_is_registered(ctx):
    reg = {m["id"]: m for m in ctx["metrics"]}
    for k in ("adoption", "eval_pass_rate", "override_rate", "critical_incidents", "hours_saved", "model_run_cost", "total_cost", "net_value"):
        assert k in reg
        for f in ("definition", "numerator", "denominator", "window", "source", "owner", "provenance"):
            assert reg[k][f]
    assert "measured on a personal prototype" in reg["eval_pass_rate"]["provenance"]   # the one real input is marked
    assert reg["total_cost"]["provenance"] == "assumed"


def _copy_data(tmp_path):
    d = tmp_path / "d"
    shutil.copytree(data.DATA, d)
    return d


def test_unregistered_measure_is_rejected(tmp_path):
    d = _copy_data(tmp_path)
    iv = json.loads((d / "interventions.json").read_text())
    iv[0]["measure"] = "happiness"
    (d / "interventions.json").write_text(json.dumps(iv))
    with pytest.raises(ValueError, match="not in the metric register"):
        data.load_all(d)


def test_cohorts_must_add_up_to_telemetry(tmp_path):
    d = _copy_data(tmp_path)
    c = json.loads((d / "cohorts.json").read_text())
    c[0]["active_users"] += 1
    (d / "cohorts.json").write_text(json.dumps(c))
    with pytest.raises(ValueError, match="do not add up"):
        data.load_all(d)


# ---------- 2. what-if scenarios
def test_scenarios_show_what_drives_each_decision(ctx):
    sc = {x["id"]: x for x in ctx["scenarios"]["scenarios"]}
    assert sc["S1"]["changed"] == {"UC02": ("FIX (quality)", "EXPAND")}
    assert sc["S2"]["changed"] == {"UC03": ("PAUSE", "EXPAND")}           # the incident is the only blocker
    assert sc["S3"]["changed"] == {"UC01": ("FIX (adoption)", "EXPAND")}  # lowering the bar would expand an unused tool
    assert sc["S4"]["changed"] == {"UC01": ("FIX (adoption)", "FIX (quality)")}
    assert sc["S5"]["changed"] == {} and sc["S5"]["net_usd"] < 0 < sc["S5"]["base_net_usd"]
    assert sc["S6"]["changed"] == {} and sc["S6"]["net_usd"] < sc["S6"]["base_net_usd"]


def test_scenarios_never_modify_the_inputs():
    inp = data.load_all()
    before = json.dumps([inp["policy"], inp["telemetry"]], sort_keys=True, default=str)
    scenarios.run(inp)
    assert json.dumps([inp["policy"], inp["telemetry"]], sort_keys=True, default=str) == before


def test_a_scenario_that_matches_nothing_fails_loudly():
    inp = data.load_all()
    inp["scenarios"] = [{"id": "X", "name": "x", "question": "x", "changes": [
        {"target": "telemetry", "use_case": "UC99", "from_week": 1, "field": "cost_usd", "op": "scale", "value": 2}]}]
    with pytest.raises(ValueError, match="matched no telemetry rows"):
        scenarios.run(inp)


# ---------- 3. fuller value case
def test_total_cost_adds_up_and_builds_carry_one_off_cost(ctx):
    for t in ctx["tco"].values():
        assert abs(sum(t["cost_lines"].values()) - t["total_cost_usd"]) < 0.01
        assert t["net_low_usd"] < t["net_usd"] < t["net_high_usd"]
    assert ctx["tco"]["UC03"]["cost_lines"]["build (one-off)"] == 320 * 90
    assert ctx["tco"]["UC04"]["cost_lines"]["build (one-off)"] == 0
    assert ctx["tco"]["UC02"]["net_usd"] < 0 < ctx["tco"]["UC02"]["net_excl_one_off_usd"]   # payback beyond 10 weeks


# ---------- 4. adoption cohorts and interventions
def test_cohorts_below_bar_are_flagged_and_have_interventions(ctx):
    low = {(c["use_case"], c["cohort"]) for c in ctx["cohorts"] if c["below_bar"]}
    assert ("UC01", "Credit research") in low and ("UC01", "Equity research") in low and ("UC02", "Reconciliations") in low
    covered = {(x["use_case"], x["cohort"]) for x in ctx["interventions"]}
    assert ("UC01", "Credit research") in covered and ("UC02", "Reconciliations") in covered
    assert all(x["owner"] and x["due"] and x["measure"] for x in ctx["interventions"])


# ---------- 5. decision capture and follow-up
def test_follow_up_checks_expectations_and_escalates_repeat_misses(ctx):
    f = {(x["review"], x["use_case"]): x for x in ctx["followup"]}
    assert f[("week 2", "UC01")]["status"] == "MISSED" and not f[("week 2", "UC01")]["escalate"]
    assert f[("week 6", "UC01")]["status"] == "MISSED" and f[("week 6", "UC01")]["escalate"]
    assert f[("week 6", "UC03")]["status"] == "MISSED" and f[("week 6", "UC03")]["actual"] == 1
    assert f[("week 6", "UC04")]["status"] == "MET" and f[("week 6", "UC05")]["status"] == "MET"


def test_record_appends_and_validates(tmp_path):
    p = tmp_path / "reg.json"
    p.write_text((data.DATA / "decision_register.json").read_text())
    n = len(json.loads(p.read_text()))
    e = followup.record(p, {"review": "week 10", "use_case": "UC04", "decision": "EXPAND", "rationale": "gates met 4 weeks",
                            "owner": "Use-case product owner", "decided_by": "GenAI steering group", "review_by": "week 14",
                            "expect": {"metric": "adoption", "op": ">=", "target": 0.55}}, "abc")
    reg = json.loads(p.read_text())
    assert len(reg) == n + 1 and reg[-1]["provenance"] == "recorded" and reg[-1]["inputs_sha256"] == "abc"
    with pytest.raises(ValueError, match="needs rationale"):
        followup.record(p, {"review": "week 10", "use_case": "UC04", "decision": "EXPAND", "rationale": "", "owner": "x",
                            "decided_by": "y", "review_by": "week 14", "expect": {"metric": "adoption", "op": ">=", "target": 0.5}}, "abc")
    open_ = followup.check(reg, context()["decisions"], data.load_policy())
    assert next(x for x in open_ if x["review"] == "week 10")["status"] == "OPEN"   # due after the data we have


# ---------- outputs
def test_dashboard_and_memo_carry_every_new_section(tmp_path):
    build(tmp_path)
    html = (tmp_path / "dashboard.html").read_text()
    memo = (tmp_path / "decision_memo.md").read_text()
    for anchor in ('id="followup"', 'id="adoption"', 'id="scenarios"', 'id="value"', 'id="metrics"'):
        assert anchor in html
    assert "## Escalation" in memo and "UC01" in memo.split("## Escalation")[1].split("##")[0]
    assert "Intervention IV01" in memo and "## What would change these decisions" in memo
    assert "assumed total cost of ownership" in memo
