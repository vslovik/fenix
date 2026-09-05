---
label: AI agent engineering
want: true
---

We are looking for an engineer to build and operate agentic systems in production. You will design
the orchestration layer: tool calling, structured extraction, retry and fallback behaviour, memory
across turns, and the boundaries between what the model decides and what deterministic code
decides. Most of the work is making non-deterministic components behave predictably enough to ship.

You will own the evaluation harness alongside the system itself — regression suites over recorded
traces, offline scoring before release, and the instrumentation that tells you when a prompt change
has quietly degraded a downstream step.

Our stack is Python, with local and hosted models behind a single interface, a vector store for
retrieval, and event-driven workers on AWS. We care more about judgement in ambiguous failure modes
than familiarity with any particular framework.

You should have shipped a system where an LLM sits on the critical path and be able to describe how
you kept it honest: what you measured, what you refused to let the model do, and what broke anyway.