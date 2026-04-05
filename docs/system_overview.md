# System Overview — Conversational AI Tutor

## System Type

Voice-based conversational AI tutor.

The system combines:
- speech recognition
- conversational interaction
- structured lesson flow
- game-based learning mechanics

## Core Interaction Model

The system operates as a guided conversational loop where each turn hinges on **decision awareness**: what the system infers from the user, what it chooses to do next in the lesson, and how it responds.

User input (speech)
→ intent interpretation
→ lesson progression decision (what to do next)
→ system response (instruction / feedback / question)
→ next user input

## Lesson Structure

Based on publicly described workflow:

- Warm-up
- Introduction / Presentation
- Practice
- Application / Production

Each stage builds on previous steps and assumes correct interpretation of user input.

## Personalization Layer

The system adapts learning based on:
- selected proficiency level
- observed responses
- engagement patterns

This creates a dynamic learning path for each user.

## Key Behavioral Dependencies

System behavior depends on:

- correct interpretation of user speech
- continuity of lesson context
- accurate feedback during practice
- alignment between user intent and lesson direction

## Critical Observation

The system is structured in a way where:

A small deviation in early interpretation can propagate through the entire lesson flow while the system remains coherent and produces no visible errors.

## Scope note

This overview is based on publicly described system behavior and observed interaction patterns.  
No assumptions are made about internal implementation.