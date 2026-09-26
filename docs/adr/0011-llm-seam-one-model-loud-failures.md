# ADR-0011: An LLM seam with one model and loud failures

**Date**: 2026-09-27
**Status**: accepted
**Deciders**: Praveen, AI assistant

## Context

The answer step calls Claude twice: once to rewrite a follow-up, once to write the Answer.
Unlike the embedder and the store, this talks to somebody else's server, costs money per
call, and cannot be made to produce a chosen reply on demand. Tests need a refusal, a bad
Citation marker and a missing marker — none of which the real model can be asked for
reliably.

ADR-0005 set the rule for seams: build one only when two things will fill it. Here two
things will — the real Claude adapter and a test fake — so the seam is real, not
hypothetical.

Three smaller questions come with it: how many models, what happens when the call fails,
and how spending is kept visible.

## Decision

Add a third seam, an LLM slot with one job: take a prompt, return text and the token
counts. The real adapter calls Claude; the fake returns scripted replies and records every
prompt it was given.

- **One model for both calls**, set once in configuration as `answer_model`, default
  `claude-sonnet-5`.
- **Failures raise.** No retries, no catching. The command-line loop prints the error and
  stays open.
- **A `max_tokens` ceiling** on the answer call, and the token counts from each reply ride
  on the Answer so each turn's cost can be printed.

The real adapter, the fake and the slot live beside the existing ones: slots in the seams
module, fakes in the fakes module, real adapters in the adapters module.

## Alternatives Considered

### Alternative 1: Call the Anthropic client directly and patch it in tests
- **Pros**: one less layer.
- **Cons**: tests depend on patching internals; the interesting cases (refusal, bad marker)
  are hard to trigger; vendor types leak through the code.
- **Why not**: the seam has two real fillers, so ADR-0005 says build it.

### Alternative 2: A cheaper model for the rewrite, a stronger one for the Answer
- **Pros**: saves a small amount per follow-up.
- **Cons**: two settings, two behaviours to reason about, and a weak rewrite poisons the
  search for the whole turn.
- **Why not**: the rewrite prompt is tiny; the saving is cents and the added complexity is
  permanent.

### Alternative 3: Catch failures and return a refusal Answer
- **Pros**: the loop never shows an error.
- **Cons**: a bad API key or a dropped network would look exactly like "your Documents do
  not say" — the most confusing bug this project could ship.
- **Why not**: a failure is not a result. ADR-0008 makes refusals normal precisely so that
  errors can stay errors.

### Alternative 4: Retry failed calls
- **Pros**: survives rate limits and timeouts.
- **Cons**: guessing at a problem not yet met, with one user and a handful of questions.
- **Why not**: the vendor client already retries some cases. Revisit when the eval script
  fires many questions in a row.

## Consequences

### Positive
- Tests run fast, free and offline, and can script the cases that matter most.
- The fake records its prompts, so tests can prove the Chunks were numbered and the history
  was passed without calling Claude.
- One place to change the model; one ceiling protecting against a runaway reply.
- Real cost is visible per turn instead of guessed.

### Negative
- A third slot and a third fake to maintain.
- No resilience to transient API failures; the person retypes the question.

### Risks
- The fake drifts away from the real adapter's behaviour, so tests pass while the real path
  breaks. Mitigated by keeping the slot tiny (prompt in, text and token counts out) and by
  proving the real path by hand in the first ticket of this phase.
