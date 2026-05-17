# Observation Template (case-neutral)

Use one record per probe execution. Copy this block into a case session file or append to that case’s `observations/observations_log.md` after a black-box run.

Records describe **observable behavior only**. Do not state product defects, infer internal implementation, or assert runtime results until a probe is executed and recorded.

---

## Field definitions

| Field | Purpose |
|-------|---------|
| **Observation ID** | Unique ID (e.g. `OBS-001`). |
| **Case ID** | Assessment case (e.g. `buddy_ai`, `lindy_ai`). |
| **Scenario ID** | From the case probe design document (e.g. `1.1`, `2.3`). |
| **Claim** | Target claim under test, as named in the case claim map or probe design. |
| **System stage** | Lesson/workflow stage when the probe occurred (e.g. warm-up, practice, task execution, workflow handoff). |
| **Initial user intent** | What the user was trying to do before the probe, as stated or implied in interaction. |
| **Probe input** | Exact or paraphrased user input or action used for the probe. |
| **Observable system behavior** | What the system said or did next—verbatim or close paraphrase of visible or audible response and next lesson/workflow step. |
| **Critical decision point** | Decision dependency under test (`input → decision → consequence`). |
| **Expected coherent behavior** | From the case probe design document: what coherent handling would look like for this scenario. |
| **Observed alignment** | Factual fit to expected coherent behavior: `aligned`, `partial`, `drift`, `not observed`, or `inconclusive`. Not a score. |
| **Recovery** | Whether the system visibly corrected after ambiguity or mismatch: `yes`, `no`, `not applicable`, or `not observed`. |
| **Lesson/workflow continuity impact** | Observed downstream effect on lesson/workflow progression after the decision point (see below). Not a hypothesis. |
| **Propagation potential** | Possible future risk that early behavior could affect later lesson/workflow steps: `low`, `medium`, `high`, `not assessed`, or `not observed`. |
| **AIRRA drift type** | Potential drift pattern from the case probe design document (label only—not a finding until observed). |
| **Evidence notes** | Timestamp, session ref, stage transitions, or other observable context. No internal architecture. |
| **Status** | `planned`, `recorded`, or `incomplete`. |

---

## Record template

```markdown
### OBS-___

| Field | Value |
|-------|-------|
| Observation ID | OBS-___ |
| Case ID | |
| Scenario ID | |
| Claim | |
| System stage | |
| Initial user intent | |
| Probe input | |
| Observable system behavior | |
| Critical decision point | |
| Expected coherent behavior | |
| Observed alignment | |
| Recovery | |
| Lesson/workflow continuity impact | |
| Propagation potential | |
| AIRRA drift type | |
| Evidence notes | |
| Status | planned |
```

---

## Lesson/workflow continuity impact

**Purpose:** Capture observed downstream effects on lesson/workflow progression after a decision point.

**Examples:** `no visible impact`, `influenced next activity selection`, `shifted topic or task`, `affected later feedback or validation`, `unclear`

This field records **observed consequences**. Do not treat it as a hypothesis.

**Propagation potential** — possible future risk whether early behavior *could* affect later lesson/workflow steps.

**Lesson/workflow continuity impact** — observed effect on what happened next in the interaction.

---

## Observed alignment (usage)

- **aligned** — Observable behavior matches expected coherent behavior for this probe.
- **partial** — Some expected behaviors appear; others are missing or unclear from outside.
- **drift** — Interaction stayed coherent locally, but behavior matched a documented *potential drift pattern* from the case probe design document.
- **not observed** — Session not run or this probe not attempted.
- **inconclusive** — Run completed; observable evidence insufficient to classify.

---

## AIRRA drift type (usage)

Use the **potential drift pattern** label from the case probe design document for the scenario. This names a risk pattern to watch for—not a confirmed defect.
