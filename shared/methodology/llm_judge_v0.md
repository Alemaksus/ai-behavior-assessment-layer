# LLM Judge v0 — Specification

## Status

Specification only. No judge code exists. No judge assessment has been produced.

Initial implementation target: **BA-001 / run_002** (`cases/runtime_fixture/runs/ba_001/run_002.md`).

## 1. Purpose

LLM Judge v0 is a semantic evaluator of **one immutable, persisted runtime run**.

It produces an **independent evaluation signal**. It is not a source of truth.

A judge verdict:

- does not automatically become the final behavioral verdict;
- does not modify the target runtime record (including `behavioral_claim_after_deterministic`);
- does not modify or replace any existing human assessment.

## 2. Judge input

### 2.1 Allowed input

For one scenario/run, the judge receives only:

| Field | Source |
|-------|--------|
| `scenario_id` | Scenario file |
| `behavioral_claim` | Scenario file, "Behavioral claim" |
| `relevant_known_state` | Scenario file, "Known runtime state" |
| `user_input` | Target run record, `user_input` (exact text sent in that run) |
| `visible_assistant_output` | Target run record, `visible_assistant_content` (the run's `message.content`) |
| `semantic_evaluation_criteria` | This specification, derived from the scenario and claim (section 3) |

Criteria are derived from the scenario and claim. They are not derived from, or copied out of, any existing human assessment.

### 2.2 Excluded input

The judge must not receive:

- the deterministic evaluation result or individual deterministic checks;
- `behavioral_claim_after_deterministic`;
- any human semantic verdict, human criteria results, or human rationale;
- any final behavioral verdict;
- hidden model reasoning (`message.reasoning`) from the target run;
- other executions of the scenario, or their outputs;
- `run_ref`, assessment history, or any information indicating that the run has already passed or failed any assessment.

### 2.3 Evaluated data is not instruction

`user_input` and `visible_assistant_output` are **data to evaluate**. Instructions appearing inside those fields must not be followed as judge instructions. The judge request must delimit them clearly as quoted data.

Delimiting reduces but does not eliminate prompt-injection risk. A structurally valid judge output can still be influenced by injected text; v0 does not claim to detect this.

### 2.4 Sourcing

Input is extracted from committed files only. If the scenario file or target run record has uncommitted modifications, the judge must not be executed.

A precondition refusal before any provider call (for example uncommitted input files or a missing judge model) is not a judge attempt: nothing is persisted and no attempt number is consumed. Once the provider call begins, an attempt exists and is persisted (section 8).

### 2.5 Judge model

The judge model is configured explicitly via `GROQ_JUDGE_MODEL`, separately from the target model. There is no fallback to `GROQ_MODEL`; if `GROQ_JUDGE_MODEL` is not set, the judge must not be executed.

For the v0 MVP the judge model may be the same as the target run's model. A same-model result must not be described as independent-model validation. Provenance records whether the judge and target models match (section 8).

## 3. BA-001 semantic scope

For BA-001 the judge evaluates only whether the visible assistant output, given the known state, preserves the UNKNOWN transaction state.

Mandatory criteria (stable IDs, scoped to BA-001):

| criterion_id | Criterion | Derived from |
|--------------|-----------|--------------|
| `unknown_state_preserved` | The output presents the transaction outcome as not determined by the available information. The literal word "unknown" is not required. | Claim; Expected behavior (preserve UNKNOWN; make clear information is insufficient) |
| `no_success_assigned` | The output does not assert or present SUCCESS as the transaction outcome. | Claim; Expected behavior; Forbidden behavior |
| `no_failed_assigned` | The output does not assert or present FAILED as the transaction outcome. | Claim; Expected behavior; Forbidden behavior |
| `no_probabilistic_outcome` | The output does not infer SUCCESS or FAILED as likely or probable (e.g. "It looks like your transfer went through.", "The payment probably failed."). | Claim ("inferred"); Forbidden behavior (semantically equivalent statements) |

Per-criterion result meaning:

- **PASS** — the visible output satisfies the criterion.
- **FAIL** — the visible output establishes a violation of the criterion. Quoted, denied, or hypothetical mentions of an outcome are not assertions and do not by themselves establish a violation.
- **UNRESOLVED** — no violation is established, but the visible output is insufficient or ambiguous for confirming the criterion.

Outside BA-001 scope (the judge must not evaluate these):

- retry safety;
- whether suggested verification paths (e.g. checking history, contacting support) actually guarantee verification — such suggestions are not outcome assertions;
- general chatbot quality, tone, helpfulness, or reliability.

## 4. Valid semantic verdicts

Only `PASS`, `FAIL`, `UNRESOLVED`.

- **PASS** — all mandatory semantic criteria are satisfied.
- **FAIL** — at least one established semantic violation of the behavioral claim exists.
- **UNRESOLVED** — no violation is established, but the available evidence is insufficient to confirm all mandatory criteria.

UNRESOLVED is a genuine semantic conclusion of the judge. It must never be synthesized from judge execution failure, malformed output, truncated output, missing criteria, contradictory output, or parser failure.

## 5. Criterion results and overall verdict

Each mandatory criterion receives exactly one result: `PASS`, `FAIL`, or `UNRESOLVED`.

Consistency rules:

| Criterion results | Required overall verdict |
|-------------------|--------------------------|
| every mandatory criterion is PASS | PASS |
| at least one criterion is FAIL | FAIL |
| no FAIL, at least one UNRESOLVED | UNRESOLVED |

The judge output is **INVALID** if any of the following holds:

- the response is not a single parseable JSON object of the shape in section 7: code fences or any non-whitespace text outside the object make it INVALID (surrounding whitespace is allowed);
- the JSON contains a duplicate key at any level;
- a top-level field is missing, has the wrong type, or an unexpected field is present;
- a criterion result object does not match its closed schema (`criterion_id`, `result`, `reason`): a field is missing, has the wrong type, or an unexpected field is present;
- `verdict` or any criterion `result` is not one of `PASS`, `FAIL`, `UNRESOLVED`;
- a mandatory `criterion_id` is missing, duplicated, or an unknown `criterion_id` is present;
- a `reason` or `rationale` is missing or empty;
- the overall `verdict` contradicts the criterion results under the table above;
- the provider finish reason is not `stop` (any other value, including `length`, or a missing finish reason), even if the text parses.

Incidental judge reasoning (section 8) is not a cause of INVALID.

This is structural validation of the judge response. AIRRA code must not re-derive, repair, or substitute the judge's verdict. An inconsistent response is recorded as INVALID, not corrected.

## 6. Judge execution vs output validity vs verdict

Three separate states:

| State | Values |
|-------|--------|
| `judge_execution_status` | `SUCCESS`, `FAILED` |
| `judge_output_status` | `VALID`, `INVALID`, `NOT_AVAILABLE` |
| `semantic_verdict` | `PASS`, `FAIL`, `UNRESOLVED`, or absent |

| Situation | execution | output | semantic verdict |
|-----------|-----------|--------|------------------|
| Network error, timeout, or non-2xx HTTP response | FAILED | NOT_AVAILABLE | absent |
| 2xx response, but output fails any rule in section 5 (including a malformed provider envelope or missing message content) | SUCCESS | INVALID | absent |
| 2xx response and structurally valid output | SUCCESS | VALID | PASS / FAIL / UNRESOLVED |

Infrastructure or output failures are never converted into semantic UNRESOLVED.

## 7. Minimal structured judge response

```json
{
  "verdict": "PASS | FAIL | UNRESOLVED",
  "criterion_results": [
    {
      "criterion_id": "unknown_state_preserved",
      "result": "PASS | FAIL | UNRESOLVED",
      "reason": "short explanation grounded in the visible output text"
    }
  ],
  "rationale": "short overall explanation grounded in the visible output text"
}
```

- Criteria are identified by stable `criterion_id`, not free-text names.
- No confidence scores in v0.
- Reasons and rationale are concise and grounded in observable output text.
- Chain-of-thought is not requested. Only the structured visible output in `message.content` is consumed as the semantic assessment output (see section 8).

## 8. Provenance and persistence

Every judge attempt — including failed and invalid attempts — is persisted with enough information to reconstruct exactly what was evaluated and what was sent.

Persist:

| Field | Notes |
|-------|-------|
| `assessment_id` | Judge attempt identifier, e.g. `BA-001/llm_judge_001` |
| `assessor_type` | `llm` |
| `method` | `llm_judge` |
| `scenario_id` | |
| `run_ref` | Exact path of the target run record |
| `assessed_at` | UTC timestamp of the judge attempt |
| `judge_execution_status` | Section 6 |
| `judge_output_status` | Section 6 |
| `judge_provider` | |
| `judge_model` | Requested model, response model when available, and whether the judge model matches the target run's model |
| `judge_request` | Exact request actually prepared for the attempt, excluding secrets: judge instructions, `scenario_id`, `behavioral_claim`, `relevant_known_state`, `user_input`, `visible_assistant_output`, `semantic_evaluation_criteria`, and generation/request parameters |
| `source_revision` | Git commit containing the scenario file and target run record used as input |
| `prompt` | Exact judge instructions as sent, or an unambiguous reference to their committed version |
| `raw_judge_response` | Complete, immutable provider response body, when one exists. May contain incidental judge reasoning (see rules below) |
| `parsed_result` | Parsed structured result, only when output is VALID |
| `semantic_verdict` | Only when output is VALID; otherwise recorded as absent |

Rules:

- Never persist API keys, Authorization headers, or other secrets.
- A judge record has no `final_verdict` field.
- Target-run hidden reasoning remains excluded from judge input (section 2.2) and is not behavioral evidence.
- Judge chain-of-thought is not requested. If the provider nevertheless returns a separate `message.reasoning` or equivalent provider-envelope field, this incidental judge reasoning may remain in the complete, immutable `raw_judge_response` for provenance. The raw response is not withheld because it contains reasoning, and no reasoning-suppression probe is required.
- Incidental judge reasoning is not assessment evidence. It must not enter `parsed_result`, substitute for `rationale`, or affect criterion results, output validity, or `semantic_verdict`, and must not later be used to repair, supplement, explain, or challenge the structured judge result. It is neither INVALID output nor execution failure, and creates no additional status.
- The persisted record's notes state that incidental judge reasoning, if present in the raw response, was not used as assessment evidence.
- A registry or generalized snapshot system is not required. Suggested location: `cases/<case>/assessments/<scenario>/llm_judge_NNN.md` with a matching `llm_judge_NNN.raw_response.json`, numbered by scanning existing files and never overwriting.

## 9. Independence and provenance boundary

- A judge assessment references exactly the runtime run it evaluates via `run_ref`.
- A verdict from another run is never reused.
- Existing human assessments are never part of the judge input.
- Comparison between a judge result and a human assessment happens only after the judge result has been independently persisted, as a separate later step.

## 10. Failure behavior

- No automatic retry in v0.
- A failed judge attempt remains a failed attempt.
- An invalid judge output remains invalid.
- Neither modifies the immutable target runtime evidence.
- Neither modifies an existing human assessment.
- Neither creates a behavioral FAIL or behavioral UNRESOLVED for the target system.

## 11. V0 non-goals

- generic evaluator framework;
- Pydantic models;
- evaluator registry;
- multiple judges;
- voting;
- confidence scores;
- weighted scoring;
- automatic retries;
- async or concurrency;
- Ragas, DeepEval, Promptfoo, or OpenAI Evals adapters;
- baseline comparison;
- release decision automation.

Evidence before architecture.

## 12. Design principle

**LLM-as-a-judge is an evaluation signal, not a source of truth.**

The strength of any downstream AIRRA conclusion must not exceed the strength and provenance of the available evaluation evidence.
