# Claim Map — Conversational AI Tutor Assessment

This document maps publicly stated product claims to observable system behavior and black-box assessment targets.

The goal is not to verify internal implementation details, but to identify:

- what the product promises
- what behavior those promises imply
- what can be observed from outside
- where silent drift may appear without visible failure

## Claim Mapping Structure

Each claim is analyzed through five questions:

1. **Public claim**  
   What the product explicitly promises.

2. **Behavioral implication**  
   What system behavior must exist for this claim to be meaningfully true.

3. **Decision dependency**  
   What decision the system must get right for the claim to hold in practice (stated as *input → decision → consequence*).

4. **Observable signals**  
   What can be checked in a black-box interaction.

5. **AIRRA risk if weak**  
   What kind of release-risk pattern may appear if the behavior is only partially true.

---

## Claim 1 — Voice-based interaction

### Public claim (Claim 1)

Buddy hears and responds using voice recognition and AI technology.

### Behavioral implication (Claim 1)

The system must interpret spoken child input reliably enough to support lesson progression and feedback.

### Decision dependency (Claim 1)

Spoken child input → correct lesson-level interpretation → progression and feedback address the intended answer or skill.

### Observable signals (Claim 1)

- recognition of short spoken answers
- handling of unclear or delayed responses
- distinction between valid, partially valid, and invalid answers
- recovery after misunderstanding

### AIRRA risk if weak (Claim 1)

The lesson may continue coherently while being based on an incorrect interpretation of the learner’s speech.

---

## Claim 2 — Teaching tailored to your child

### Public claim (Claim 2)

Buddy provides teaching tailored to the child and supports personalized learning.

### Behavioral implication (Claim 2)

The system must adjust lesson direction, pacing, or response style based on learner level or observed performance.

### Decision dependency (Claim 2)

Settings and observed answers → how much to adapt direction, pacing, and response style → the lesson trajectory visibly reflects those choices.

### Observable signals (Claim 2)

- differences across proficiency settings
- different handling of strong vs weak answers
- response variation after repeated difficulty
- signs of adaptation in lesson flow

### AIRRA risk if weak (Claim 2)

The system may appear personalized while actually following a mostly fixed path, creating false confidence in learner fit.

---

## Claim 3 — Structured lesson flow

### Public claim (Claim 3)

Lessons follow a structured sequence such as Warm-up, Introduction, Practice, and Application.

### Behavioral implication (Claim 3)

Each stage should build on the previous one and preserve lesson continuity.

### Decision dependency (Claim 3)

Current stage and latest input → which step comes next and how it links to prior content → the structured sequence stays internally consistent.

### Observable signals (Claim 3)

- whether warm-up connects to the next lesson step
- whether introduced concepts are what later get practiced
- whether application checks the same concepts in context
- whether transitions remain aligned after ambiguous input

### AIRRA risk if weak (Claim 3)

A small early drift may propagate through the entire lesson while the system still appears organized and coherent.

---

## Claim 4 — Mastery learning

### Public claim (Claim 4)

Students are expected to master concepts before progressing to new material.

### Behavioral implication (Claim 4)

The system must distinguish between true understanding and superficial completion.

### Decision dependency (Claim 4)

Practice responses → mastery vs superficial completion → advancement or extra practice matches real readiness, not mere turn completion.

### Observable signals (Claim 4)

- whether incorrect or partial responses trigger repetition or correction
- whether progression slows down after repeated weak performance
- whether the system checks concept retention before moving on

### AIRRA risk if weak (Claim 4)

The product may signal progress without sufficient mastery, creating an illusion of learning advancement.

---

## Claim 5 — Safe learning space

### Public claim (Claim 5)

Buddy offers a safe, child-friendly learning environment.

### Behavioral implication (Claim 5)

The system should remain bounded, appropriate, and predictable even under unusual or off-track interaction.

### Decision dependency (Claim 5)

Off-track, ambiguous, or refusal inputs → bounded, appropriate response → child-safety holds without losing educational usefulness.

### Observable signals (Claim 5)

- behavior after off-topic input
- handling of confusion, silence, or refusal
- whether safety causes lesson avoidance or generic fallback behavior
- whether the system stays educational while remaining safe

### AIRRA risk if weak (Claim 5)

The system may remain safe in tone while losing educational usefulness, resulting in safe-but-low-value interaction.

---

## Working Note

This claim map is intentionally behavior-centered.

It does not attempt to prove whether the system architecture is strong or weak internally.  
It only defines which public promises create black-box expectations that can be assessed through observed interaction.
