import json
from pathlib import Path
from tower import data, value
from tower.__main__ import run


def test_value_is_hours_first_and_reconciles(decisions, base):
    pol = base[0]
    s = decisions["UC05"]["series"]
    v = value.value(s, pol)
    assert v["hours_saved"] == round(sum(r["tasks_accepted"] * 35.0 for r in s) / 60, 1)
    assert v["value_usd_illustrative"] == round(v["hours_saved"] * 90)
    assert decisions["UC02"]["series"] and value.value(decisions["UC02"]["series"], pol)["cost_per_task_usd"] == 0.0018


def test_build_writes_three_outputs_tied_to_inputs(tmp_path):
    res = run(tmp_path)
    html = (tmp_path / "dashboard.html").read_text()
    memo = (tmp_path / "decision_memo.md").read_text()
    log = json.loads((tmp_path / "decision_log.json").read_text())
    assert "Synthetic data" in html and "Synthetic data" in memo
    assert log["inputs_sha256"] == data.fingerprint_all() == res["fingerprint"]
    assert [d["decision"] for d in log["decisions"]] == ["PAUSE", "FIX", "FIX", "EXPAND", "EXPAND"]
    assert "expand 2, fix 2, pause 1" in memo and "## Decisions needed from leadership" in memo
    assert "champion" in memo                                   # adoption fix has adoption actions
    assert "Error analysis by break type" in memo               # quality fix has quality actions


def test_outputs_are_deterministic_apart_from_timestamps(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    run(a); run(b)
    strip = lambda p: "\n".join(l for l in p.read_text().splitlines() if "Generated" not in l and "generated" not in l)
    assert strip(a / "decision_memo.md") == strip(b / "decision_memo.md")
