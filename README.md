# AI Behavior Assessment Layer

This repository contains **AIRRA Behavioral Assessment** case studies: structured, black-box examinations of AI system behavior using observed or intentionally designed interaction scenarios.

## What this is not

- a product
- a universal testing framework
- a scoring system
- a dashboard

## What it contains

Assessments are built from:

- public claims
- implied decision dependencies
- runtime probes when accessible
- observation logs
- drift patterns

No runtime observations or findings are asserted here unless recorded in a case’s evidence files.

## Current cases

### 1. Buddy.ai

| | |
|---|---|
| **Path** | `cases/buddy_ai/` |
| **Status** | Deferred runtime case |
| **Reason** | Mobile-app runtime; possible subscription or device constraints |
| **Current value** | Public claim analysis and deferred runtime probe design |

### 2. Lindy AI

| | |
|---|---|
| **Path** | `cases/lindy_ai/` |
| **Status** | Potential runtime candidate |
| **Reason** | Browser SaaS with potentially observable workflow and task execution |
| **Current value** | Skeleton only; runtime access not validated in this repository; runtime assessment not started; no runtime evidence |

## Repository structure

```
cases/
  buddy_ai/
  lindy_ai/

shared/
  templates/
  methodology/
```

Case-specific docs, sessions, and observations live under each `cases/<name>/` directory.
