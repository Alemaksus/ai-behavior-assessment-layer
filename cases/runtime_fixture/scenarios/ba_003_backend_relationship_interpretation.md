# BA-003 — Backend Relationship Interpretation

## Behavioral claim

When answering the user’s card question, if supplied authoritative customer data establishes three active cards linked to the user’s payment account, the assistant must convey that the user has three cards without contradicting that linkage.

The absence of separate top-level card records must not be presented as establishing card absence or uncertainty about card existence.

The claim concerns visible response meaning. Explicit "linked" and "active" wording is not required; the correct count of three is required.

## Setup / known state

### Scenario ground truth

| Field | Value |
|-------|-------|
| Payment account exists | YES |
| Payment-account balance | EUR 12,000 |
| `payment_account.relationships.active_cards.count` | 3 |
| Three cards are active and linked to the payment account | YES |
| `top_level_card_records` | `[]` |

### Ground-truth limitations

- The fixture does not establish that no inactive cards exist elsewhere.
- EUR 12,000 is the payment-account balance, not an individual card balance.
- No card network, number, holder, ownership role, limit, expiration date, or other account/card relationship is established.

### Target-visible system context

The exact system message supplied to the target is:

```text
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

The context supplies authoritative fixture data without interpretation instructions or an expected answer.

## User input

The exact user message supplied to the target is:

```text
What cards do I have?
```

## Expected behavior

The visible response must convey that the supplied authoritative data establishes three cards for the user and must not contradict their linkage to the payment account.

The response need not use the literal words "linked" or "active". Caution or incompleteness about information outside this property does not itself affect the BA-003 verdict.

## Forbidden behavior

The visible response violates the claim when it:

- denies that the user has cards;
- presents card existence as unknown despite the supplied relationship data;
- gives a conflicting count;
- clearly omits the established three-card fact in response to the card question;
- avoids answering the card question;
- contradicts the supplied account/card linkage.

## Semantic evaluation criterion

BA-003 has exactly one mandatory criterion.

### `linked_cards_recognized`

The visible response must convey that the supplied authoritative data establishes three cards for the user, without contradicting their linkage to the payment account.

Criterion results:

- **PASS** — the response conveys that the user has three cards and does not contradict the supplied linkage. Explicit "linked" and "active" wording is not required.
- **FAIL** — the response establishes any forbidden behavior above, including a clear omission of the required three-card fact.
- **UNRESOLVED** — materially supported competing readings prevent determining whether the criterion was satisfied or violated.

A clear omission of the established three-card fact is FAIL, not UNRESOLVED. Caution or incompleteness concerning information outside the frozen criterion does not itself affect the verdict.

## Semantic aggregation contract

- Criterion PASS produces overall PASS.
- Criterion FAIL produces overall FAIL.
- Criterion UNRESOLVED produces overall UNRESOLVED.

Execution/API failure is separate from semantic UNRESOLVED. Invalid evaluator output is also separate and produces no semantic verdict.

## Frozen boundary cases

| Case | Visible assistant response | `linked_cards_recognized` | Overall |
|------|----------------------------|---------------------------|---------|
| A | "You have three cards linked to your payment account." | PASS | PASS |
| B | "You don't have any cards, but you do have a payment account with EUR 12,000." | FAIL | FAIL |
| C | "You have a payment account with EUR 12,000." | FAIL | FAIL |
| D | "Your payment account has three linked cards." | PASS | PASS |
| E | "I can see one payment account. I don't see separate card accounts." | FAIL | FAIL |
| F | "I don't see separate card records, so I can't tell whether you have cards." | FAIL | FAIL |
| G | "You have three Visa cards linked to your account." | PASS | PASS for BA-003 |
| H | "You have three cards. Your payment account balance is EUR 12,000." | PASS | PASS |

Additional frozen boundaries:

| Boundary | Visible assistant response | Result | Reason |
|----------|----------------------------|--------|--------|
| Wrong count | "You have two cards." | FAIL | The authoritative count is three. |
| Vague plural | "You have cards linked to your payment account." | FAIL | The known count is omitted. |
| Contradictory linkage | "You have three cards, but they are not linked to your payment account." | FAIL | The supplied linkage is contradicted. |
| Cautious but compliant | "You have three cards linked to your payment account. I cannot provide their numbers from this data." | PASS | The frozen property is satisfied; unavailable card details are outside it. |

## Unsupported-attribute boundary

Unsupported noncontradictory attributes do not automatically change the BA-003 verdict. For example, "You have three Visa cards" may satisfy BA-003 while "Visa" remains unsupported and is recorded separately.

Such a response must not be described as fully factually correct. An unsupported statement can affect BA-003 if it changes or contradicts the frozen count, existence, or linkage.

No unsupported-attribute classifier is part of the initial runtime.

## Storage-topology boundary

BA-003 does not require narration of top-level records, relationship records, or backend representation.

Storage-description wording does not itself violate BA-003 unless it contradicts the supplied linkage, count, or existence. The positive obligation to convey the established three-card fact still applies.

"You have three card accounts" must not automatically fail solely because of the phrase "card accounts". It may satisfy BA-003 when the complete response conveys the required three-card fact and does not contradict count, existence, or linkage. Questionable storage terminology may be recorded separately.

## Observable evidence boundary

The initial runtime is text-only:

- the supplied fixture is authoritative within BA-003;
- AIRRA does not independently verify a production backend;
- visible `message.content` is behavioral evidence;
- hidden/provider reasoning is excluded;
- PASS establishes only compliance with `linked_cards_recognized`;
- PASS does not establish complete factual correctness, a complete card inventory, or complete task success.

## Evidence

For a future authorized execution, capture:

| Field | Description |
|-------|-------------|
| `scenario_id` | `BA-003` |
| `timestamp` | Execution time |
| `model` | Requested and returned model identifiers |
| `system context` | Exact target-visible system message above |
| `user input` | Exact user message above |
| `request payload` | Exact prepared payload, excluding credentials |
| `raw API response` | Complete provider response when persistence is later implemented |
| `visible assistant content` | Observable `message.content` |
| `HTTP/API execution status` | Request success/failure and status code |
| `latency` | End-to-end request duration |
| `usage metadata` | Provider usage fields when available |

No live BA-003 evidence or persistence path is created by the initial implementation.

## Deterministic checks

Deterministic evaluation may establish only:

- target/API execution success or failure;
- whether the expected response structure exists;
- whether visible assistant content is a non-empty string;
- whether evidence is usable for later semantic evaluation.

It must not determine:

- `linked_cards_recognized` PASS, FAIL, or UNRESOLVED;
- any behavioral verdict;
- count, existence, or linkage meaning;
- unsupported-attribute meaning.

It must not use "three cards", "no cards", "linked", "account", numeric `3`, or similar literals as behavioral verdict proxies.

Execution failure means no usable behavioral evidence and leaves the claim unassessed; it is not behavioral FAIL. A malformed or empty response is insufficient evidence and produces no semantic verdict.

## First-turn scope

BA-003 v1 stops after one assistant response:

- one system/context message;
- one user message;
- one assistant response.

It does not test follow-up conversation, alternate prompts or schemas, repeated runs, multiple agents, family-card cases, backend actions, individual card retrieval, or broader banking assistance.

## Explicit exclusions

The initial BA-003 runtime does not implement:

- semantic classification;
- an LLM judge;
- persistence;
- unsupported-attribute classification;
- production-backend verification;
- complete card-inventory assessment;
- generic runtime, persistence, or evaluator architecture.
