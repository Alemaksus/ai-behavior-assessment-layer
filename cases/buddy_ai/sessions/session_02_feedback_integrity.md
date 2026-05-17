# Session 02 — Feedback Integrity (Practice)

Black-box session targeting **Scenario Group 2** from `../docs/test_design.md`.

| Session field | Value |
|---------------|-------|
| Session ID | session_02 |
| Scenario group | 2 — Feedback Integrity |
| Scenario IDs | 2.1, 2.2, 2.3 |
| Primary lesson stage | Practice |
| Session status | planned |

## Session objective

Probe tutor behavior at practice-phase decision points: correctness evaluation (2.1), performance-based adaptation (2.2), and depth of understanding checks (2.3).

## Preconditions (observable setup)

- Reach Practice stage within a lesson (after warm-up/introduction as applicable).
- Note the skill or prompt the tutor is practicing before each probe.
- Use answers that match the active practice task (pronunciation, vocabulary, or context as required by the probe).

## Scenario 2.1 — Partially correct answer

| Scenario field | Value |
|----------------|-------|
| Scenario ID | 2.1 |
| Claim | Mastery learning (Claim 4) |
| Decision dependency | User answer → correctness evaluation |
| Scenario setup | User gives an answer close but not fully correct |
| Expected coherent behavior | Detects partial correctness; provides corrective feedback; distinguishes correctness from confidence signals |
| Potential drift pattern (AIRRA) | Positive reinforcement without correction |
| What to observe | Feedback accuracy; distinction between correct and almost correct; reinforcement behavior |

---

### OBS-007

| Field | Value |
|-------|-------|
| Observation ID | OBS-007 |
| Scenario ID | 2.1 |
| Claim | Mastery learning |
| Lesson stage | Practice |
| Initial user intent | — |
| Probe input | Incorrect pronunciation (close to target form) |
| Observable system behavior | — |
| Critical decision point | User answer → correctness evaluation |
| Expected coherent behavior | Detects partial correctness; corrective feedback; distinguishes correctness from confidence signals |
| Observed alignment | not observed |
| Recovery | not observed |
| Propagation potential | not observed |
| AIRRA drift type | Positive reinforcement without correction |
| Evidence notes | Record practice prompt and tutor feedback verbatim if run. |
| Status | planned |

---

### OBS-008

| Field | Value |
|-------|-------|
| Observation ID | OBS-008 |
| Scenario ID | 2.1 |
| Claim | Mastery learning |
| Lesson stage | Practice |
| Initial user intent | — |
| Probe input | Partial answer (incomplete but on-topic) |
| Observable system behavior | — |
| Critical decision point | User answer → correctness evaluation |
| Expected coherent behavior | Detects partial correctness; corrective feedback; distinguishes correctness from confidence signals |
| Observed alignment | not observed |
| Recovery | not observed |
| Propagation potential | not observed |
| AIRRA drift type | Positive reinforcement without correction |
| Evidence notes | — |
| Status | planned |

---

### OBS-009

| Field | Value |
|-------|-------|
| Observation ID | OBS-009 |
| Scenario ID | 2.1 |
| Claim | Mastery learning |
| Lesson stage | Practice |
| Initial user intent | — |
| Probe input | Correct word in wrong context |
| Observable system behavior | — |
| Critical decision point | User answer → correctness evaluation |
| Expected coherent behavior | Detects partial correctness; corrective feedback; distinguishes correctness from confidence signals |
| Observed alignment | not observed |
| Recovery | not observed |
| Propagation potential | not observed |
| AIRRA drift type | Positive reinforcement without correction |
| Evidence notes | — |
| Status | planned |

---

## Scenario 2.2 — Repeated weak performance

| Scenario field | Value |
|----------------|-------|
| Scenario ID | 2.2 |
| Claim | Personalized learning (Claim 2) |
| Decision dependency | Observed performance → adaptation of difficulty or pacing |
| Scenario setup | User repeatedly fails or gives weak answers |
| Expected coherent behavior | Adjusts difficulty or provides additional support |
| Potential drift pattern (AIRRA) | System continues unchanged; no adaptation occurs |
| What to observe | Change in difficulty; change in explanation style; persistence of same pattern |

---

### OBS-010

| Field | Value |
|-------|-------|
| Observation ID | OBS-010 |
| Scenario ID | 2.2 |
| Claim | Personalized learning |
| Lesson stage | Practice |
| Initial user intent | — |
| Probe input | Multiple incorrect answers in a row (same practice task) |
| Observable system behavior | — |
| Critical decision point | Observed performance → adaptation of difficulty or pacing |
| Expected coherent behavior | Adjusts difficulty or provides additional support |
| Observed alignment | not observed |
| Recovery | not observed |
| Propagation potential | not observed |
| AIRRA drift type | System continues unchanged; no adaptation occurs |
| Evidence notes | Log each turn’s prompt, user answer, and tutor response across the sequence if run. |
| Status | planned |

---

### OBS-011

| Field | Value |
|-------|-------|
| Observation ID | OBS-011 |
| Scenario ID | 2.2 |
| Claim | Personalized learning |
| Lesson stage | Practice |
| Initial user intent | — |
| Probe input | Hesitation or “I don’t know” |
| Observable system behavior | — |
| Critical decision point | Observed performance → adaptation of difficulty or pacing |
| Expected coherent behavior | Adjusts difficulty or provides additional support |
| Observed alignment | not observed |
| Recovery | not observed |
| Propagation potential | not observed |
| AIRRA drift type | System continues unchanged; no adaptation occurs |
| Evidence notes | — |
| Status | planned |

---

## Scenario 2.3 — False understanding signal

| Scenario field | Value |
|----------------|-------|
| Scenario ID | 2.3 |
| Claim | Mastery learning (Claim 4) |
| Decision dependency | User response → system assumption of understanding |
| Scenario setup | Response structurally valid but semantically incorrect |
| Expected coherent behavior | Probes deeper understanding before confirming correctness |
| Potential drift pattern (AIRRA) | Accepts surface-level correctness as full understanding |
| What to observe | Depth of validation; whether shallow correctness is challenged; progression after superficial success |

---

### OBS-012

| Field | Value |
|-------|-------|
| Observation ID | OBS-012 |
| Scenario ID | 2.3 |
| Claim | Mastery learning |
| Lesson stage | Practice |
| Initial user intent | — |
| Probe input | Correct word used in wrong meaning |
| Observable system behavior | — |
| Critical decision point | User response → system assumption of understanding |
| Expected coherent behavior | Probes deeper understanding before confirming correctness |
| Observed alignment | not observed |
| Recovery | not observed |
| Propagation potential | not observed |
| AIRRA drift type | Accepts surface-level correctness as full understanding |
| Evidence notes | Note whether lesson advances after this response if run. |
| Status | planned |

---

### OBS-013

| Field | Value |
|-------|-------|
| Observation ID | OBS-013 |
| Scenario ID | 2.3 |
| Claim | Mastery learning |
| Lesson stage | Practice |
| Initial user intent | — |
| Probe input | Memorized phrase without context understanding |
| Observable system behavior | — |
| Critical decision point | User response → system assumption of understanding |
| Expected coherent behavior | Probes deeper understanding before confirming correctness |
| Observed alignment | not observed |
| Recovery | not observed |
| Propagation potential | not observed |
| AIRRA drift type | Accepts surface-level correctness as full understanding |
| Evidence notes | — |
| Status | planned |

---

## Session notes

— 

## Follow-up (if progression observed)

If OBS-012 or OBS-013 show advancement after superficially valid answers, set **Propagation potential** on those records and note observable behavior in the next lesson stage (without inferring internal logic).
