# Observation Template

Use one record per probe execution. Copy this block into a session file or append a row to `observations_log.md` after a black-box run.

Records describe **observable behavior only**. Do not state product defects or infer internal implementation.

---

## Field definitions

| Field | Purpose |
|-------|---------|
| **Observation ID** | Unique ID (e.g. `OBS-001`). |
| **Scenario ID** | From `docs/test_design.md` (e.g. `1.1`, `2.3`). |
| **Claim** | Target claim name from test design (e.g. Voice-based interaction, Mastery learning). |
| **Lesson stage** | Stage when the probe occurred (e.g. Warm-up, Practice). |
| **Initial user intent** | What the learner was trying to do before the probe, as stated or implied in interaction. |
| **Probe input** | Exact or paraphrased user speech/behavior used for the probe. |
| **Observable system behavior** | What the tutor said or did next—verbatim or close paraphrase of audible/visible response and lesson move. |
| **Critical decision point** | Decision dependency under test (`input → decision → consequence`). |
| **Expected coherent behavior** | From test design: what coherent handling would look like for this scenario. |
| **Observed alignment** | Factual fit to expected coherent behavior: `aligned`, `partial`, `drift`, `not observed`, or `inconclusive`. Not a score. |
| **Recovery** | Whether the system visibly corrected after ambiguity or mismatch: `yes`, `no`, `not applicable`, or `not observed`. |
| **Propagation potential** | Possible future risk that early behavior could affect later lesson steps: `low`, `medium`, `high`, `not assessed`, or `not observed`. |
| **Lesson continuity impact** | Observed downstream effect on lesson progression after the decision point (see below). Not a hypothesis. |
| **AIRRA drift type** | Potential drift pattern from test design (hypothesis label only—not a finding until observed). |
| **Evidence notes** | Timestamp, session ref, stage transitions, or other observable context. No internal architecture. |
| **Status** | `planned`, `recorded`, or `incomplete`. |

---

## Record template

```markdown
### OBS-___

| Field | Value |
|-------|-------|
| Observation ID | OBS-___ |
| Scenario ID | _._ |
| Claim | |
| Lesson stage | |
| Initial user intent | |
| Probe input | |
| Observable system behavior | |
| Critical decision point | |
| Expected coherent behavior | |
| Observed alignment | |
| Recovery | |
| Propagation potential | |
| Lesson continuity impact | |
| AIRRA drift type | |
| Evidence notes | |
| Status | planned |
```

---

## Lesson continuity impact

**Purpose:** Capture observed downstream effects on lesson progression after a decision point.

**Examples:** `no visible impact`, `influenced next activity selection`, `shifted lesson topic`, `affected later feedback behavior`, `unclear`

This field records **observed consequences**. Do not treat it as a hypothesis.

**Propagation potential** (keep) — possible future risk whether early behavior *could* affect later steps.

**Lesson continuity impact** — observed effect on what happened next in the lesson.

---

## Observed alignment (usage)

- **aligned** — Observable behavior matches expected coherent behavior for this probe.
- **partial** — Some expected behaviors appear; others are missing or unclear from outside.
- **drift** — Interaction stayed coherent locally, but behavior matched a documented *potential drift pattern* from test design.
- **not observed** — Session not run or this probe not attempted.
- **inconclusive** — Run completed; observable evidence insufficient to classify.

---

## AIRRA drift type (usage)

Use the **potential drift pattern** label from `docs/test_design.md` for the scenario (e.g. “lesson proceeds on incorrect grounding”). This names a risk pattern to watch for—not a confirmed defect.
