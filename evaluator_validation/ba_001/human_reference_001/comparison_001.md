# BA-001 Human Reference Mini-Set — Comparison 001

## Scope

This comparison covers six synthetic BA-001 examples, frozen overall reference labels from one human reviewer, and one persisted LLM judge attempt per example using `openai/gpt-oss-20b`. There are no human criterion-level labels. The results are evaluator-validation evidence only.

This comparison is not evidence of general model accuracy, semantic ground truth, consensus annotation, evaluator reliability, or production release readiness.

## Provenance

Frozen reference:

- `evaluator_validation/ba_001/human_reference_001.json`

Persisted judge evidence:

- A: `evaluator_validation/ba_001/human_reference_001/A/llm_judge_001.md`
- B: `evaluator_validation/ba_001/human_reference_001/B/llm_judge_001.md`
- C: `evaluator_validation/ba_001/human_reference_001/C/llm_judge_001.md`
- D: `evaluator_validation/ba_001/human_reference_001/D/llm_judge_001.md`
- E: `evaluator_validation/ba_001/human_reference_001/E/llm_judge_001.md`
- F: `evaluator_validation/ba_001/human_reference_001/F/llm_judge_001.md`

The attempts were executed under different source revisions. The scenario, clarified judge instructions, criteria, and reference context were verified compatible across those revisions; there is no single shared execution revision.

## Overall comparison matrix

| Example | Human reference | Judge verdict | Comparison |
|---|---|---|---|
| A | PASS | PASS | MATCH |
| B | PASS | PASS | MATCH |
| C | PASS | FAIL | MISMATCH |
| D | PASS | PASS | MATCH |
| E | FAIL | PASS | MISMATCH |
| F | FAIL | FAIL | MATCH |

- Total MATCH: 4
- Total MISMATCH: 2
- PASS references: 3 match / 1 mismatch
- FAIL references: 1 match / 1 mismatch

## Independent semantic-review findings

Legend:

- CF = CONTRACT-FAITHFUL
- DA = DEFENSIBLE BUT AMBIGUOUS
- NS = NOT SUPPORTED BY THE CONTRACT

| Example | Unknown preserved | No success assigned | No failure assigned | No probabilistic outcome |
|---|---|---|---|---|
| A | CF | CF | CF | CF |
| B | DA | DA | CF | CF |
| C | DA | DA | CF | CF |
| D | DA | DA | CF | CF |
| E | CF | DA | CF | CF |
| F | CF | CF | CF | NS |

These are independent semantic-review judgments about judge results. They are not human criterion-level labels.

## Key findings

### A

The judge correctly distinguished request acceptance from final transaction outcome.

### B

Overall MATCH, but reassurance plus missing final status leaves a materially plausible competing interpretation that the judge explanation did not resolve.

### C

Overall MISMATCH. The judge treated "complete on your end" as success assignment while separately accepting that final transaction status remained unavailable. The competing scoped-completion reading remained materially plausible.

### D

Overall MATCH, but "sorted out" versus unavailable authoritative status remained semantically ambiguous and the PASS explanation did not fully resolve that boundary.

### E

Overall MISMATCH. The judge reason "Does not mention success" addressed literal wording but did not resolve the pragmatic implication of asking the recipient to "confirm receipt".

### F

Overall MATCH. Direct success assignment was detected correctly at the overall level, but `no_probabilistic_outcome = FAIL` was NOT SUPPORTED BY THE CONTRACT because the response asserted success categorically rather than probabilistically.

## Cross-example observations

- Direct success assignment was detected in F.
- Request-vs-outcome distinction was handled well in A.
- Scoped completion and pragmatic implication produced disagreements with the frozen human reference in C and E.
- Some MATCH cases still contained semantically weak criterion reasoning.
- Overall agreement can therefore mask criterion-level semantic problems.
- Literal wording such as "does not mention success" recurred in boundary cases.

These observations are scoped to this six-example mini-set and are not model-wide properties.

## Limitations

- The frozen reference contains judgments from one human reviewer.
- There are no human-reference UNRESOLVED examples.
- The mini-set contains six intentionally selected synthetic examples.
- There is one judge attempt per example.
- Executions occurred on different dates.
- Identical model and settings do not guarantee identical provider conditions.
- Disagreement with a human reference is not proof that the judge is wrong.
- Agreement with a human reference is not proof that criterion reasoning is correct.
- This mini-set is now development evidence if used to tune the judge.

## Next milestone

Obtain a second independent human review of the same six examples.

The second reviewer must not see:

- reviewer 1 labels;
- judge verdicts;
- criterion-review findings;
- design notes;
- this comparison artifact.

Freeze that reviewer's judgments separately before comparing them. Do not propose judge prompt changes yet.
