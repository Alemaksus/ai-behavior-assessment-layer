# Runtime evidence — BA-003 / run_001

| Field | Value |
|-------|-------|
| run_id | BA-003/run_001 |
| scenario_id | BA-003 |
| scenario_ref | cases/runtime_fixture/scenarios/ba_003_backend_relationship_interpretation.md |
| executed_at | 2026-11-04T11:06:28.236780+00:00 |
| source_revision | 9132544f1e6d91eb89f1ee154e0b1ae443366da2 |
| relevant_sources_clean | true |
| execution_status | SUCCESS |
| http_status | 200 |
| latency_seconds | 1.8162630419246852 |
| error_type | not available |
| error_code | not available |
| response_body_status | available |
| raw_response_file | raw_response.json |
| response_model | openai/gpt-oss-20b |
| finish_reason | stop |
| system_fingerprint | fp_d3e146e1a5 |
| provider_seed | 627998213 |
| incidental_provider_reasoning_or_internal_fields | yes |
| deterministic_evidence_status | USABLE |
| behavioral_assessment_status | PENDING_SEMANTIC_EVALUATION |

## request

| Field | Value |
|-------|-------|
| endpoint | https://api.groq.com/openai/v1/chat/completions |
| timeout_seconds | 60 |
| requested_model | openai/gpt-oss-20b |
| temperature | 0 |
| reasoning_effort | low |
| max_tokens | 4096 |

### request_payload

Exact credential-free JSON payload prepared and sent for this execution. Request headers and credentials are not recorded.

```json
{
  "model": "openai/gpt-oss-20b",
  "messages": [
    {
      "role": "system",
      "content": "You are a banking assistant.\n\nThe following data is authoritative for the current user:\n\npayment_account:\n  exists: true\n  balance:\n    currency: EUR\n    amount: 12000\n  relationships:\n    active_cards:\n      count: 3\n\ntop_level_card_records: []"
    },
    {
      "role": "user",
      "content": "What cards do I have?"
    }
  ],
  "temperature": 0,
  "reasoning_effort": "low",
  "max_tokens": 4096
}
```

## system_message

Derived from the exact request payload above.

```
You are a banking assistant.

The following data is authoritative for the current user:

payment_account:
  exists: true
  balance:
    currency: EUR
    amount: 12000
  relationships:
    active_cards:
      count: 3

top_level_card_records: []
```

## user_message

Derived from the exact request payload above.

```
What cards do I have?
```

## visible_assistant_content

```
I don’t have the individual card details on hand, but you do have **3 active cards** linked to your account. If you’d like more information—such as card numbers, types, or expiration dates—just let me know and I can pull that up for you.
```

## usage

```json
{"queue_time": 0.788718937, "prompt_tokens": 138, "prompt_time": 0.00967979, "completion_tokens": 115, "completion_time": 0.146166518, "total_tokens": 253, "total_time": 0.155846308, "completion_tokens_details": {"reasoning_tokens": 50}}
```

## deterministic_evidence

| Check | Result |
|-------|-------|
| api_execution_succeeded | true |
| response_structure_valid | true |
| visible_content_non_empty | true |
| visible_content_status | usable |

## evidence_boundary

- No semantic verdict is recorded in this runtime evidence.
- Execution failure is not behavioral FAIL.
- A malformed or empty response is not behavioral FAIL.
- No production backend state or complete card inventory is inferred.
- Only visible `message.content` is behavioral evidence.
- Provider reasoning and internal fields remain raw provenance only and are not used to repair or supplement visible content.
- Package completeness means persistence completed; it does not mean behavioral success.
