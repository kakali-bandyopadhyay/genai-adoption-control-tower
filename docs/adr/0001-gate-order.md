# ADR 0001 – Gate order: controls, then quality, then adoption, then expansion

**Status:** Accepted (20 Oct 2026)

## Context
A weekly review sees many numbers at once. Ranking pilots on an average (or on adoption) would let a pilot with a control failure expand because its other numbers look good.

## Decision
Checks run in a fixed order, and the first that fires decides:
1. any critical control incident in the last four weeks → **PAUSE**;
2. eval pass below the tier bar or overrides above it → **FIX (quality)**;
3. adoption below the tier bar → **FIX (adoption)**;
4. every bar met for three consecutive weeks → **EXPAND** one stage;
5. otherwise **CONTINUE**.
High-risk use cases keep human review at every stage, whatever the numbers.

## Consequences
- A strong pilot can be paused; that is the intended behaviour (tested: UC03).
- Quality and adoption problems get different actions, because they have different causes (tested: UC01 vs UC02).
- One good week never expands a pilot (tested).
