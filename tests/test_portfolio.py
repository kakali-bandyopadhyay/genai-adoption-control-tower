import json
import pytest
from tower import data, portfolio


def test_inputs_load_and_validate(base):
    pol, pr, rows = base
    assert len(pr) == 9 and len(rows) == 50
    assert {u["id"] for u in pr} == {f"UC0{i}" for i in range(1, 10)}


def test_bad_score_is_rejected(tmp_path):
    for f in ("policy.json", "telemetry.csv"):
        (tmp_path / f).write_bytes((data.DATA / f).read_bytes())
    ucs = json.loads((data.DATA / "use_cases.json").read_text())
    ucs[0]["value"] = 7
    (tmp_path / "use_cases.json").write_text(json.dumps(ucs))
    with pytest.raises(ValueError, match="UC01: value must be an integer 1-5"):
        data.load_use_cases(tmp_path)


def test_impossible_telemetry_is_rejected(tmp_path):
    for f in ("policy.json", "use_cases.json"):
        (tmp_path / f).write_bytes((data.DATA / f).read_bytes())
    lines = (data.DATA / "telemetry.csv").read_text().splitlines()
    cols = lines[1].split(",")
    cols[4] = str(int(cols[3]) + 1)             # more weekly users than eligible users
    lines[1] = ",".join(cols)
    (tmp_path / "telemetry.csv").write_text("\n".join(lines) + "\n")
    with pytest.raises(ValueError, match="impossible counts"):
        data.load_telemetry(tmp_path)


def test_score_is_the_documented_weighted_sum(base):
    pol, pr, _ = base
    u = next(x for x in pr if x["id"] == "UC02")
    assert u["score"] == round(0.40 * 5 + 0.25 * 4 + 0.20 * 4 + 0.15 * 4, 2) == 4.40
    assert [x["rank"] for x in pr] == list(range(1, 10))
    assert pr[0]["id"] == "UC02"


@pytest.mark.parametrize("sens,risk,tier", [(1, 2, "low"), (3, 2, "medium"), (2, 4, "high"), (5, 1, "high")])
def test_risk_tier_takes_the_worse_of_sensitivity_and_model_risk(base, sens, risk, tier):
    pol = base[0]
    assert portfolio.risk_tier({"data_sensitivity": sens, "model_risk": risk}, pol) == tier


@pytest.mark.parametrize("diff,sens,src", [(1, 2, "buy"), (2, 3, "buy"), (1, 4, "hybrid"), (3, 3, "hybrid"), (4, 2, "build"), (2, 5, "build")])
def test_sourcing_rule(diff, sens, src):
    assert portfolio.sourcing({"differentiation": diff, "data_sensitivity": sens})[0] == src
