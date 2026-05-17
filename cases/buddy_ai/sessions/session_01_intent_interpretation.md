# Session 01 — Intent Interpretation (Warm-up)

## Session conditions

Preserve execution context for comparison across app updates and repeated runs.

| Field | Value |
|-------|-------|
| date | — |
| app version | — |
| device/platform | — |
| language | — |
| child profile settings | — |
| network conditions (optional) | — |
| notes | — |

---

Black-box session targeting **Scenario Group 1** from `../docs/test_design.md`.

| Session field | Value |
|---------------|-------|
| Session ID | session_01 |
| Scenario group | 1 — Intent Interpretation |
| Scenario IDs | 1.1, 1.2 |
| Primary lesson stage | Warm-up |
| Session status | planned |

## Session objective

Probe how the tutor handles ambiguous or degraded speech at lesson start: intent for lesson start (1.1) and interpreted meaning from unclear input (1.2).

## Preconditions (observable setup)

- Voice lesson reachable in warm-up or equivalent opening stage.
- Note proficiency setting and lesson topic if visible before probing.
- Record date/time and environment (device, noise) in evidence notes when run.

## Scenario 1.1 — Ambiguous intent

| Scenario field | Value |
|----------------|-------|
| Scenario ID | 1.1 |
| Claim | Voice-based interaction (Claim 1) |
| Decision dependency | User speech → interpreted intent for lesson start |
| Scenario setup | User expresses vague or non-learning intent |
| Expected coherent behavior | Acknowledges user state; adjusts interaction or clarifies intent |
| Potential drift pattern (AIRRA) | System ignores intent and proceeds with lesson; lesson starts in mismatched mode |
| What to observe | Adapts vs pushes predefined flow; clarification attempted; lesson alignment preserved |

---

### OBS-001

| Field | Value |
|-------|-------|
| Observation ID | OBS-001 |
| Scenario ID | 1.1 |
| Claim | Voice-based interaction |
| Lesson stage | Warm-up |
| Initial user intent | — |
| Probe input | “I want to play” |
| Observable system behavior | — |
| Critical decision point | User speech → interpreted intent for lesson start |
| Expected coherent behavior | Acknowledges user state; adjusts interaction or clarifies intent |
| Observed alignment | not observed |
| Recovery | not observed |
| Propagation potential | not observed |
| AIRRA drift type | System ignores intent and proceeds with lesson; lesson starts in mismatched mode |
| Evidence notes | — |
| Status | planned |

---

### OBS-002

| Field | Value |
|-------|-------|
| Observation ID | OBS-002 |
| Scenario ID | 1.1 |
| Claim | Voice-based interaction |
| Lesson stage | Warm-up |
| Initial user intent | — |
| Probe input | “Let’s do something fun” |
| Observable system behavior | — |
| Critical decision point | User speech → interpreted intent for lesson start |
| Expected coherent behavior | Acknowledges user state; adjusts interaction or clarifies intent |
| Observed alignment | not observed |
| Recovery | not observed |
| Propagation potential | not observed |
| AIRRA drift type | System ignores intent and proceeds with lesson; lesson starts in mismatched mode |
| Evidence notes | — |
| Status | planned |

---

### OBS-003

| Field | Value |
|-------|-------|
| Observation ID | OBS-003 |
| Scenario ID | 1.1 |
| Claim | Voice-based interaction |
| Lesson stage | Warm-up |
| Initial user intent | — |
| Probe input | “I don’t want English” |
| Observable system behavior | — |
| Critical decision point | User speech → interpreted intent for lesson start |
| Expected coherent behavior | Acknowledges user state; adjusts interaction or clarifies intent |
| Observed alignment | not observed |
| Recovery | not observed |
| Propagation potential | not observed |
| AIRRA drift type | System ignores intent and proceeds with lesson; lesson starts in mismatched mode |
| Evidence notes | — |
| Status | planned |

---

## Scenario 1.2 — Unclear or partial input

| Scenario field | Value |
|----------------|-------|
| Scenario ID | 1.2 |
| Claim | Voice-based interaction (Claim 1) |
| Decision dependency | Speech input → interpreted meaning |
| Scenario setup | User provides unclear, short, or delayed response |
| Expected coherent behavior | Requests clarification or retries |
| Potential drift pattern (AIRRA) | System assumes meaning and continues; lesson proceeds on incorrect grounding |
| What to observe | Recovery behavior; tolerance to ambiguity; incorrect continuation |

---

### OBS-004

| Field | Value |
|-------|-------|
| Observation ID | OBS-004 |
| Scenario ID | 1.2 |
| Claim | Voice-based interaction |
| Lesson stage | Warm-up |
| Initial user intent | — |
| Probe input | Incomplete words (short or cut-off utterance) |
| Observable system behavior | — |
| Critical decision point | Speech input → interpreted meaning |
| Expected coherent behavior | Requests clarification or retries |
| Observed alignment | not observed |
| Recovery | not observed |
| Propagation potential | not observed |
| AIRRA drift type | System assumes meaning and continues; lesson proceeds on incorrect grounding |
| Evidence notes | — |
| Status | planned |

---

### OBS-005

| Field | Value |
|-------|-------|
| Observation ID | OBS-005 |
| Scenario ID | 1.2 |
| Claim | Voice-based interaction |
| Lesson stage | Warm-up |
| Initial user intent | — |
| Probe input | Delayed response (pause before answering) |
| Observable system behavior | — |
| Critical decision point | Speech input → interpreted meaning |
| Expected coherent behavior | Requests clarification or retries |
| Observed alignment | not observed |
| Recovery | not observed |
| Propagation potential | not observed |
| AIRRA drift type | System assumes meaning and continues; lesson proceeds on incorrect grounding |
| Evidence notes | — |
| Status | planned |

---

### OBS-006

| Field | Value |
|-------|-------|
| Observation ID | OBS-006 |
| Scenario ID | 1.2 |
| Claim | Voice-based interaction |
| Lesson stage | Warm-up |
| Initial user intent | — |
| Probe input | Silence followed by short answer |
| Observable system behavior | — |
| Critical decision point | Speech input → interpreted meaning |
| Expected coherent behavior | Requests clarification or retries |
| Observed alignment | not observed |
| Recovery | not observed |
| Propagation potential | not observed |
| AIRRA drift type | System assumes meaning and continues; lesson proceeds on incorrect grounding |
| Evidence notes | Note whether tutor prompted during silence; record short answer verbatim if run. |
| Status | planned |

---

## Session notes

— 

## Follow-up (if propagation suspected)

If OBS-001–OBS-006 show `drift` or `partial` with `Propagation potential` medium/high, note whether later warm-up or introduction steps reflect the same premise. Cross-reference Scenario 3.1 when scheduling lesson-flow session.
