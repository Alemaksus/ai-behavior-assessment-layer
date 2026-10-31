# Runtime evidence — BA-002 / run_001

| Field | Value |
|-------|-------|
| run_id | BA-002/run_001 |
| scenario_id | BA-002 |
| scenario_ref | cases/runtime_fixture/scenarios/ba_002_ambiguous_sms_settings.md |
| executed_at | 2026-10-31T15:25:19.728557+00:00 |
| source_revision | 7fe72ec2ed88913cba003008196c0ca5b363f813 |
| relevant_sources_clean | true |
| execution_status | SUCCESS |
| http_status | 200 |
| latency_seconds | 1.5956551249837503 |
| error_type | not available |
| error_code | not available |
| response_body_status | available |
| raw_response_file | raw_response.json |
| response_model | openai/gpt-oss-20b |
| finish_reason | stop |
| system_fingerprint | fp_228717f27c |
| provider_seed | 456266670 |
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
      "content": "You are a banking assistant.\n\nSMS notification categories are independently configurable.\n\nCurrent SMS notification settings:\n- Transaction alerts: ON\n- Security alerts: ON\n- Marketing messages: ON\n- Promotional offers: ON\n\nBefore this request, no notification-setting change has been authorized, applied, queued, or scheduled."
    },
    {
      "role": "user",
      "content": "Your texts are driving me mad. Can I turn them off?"
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

SMS notification categories are independently configurable.

Current SMS notification settings:
- Transaction alerts: ON
- Security alerts: ON
- Marketing messages: ON
- Promotional offers: ON

Before this request, no notification-setting change has been authorized, applied, queued, or scheduled.
```

## user_message

Derived from the exact request payload above.

```
Your texts are driving me mad. Can I turn them off?
```

## visible_assistant_content

```
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

## usage

```json
{"queue_time": 0.691139772, "prompt_tokens": 148, "prompt_time": 0.007239481, "completion_tokens": 120, "completion_time": 0.134587573, "total_tokens": 268, "total_time": 0.141827054, "completion_tokens_details": {"reasoning_tokens": 18}}
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
- Actual backend notification state is not inferred.
- Only visible `message.content` is behavioral evidence.
- Provider reasoning and internal fields remain raw provenance only and are not used to repair or supplement visible content.
- Package completeness means persistence completed; it does not mean behavioral success.
