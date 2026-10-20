"""One evaluation pass: prioritise the portfolio and gate every live use case. Pure: inputs are not modified."""
from __future__ import annotations

import copy

from . import gates, portfolio


def evaluate(policy: dict, use_cases: list[dict], telemetry: list[dict]) -> tuple[list[dict], list[dict]]:
    pr = portfolio.prioritise(copy.deepcopy(use_cases), policy)
    ds = gates.decide_all(pr, copy.deepcopy(telemetry), policy)
    return pr, ds
