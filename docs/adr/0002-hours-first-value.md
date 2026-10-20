# ADR 0002 – Value is reported in hours saved first, money second

**Status:** Accepted (20 Oct 2026)

## Context
Money values for GenAI are easy to inflate (a high hourly rate, cost counted as model calls only).

## Decision
Hours saved (accepted tasks × minutes saved per task) is the primary measure. Money is a translation at an illustrative, stated rate; cost is labelled "model run cost" because licences, infrastructure and support are excluded.

## Consequences
The memo and dashboard never present a return-on-investment figure; leadership sees hours, run cost and cost per task, with the assumptions named.
