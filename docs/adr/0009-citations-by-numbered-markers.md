# ADR-0009: Citations by numbered markers

**Date**: 2026-09-27
**Status**: accepted
**Deciders**: Praveen, AI assistant

## Context

Every Answer must show its proof: which Document, which page, and the exact text it came
from. The retrieved Chunks are known on our side, so the only open question is how the
Answer points at the ones it actually used.

Returning every retrieved Chunk shows what was searched, not what was used — a reader
cannot tell the two apart, which defeats the purpose. Asking the model for structured
output per claim gives finer proof but adds parsing and a new failure mode.

There is also a safety question. Whatever the model writes must never become the source of
a page number, or it could invent one.

## Decision

Number the Chunks from 1 in the prompt, each shown with its Document name and page, and
instruct Claude to mark its statements with those numbers. Build the Citations on our side
by mapping the markers back to the Hits that were sent.

Rules that close the gaps:

- A marker that does not match a Chunk that was sent is dropped.
- An Answer with no markers is returned unchanged, with an empty Citation list and `found`
  true.
- A Citation is an existing Hit — Document name, page, text, score — not a new type.

## Alternatives Considered

### Alternative 1: Return every retrieved Chunk as the Citations
- **Pros**: no marker convention, nothing to parse.
- **Cons**: shows what was searched, not what was used; a correct-looking Citation list can
  sit under a wrong answer.
- **Why not**: it cannot prove grounding, which is the entire point.

### Alternative 2: Ask for JSON with a Citation attached to each claim
- **Pros**: the finest proof — per sentence rather than per answer.
- **Cons**: a parser, malformed-output handling, and a longer, more fragile prompt.
- **Why not**: more detail than this phase needs, and more failure modes than it can pay
  for.

### Alternative 3: A new Citation type separate from Hit
- **Pros**: names the concept in code.
- **Cons**: a fourth near-identical view of the same facts, after ChunkPayload,
  SearchResult and Hit.
- **Why not**: a Citation is exactly a Hit that was used. Same facts, same type.

## Consequences

### Positive
- The Citations are the Chunks the model really used, so the proof means something.
- Page numbers can never be invented — they are read from our own Hits, never from the
  model's text.
- No new data type; the shape stays as small as it was.

### Negative
- The marker convention must be explained in the prompt, and the model may not always obey
  it.
- The Answer text carries visible markers such as `[1]`, which the web layer will later
  have to render.

### Risks
- The model marks a Chunk it did not really use, producing a plausible but wrong Citation.
  Mitigated by printing the cited Chunk text beside the Answer, so a person can check, and
  by the eval script's page check later.
- Markers in an unexpected format go unread, silently emptying the Citation list. Mitigated
  by a test for the no-marker case, which keeps the Answer and flags the absence.
