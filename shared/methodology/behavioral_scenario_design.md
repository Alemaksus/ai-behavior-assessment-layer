# Behavioral Scenario Design Rule

Every executable behavioral scenario must define:

1. **Behavioral claim** — What system behavior is expected to remain true.

2. **Setup / known state** — What is known to the system before the interaction.

3. **User input** — The exact stimulus presented to the system.

4. **Expected behavior** — What the system should do.

5. **Forbidden behavior** — What observable behavior would violate the claim.

6. **Evidence** — What runtime data must be captured to assess the behavior.

7. **Deterministic checks** — Only conditions that can be evaluated without semantic interpretation.

## Evidence boundaries

- A deterministic check must not pretend to evaluate behavior that requires semantic interpretation.

- If a behavioral claim cannot be fully assessed deterministically, the scenario must explicitly leave that part unresolved for semantic evaluation, such as manual assessment or LLM-as-a-judge.

- Passing deterministic checks does **not** by itself mean that the behavioral claim passed.

- The strength of the verdict must not exceed the strength of the collected evidence.

## Design principle

**Evidence must support the claim. A test must not report a stronger behavioral conclusion than its evaluation method can justify.**
