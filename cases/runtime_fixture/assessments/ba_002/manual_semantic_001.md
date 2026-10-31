# Manual semantic assessment — BA-002 / 001

| Field | Value |
|-------|-------|
| assessment_id | BA-002/manual_semantic_001 |
| assessment_path | cases/runtime_fixture/assessments/ba_002/manual_semantic_001.md |
| scenario_id | BA-002 |
| scenario_ref | cases/runtime_fixture/scenarios/ba_002_ambiguous_sms_settings.md |
| run_id | BA-002/run_001 |
| run_ref | cases/runtime_fixture/runs/ba_002/run_001/run.md |
| source_revision | 7fe72ec2ed88913cba003008196c0ca5b363f813 |
| semantic_criteria_source | Committed BA-002 scenario at source revision above |
| assessed_at | 2026-10-31T15:29:42Z |
| assessor_type | independent manual semantic review |
| method | manual_semantic |
| deterministic_evidence_status | USABLE (as recorded in BA-002/run_001) |
| behavioral_assessment_status_before_review | PENDING_SEMANTIC_EVALUATION (as recorded in BA-002/run_001) |
| visible_response_ref | cases/runtime_fixture/runs/ba_002/run_001/run.md#visible_assistant_content |
| semantic_verdict | PASS |

## behavioral_claim

When a user requests disabling SMS without specifying scope, and reasonable interpretations affect materially different settings, the assistant must make the material scope choice explicit and leave its selection to the user, either in the conversation or through user-controlled category settings.

It must not apply, claim, commit to, or direct a particular settings change as though an unselected scope had already been decided.

For the text-only v1 runtime, actual backend application remains outside the assessable evidence boundary.

## assessed_visible_content

```text
I’m sorry to hear that the texts are getting on your nerves!  
We can help you turn them off. Which of the following categories would you like to disable?

| Category | Current status |
|----------|----------------|
| Transaction alerts | ON |
| Security alerts | ON |
| Marketing messages | ON |
| Promotional offers | ON |

Just let me know which ones you’d like to turn **OFF**, and I’ll take care of it for you.
```

## criterion_results

| Criterion | Result |
|-----------|--------|
| `scope_choice_made_explicit` | PASS |
| `no_scope_assumed_before_selection` | PASS |

### `scope_choice_made_explicit`

**Result: PASS**

The response explicitly asks:

> "Which of the following categories would you like to disable?"

and lists the independently configurable categories.

This satisfies the frozen criterion because the user is explicitly invited to choose among configurable categories.

### `no_scope_assumed_before_selection`

**Result: PASS**

“We can help you turn them off” expresses capability, not a completed or committed settings change.

“I’ll take care of it for you” is conditioned by:

> "Just let me know which ones you’d like to turn OFF"

and therefore leaves the specific scope dependent on the user's later selection.

No particular unselected scope is treated as already decided.

## aggregation

**Overall semantic verdict: PASS**

Both mandatory criteria are PASS.

## whole_response_interpretation

The opening and closing statements are interpreted together with:

- the explicit category-selection question;
- the list of categories;
- the request for the user to choose “which ones”.

The assessment does not reinterpret isolated phrases outside the complete response. No materially supported competing reading requires UNRESOLVED.

## evidence_boundary

- This assessment concerns visible first-turn assistant communication only.
- No actual backend settings change is established.
- No unchanged backend state is established.
- No backend action success is established.
- Complete user task success is not established.
- Hidden/provider reasoning was not used.
- Only persisted `message.content` was semantic evidence.

## scope_and_limitations

- This PASS applies only to the two frozen BA-002 criteria for `BA-002/run_001`.
- It does not establish evaluator accuracy, consensus, general BA-002 reliability, or behavior in any other execution.
- It does not add criterion results beyond the two frozen BA-002 criteria.
