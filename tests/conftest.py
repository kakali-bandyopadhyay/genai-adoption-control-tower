import copy
import pytest
from tower import data, gates, portfolio


@pytest.fixture
def base():
    pol, ucs, rows = data.load_policy(), data.load_use_cases(), data.load_telemetry()
    return pol, portfolio.prioritise(ucs, pol), rows


@pytest.fixture
def decisions(base):
    pol, pr, rows = base
    return {d["use_case"]: d for d in gates.decide_all(pr, copy.deepcopy(rows), pol)}
