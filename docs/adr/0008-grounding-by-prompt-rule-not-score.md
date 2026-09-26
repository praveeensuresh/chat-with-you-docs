# ADR-0008: Grounding by prompt rule, not by score

**Date**: 2026-09-27
**Status**: accepted
**Deciders**: Praveen, AI assistant

## Context

The headline promise of this project is the Grounded answer: if the Documents do not hold
the answer, the tool says so instead of guessing. Something must enforce that.

Two places can enforce it. Before the Claude call, by refusing when the best Chunk's
similarity score is too low. Or inside the Claude call, by instructing the model to answer
only from the Chunks it was given. A cosine score from `e5-base` has no natural line
between "related" and "not related" — any threshold chosen today would be a guess, and a
wrong guess makes the tool refuse questions it could have answered.

There is also a separate, certain case: when the search returns no Chunks at all, the
outcome is already known before any model is asked.

## Decision

Enforce grounding with the prompt rule. Claude is given the numbered Chunks and told to
answer only from them, and to reply with the exact marker `NOT_IN_DOCUMENTS` when they do
not hold the answer. That marker sets the Answer's `found` flag to false and is replaced
with friendly wording before anyone sees it.

No score cut-off in this phase. When the search returns zero Chunks, return the refusal
directly without calling Claude.

## Alternatives Considered

### Alternative 1: A similarity score cut-off before the Claude call
- **Pros**: cheaper — no model call for weak matches; deterministic.
- **Cons**: the threshold is a guess with no evidence behind it; too high and good
  questions are refused, too low and it does nothing.
- **Why not**: the eval script exists to measure exactly this. Adding the cut-off after
  measurement gives a defensible number and an honest story.

### Alternative 2: Ask Claude for JSON with a `found` field
- **Pros**: a structured signal instead of string matching.
- **Cons**: a parser plus a new failure mode (malformed JSON) for one extra bit of
  information.
- **Why not**: one exact marker carries the same bit with no parsing.

### Alternative 3: Infer the refusal from the wording, or from an empty Citation list
- **Pros**: no marker convention to maintain.
- **Cons**: an Answer that cites nothing is not the same as a refusal, and guessing from
  wording is unreliable.
- **Why not**: this is the guessing the whole decision is meant to remove.

## Consequences

### Positive
- No invented threshold anywhere in the system.
- A refusal is a normal result with a plain flag on it, easy to score in the eval script.
- The zero-Chunk short-circuit removes a model call whose outcome is already certain.

### Negative
- Weak-but-non-empty matches still cost a Claude call before being refused.
- Grounding now depends on the model following an instruction, which is not a guarantee.

### Risks
- The model ignores the marker rule and answers from its own knowledge. Mitigated by the
  Citation rules in ADR-0009 — an answer with no Citations is visible as such — and by the
  eval script, which measures refusals directly.
- The marker text leaks to a person. Mitigated by replacing it before the Answer is
  returned, with a test that asserts the marker never appears in the returned text.
