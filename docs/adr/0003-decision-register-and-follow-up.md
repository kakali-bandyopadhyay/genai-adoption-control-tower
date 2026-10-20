# ADR 0003 – Decisions are recorded with an expected outcome and checked at the next review

**Status:** Accepted (20 Oct 2026)

## Context
A review that produces decisions but never checks them becomes a report. Leaders need to see whether last time's decision worked before making the next one.

## Decision
- Every decision is recorded with rationale, owner, decided-by, a review-by week and **one expected outcome** (metric, operator, target) from the metric register.
- The register is append-only (`python -m tower record` adds; nothing rewrites an entry). Each recorded entry carries the input fingerprint it was made on.
- At each review, expectations due are marked MET or MISSED from the telemetry; **two consecutive misses for a use case escalate to the sponsor** (`policy.json` follow_up).

## Consequences
- UC01's adoption decision missed twice and is escalated (tested).
- An expectation must use a registered metric, so "success" is defined before the decision, not after.
