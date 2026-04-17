"""Health Agent Infra — deterministic tooling for an agent-owned runtime.

Python modules in this package are the runtime's *tools*: data acquisition,
validation, normalization, writeback, review persistence. All judgment
(state classification, policy application, recommendation shaping,
reporting) lives in markdown skills in the sibling ``skills/`` directory,
read by the agent that consumes this package.

See ``reporting/docs/tour.md`` for the architecture walkthrough.
"""
