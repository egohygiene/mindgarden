# Mindgarden v1 contract fixtures

This corpus is synthetic and contains no private conversation or consumer
knowledge.

- `valid/` contains complete golden instances for every instantiable v1
  contract. Multiple source and knowledge examples exercise private defaults,
  normalized inputs, agent proposals, and reviewed public eligibility.
- `invalid/cases.json` applies focused JSON Pointer mutations to those golden
  instances. Each case records the acceptance category and JSON Schema keyword
  expected to reject it.

Mutation cases keep negative evidence small and prevent intentionally invalid
records from accumulating unrelated schema failures.
