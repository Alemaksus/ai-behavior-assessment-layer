# Buddy.ai — Deferred Runtime Behavioral Assessment Case

Black-box behavioral assessment of a voice-based conversational AI tutor. Runtime interaction through the mobile app is **required** for evidence collection and has **not** been observed in this repository.

## Purpose

This case examines whether a polished, coherent tutoring workflow can remain user-friendly while misaligning with learner intent or lesson direction—without visible errors. Scope is defined by publicly stated product claims and implied decision dependencies, not internal implementation.

**Deferred runtime:** Probe design and observation templates are prepared; black-box runs against the live app are pending until mobile access is available.

## Current Evidence

| Type | Location | Status |
|------|----------|--------|
| Public claim analysis | `docs/claim_map.md`, `docs/system_overview.md` | Available |
| Black-box probe design | `docs/test_design.md` | Available |
| Planned runtime probes | `sessions/`, `observations/` | Not executed |

No runtime behavior, observation records, or findings are claimed here.

## Deferred Runtime

Evidence collection depends on:

- **Mobile app** — voice lessons run in the Buddy.ai app, not a browser-only flow accessible from this repo.
- **Access constraints** — subscription, device, child profile, or regional limits may block or delay probe execution.

Until runtime access is established, this case remains **claim- and design-level** only.

## Existing Templates

Prepared for deferred execution; all entries are **planned** or **deferred** probes, not observed evidence.

| Artifact | Path | Role |
|----------|------|------|
| Session plans | `sessions/session_01_intent_interpretation.md`, `sessions/session_02_feedback_integrity.md` | Warm-up intent and practice feedback scenarios |
| Observation index | `observations/observations_log.md` | 13 planned probes mapped to scenario IDs |
| Observation template | `observations/observation_template.md` | Field definitions for future records |

Scenario logic in test design and session files remains useful when runtime access is available; it does not imply prior observation.

## Notes

- **Runtime observations are deferred** — no filled observation records represent live app behavior.
- **Public claim assessment only** — current value is mapping claims to decision dependencies and documenting probes awaiting execution.
- Do not infer architecture, models, or defects from this case folder.
