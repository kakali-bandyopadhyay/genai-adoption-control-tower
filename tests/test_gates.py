import copy
from tower import gates


def test_planted_decisions(decisions):
    assert {k: d["decision"] for k, d in decisions.items()} == {
        "UC01": "FIX", "UC02": "FIX", "UC03": "PAUSE", "UC04": "EXPAND", "UC05": "EXPAND"}
    assert decisions["UC01"]["fix_type"] == "adoption" and decisions["UC02"]["fix_type"] == "quality"
    assert decisions["UC04"]["next_stage"] == "limited_production" and decisions["UC05"]["next_stage"] == "scale"


def test_control_incident_outranks_good_numbers(decisions):
    d = decisions["UC03"]
    last = d["series"][-1]
    assert last["eval_pass_rate"] >= d["gate"]["min_eval_pass"] and last["adoption"] >= d["gate"]["min_adoption"]
    assert d["decision"] == "PAUSE" and "week 8" in d["reasons"][0]


def test_high_tier_always_keeps_human_review(decisions):
    for k in ("UC02", "UC03"):
        assert any("human review" in r for r in decisions[k]["reasons"])
    assert not any("human review" in r for r in decisions["UC04"]["reasons"])


def test_offline_baseline_gap_is_reported(decisions):
    assert any("54/54" in r and "96%" in r for r in decisions["UC02"]["reasons"])


def test_expand_needs_consecutive_weeks(base):
    pol, pr, rows = base
    rows = copy.deepcopy(rows)
    for r in rows:                       # break UC04 two weeks before the end: streak drops to 1
        if r["use_case"] == "UC04" and r["week"] == 9:
            r["override_rate"] = 0.30
    d = gates.decide(next(u for u in pr if u["id"] == "UC04"), rows, pol)
    assert d["decision"] == "CONTINUE" and "1 week(s)" in d["reasons"][0]


def test_incident_ages_out_of_the_window(base):
    pol, pr, rows = base
    rows = copy.deepcopy(rows)
    for r in rows:                       # move UC03's incident to week 2, outside the 4-week window
        if r["use_case"] == "UC03":
            r["incidents_critical"] = 1 if r["week"] == 2 else 0
    d = gates.decide(next(u for u in pr if u["id"] == "UC03"), rows, pol)
    assert d["decision"] != "PAUSE"


def test_backlog_items_get_no_decision(decisions):
    assert not {"UC06", "UC07", "UC08", "UC09"} & set(decisions)
