---
label: LLM evaluation and observability
want: true
---

This role owns the question of whether our language-model features are actually working. You will
build the evaluation infrastructure: offline benchmarks over curated datasets, online scoring of
live traffic, human review workflows where automated scoring is not trustworthy, and the tracing
that makes a bad output attributable to a specific step.

Concretely, you will define the metrics for each feature, build the pipelines that compute them,
and make the results visible enough that a prompt or model change cannot ship without someone
seeing its effect. When a regression appears, you will be the person who can say which component
caused it.

Python, with a data pipeline and a warehouse behind it. Experience with statistical validation is
valuable — knowing when a measured difference is real and when it is sample size.

We want someone sceptical by temperament, who has seen a benchmark be gamed by the system it was
supposed to measure and designed the replacement.