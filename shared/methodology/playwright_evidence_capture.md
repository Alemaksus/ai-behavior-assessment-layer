# Playwright Evidence Capture Approach

## Purpose

Playwright may be used later in AIRRA Behavioral Assessment cases to preserve **browser-visible** evidence, including:

- public claims
- website states
- runtime task pages when accessible
- screenshots
- traces
- page states

This document describes the intended approach only. It does not assert that Playwright is installed or in use.

## What Playwright can support

- capturing public website claims
- preserving screenshots of relevant pages
- recording browser traces for reproducibility
- documenting observable UI states
- capturing workflow or task execution pages when runtime access exists

## What Playwright must not be used for

- inferring internal model behavior
- claiming AI defects without observable evidence
- testing mobile-only app behavior
- replacing human behavioral interpretation
- generating scores or dashboards

## Case usage

### Buddy.ai

- useful for public website claim capture only
- not suitable for mobile app runtime behavior

### Lindy AI

- potentially useful for capturing browser-visible workflow or task execution evidence
- runtime access still must be validated manually first

## Evidence discipline

Captured evidence should always be linked to:

- case ID
- session ID
- observation ID
- scenario or probe ID
- timestamp
- source URL or runtime page

Artifacts should be stored under the relevant case (for example `cases/<case_id>/docs/runtime_surface.md` or case observation records), not treated as standalone proof without observation context.

## Status

Documentation only.

Playwright is not installed yet.

No automated evidence capture has been implemented.
