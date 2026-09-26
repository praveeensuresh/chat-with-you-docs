# ADR-0010: Follow-up questions by rewriting

**Date**: 2026-09-27
**Status**: accepted
**Deciders**: Praveen, AI assistant

## Context

The product must support a running conversation, not one-shot questions. A follow-up such
as "what about the second one?" carries no meaning on its own, so searching on those words
finds nothing useful. The search needs a question that stands alone.

Carrying a conversation also raises two smaller questions: what a past Turn holds, and how
much of the conversation is carried as it grows.

## Decision

`answer()` takes the recent Turns as history. When history is present, a rewrite step
turns the question into a Rewritten question that stands on its own, and the search runs on
that. When there is no history, the rewrite step is skipped entirely.

A Turn holds the question and the answer text only — no Citations. Only the last 6 Turns
are read; the caller may keep more for display.

## Alternatives Considered

### Alternative 1: One question at a time, no history
- **Pros**: no second model call, no rewrite prompt, much less to build and test.
- **Cons**: every follow-up must be typed out in full, which is not how people talk.
- **Why not**: a running conversation is a stated must-have, and the rewrite is the one
  step that makes it work.

### Alternative 2: Rewrite on every question, including the first
- **Pros**: one path, no branching.
- **Cons**: pays for a model call that does nothing on the first question of every session.
- **Why not**: the "is there history" test is free and certain.

### Alternative 3: Ask the model whether the question stands alone, and rewrite only if not
- **Pros**: skips the rewrite for independent follow-ups.
- **Cons**: spends a model call to decide whether to spend a model call, and can be wrong.
- **Why not**: once history exists, rewriting is harmless — a question that already stands
  alone comes back roughly unchanged.

### Alternative 4: Carry Citations in the history too
- **Pros**: the full past Turn is available.
- **Cons**: page numbers and Chunk text add noise and tokens to a prompt whose only job is
  to rewrite words.
- **Why not**: the rewrite step needs what was said, not where it came from.

## Consequences

### Positive
- Follow-ups work in normal language.
- The first question of a session costs one model call, not two.
- The rewrite prompt stays small and cannot grow without limit.

### Negative
- Every question after the first costs a second model call.
- A bad rewrite poisons the search for that whole turn, and the cause is not visible in the
  Answer.

### Risks
- The rewrite changes the meaning of the question. Mitigated by keeping the rewrite prompt
  narrow — restate the question using the recent Turns, change nothing else — and by
  testing that the search receives the Rewritten question.
- A conversation that turns to a new topic drags stale context through the rewrite.
  Mitigated by the 6-Turn window.
