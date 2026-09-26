<!-- Published as GitHub issue #6: https://github.com/praveeensuresh/chat-with-you-docs/issues/6 -->

# Spec: Grounded answer with Citations (CLI chat)

Phase 2, Week 2. Backend only, proven from the command line. This sits on top of the
ingestion and retrieval pipeline (GitHub issue #2) and is the base the web chat page
will later reuse without a rewrite.

Uses the glossary in `CONTEXT.md` (Document, Chunk, Citation, Grounded answer, Answer,
Turn) and follows ADR-0004 (pipeline), ADR-0005 (deep modules and test seams),
ADR-0007 through ADR-0011 (the decisions made for this phase).

## Problem Statement

A person can already load a Document and find the Chunks that match a question, but the
command line only prints raw Chunks. The person must read the pieces and work out the
answer themselves. There is no Answer, no wording, and no way to tell "the Documents do
not say" from "nothing matched the words you used". The project's headline promise —
answer only from the Documents, and show the proof — is not yet kept.

## Solution

Add a third front door, `answer(question)`, that turns a question into an Answer: text
written only from the Chunks that were found, the Citations it used, and a plain signal
of whether the Documents held the answer at all.

- The Chunks found for the question are numbered and given to Claude with their Document
  name and page.
- Claude writes the answer and marks each statement with the number of the Chunk it came
  from. Those numbers become the Citations.
- If the Chunks do not hold the answer, Claude says so with a fixed marker, and the
  Answer comes back with `found` false and a friendly sentence.
- A `chat` command keeps the recent Turns, so a follow-up question like "what about the
  second one?" is understood before the search runs.

The real work lives behind the one front door. The command line is a thin wrapper, so the
later web page and the eval script reuse the same function.

## User Stories

1. As a developer, I want to ask a question from the command line and get an Answer in
   plain words, so that I can see the whole pipeline work end to end.
2. As a developer, I want the Answer to be built only from the Chunks that were found, so
   that the tool cannot invent facts.
3. As a developer, I want the Answer to carry the Citations it used, so that I can check
   every statement against the Document.
4. As a developer, I want each Citation to name the Document and the page, so that I can
   open the source and read it myself.
5. As a developer, I want each Citation to carry the Chunk text, so that I can judge the
   Answer without opening the Document at all.
6. As a developer, I want Claude to mark its statements with Chunk numbers, so that the
   Citations are the Chunks it really used, not everything that was searched.
7. As a developer, I want a marker that points at a Chunk that was never given to be
   dropped, so that an invented Citation can never reach the person.
8. As a developer, I want an Answer with no markers at all to still come back, with an
   empty Citation list, so that the eval script can later score "answered without proof"
   as its own kind of failure.
9. As a developer, I want the tool to say it cannot find the answer when the Chunks do not
   hold it, so that the Grounded answer promise is kept.
10. As a developer, I want a refusal to be a normal result and not an error, so that the
    caller does not have to treat a correct outcome as a breakage.
11. As a developer, I want a plain `found` signal on the Answer, so that a refusal is told
    apart from an Answer that simply cited nothing.
12. As a developer, I want the internal refusal marker replaced before it is shown, so
    that a person never sees machinery in the wording.
13. As a developer, I want a question asked against an empty store to return "not found"
    without calling Claude, so that no money is spent on an outcome that is already known.
14. As a developer, I want each Chunk in the prompt to show its Document name and page, so
    that Claude can answer questions about where something came from.
15. As a developer, I want five Chunks used by default, and the number changeable, so that
    the eval script can later tune it with evidence.
16. As a developer, I want a `chat` command that keeps a session open, so that I can ask
    several questions without starting again.
17. As a person using `chat`, I want to ask a follow-up question in normal words, so that I
    do not have to repeat the whole question every time.
18. As a developer, I want a follow-up rewritten into a standalone question before the
    search runs, so that the search is not given words that mean nothing on their own.
19. As a developer, I want the rewrite step skipped when there is no history, so that the
    first question of a session does not pay for a Claude call that does nothing.
20. As a developer, I want only the recent Turns carried, so that a long conversation does
    not grow the prompt without limit.
21. As a developer, I want the history to hold only the question and the answer text, so
    that the rewrite prompt stays small and free of noise.
22. As a developer, I want each printed Citation trimmed to a readable length, so that the
    screen stays usable while still showing the proof.
23. As a developer, I want the tokens used by each turn printed, so that I learn what this
    system really costs.
24. As a developer, I want a ceiling on the answer length, so that one reply cannot run
    away with my money.
25. As a developer, I want a failed Claude call to fail loudly, so that a bad API key is
    never disguised as "your Documents do not say".
26. As a developer, I want the `chat` session to stay open after an error, so that one bad
    call does not end my work.
27. As a developer, I want the model set in one place, so that changing it is one edit.
28. As a developer, I want to swap in a fake Claude during tests, so that tests run fast,
    free, and offline.
29. As a developer, I want to script the fake's replies, so that I can test a refusal, a
    bad marker and a missing marker on demand — cases the real Claude cannot be made to
    produce reliably.
30. As a developer, I want to see the prompt the fake was given, so that I can prove the
    Chunks were numbered and the history was passed, without calling Claude.
31. As a maintainer, I want the answer path behind one front door, so that the web page and
    the eval script reuse it with no new logic.
32. As a maintainer, I want a passing test suite over the answer path, so that later
    changes are safe.

## Implementation Decisions

### Modules

- **Answer core** — a third front door, `answer`, beside `ingest` and `search`. It takes
  the question, the recent Turns, the three seams and a result count, and returns an
  Answer. Hides: the search call, prompt building, the Claude call, marker parsing,
  Citation building, and the follow-up rewrite. The embedder and the store are pass-through
  arguments — `answer` only hands them to `search`. That is deliberate: bundling them
  behind one slot would create a seam with a single filler, which ADR-0005 forbids.
  The Answer is a plain dataclass; no LangGraph state object or Anthropic type is ever
  returned, so no caller gains a dependency on either.
- **LLM adapter** — the real Claude adapter, added beside the existing embedder and store
  adapters.
- **LLM fake** — an in-memory fake with scripted replies that records the prompts it was
  given, added beside the existing fakes.
- **Command line** — a new `chat` command, a thin wrapper that holds the Turns and prints.

### Decisions this phase rests on

Each rule below has exactly one home — the ADR named beside it. This plan states which
decisions apply, not what they say, so that tuning a rule while building changes one file.

- The answer path is a LangGraph graph held inside the front door; nothing outside knows
  the graph exists — ADR-0007.
- Grounding is enforced by the prompt rule with a fixed refusal marker, and there is no
  score cut-off in this phase — ADR-0008.
- Citations come from numbered markers and are built on our side, so a page can never be
  invented; a Citation is an existing Hit, not a new type — ADR-0009.
- Follow-ups are handled by rewriting the question, and only when history exists — ADR-0010.
- One model for both calls, failures raise, and a token ceiling plus per-turn counts keep
  cost visible — ADR-0011.
- All of this stays in the existing pipeline package: one place for slots, one place for
  fakes, one place for real adapters — ADR-0011.

### Command line

`chat` opens a session: read a question, print the Answer, print each Citation as Document
name, page and the Chunk text trimmed to about 200 characters, then print the tokens used
for that turn. The loop keeps the Turns in memory and ends on `exit`.

### Configuration

Two new settings: `answer_model` and `answer_max_tokens`. The existing `anthropic_api_key`
is already present and becomes required to run the answer path.

### Dependencies

Nothing new to install. `anthropic` and `langgraph` were already declared and installed
during Phase 1 setup, together with `langchain-core`.

`langgraph` is used for the graph only. The Claude call goes through the LLM seam and the
`anthropic` client directly, never through a LangChain model wrapper — vendor types must
not leak past the slot (ADR-0011). `langchain-anthropic` is currently declared but unused;
it is that wrapper, so it is removed as part of this phase rather than left as a tempting
shortcut past the decision.

The installed `anthropic` client predates the model id this phase names, so confirming
that `answer_model` is accepted is part of the first real call in ticket 1.

## Testing Decisions

A good test here checks what a caller observes at the front door: the Answer's text,
Citations, `found` flag and token counts, plus what the fake Claude was asked. It must not
call graph nodes directly, and it must not reach into the Anthropic client. Node-level
tests would pin the tests to the graph's current shape, so that adding a node later breaks
tests even though nothing a user sees has changed.

There is exactly one test surface: `answer()`, with the fake embedder, fake store and fake
Claude injected. This matches the surface set in Week 1, where `ingest()` and `search()`
are tested the same way.

Prior art: the existing pipeline tests — they inject the fakes, assert on returned values,
and assert on the calls the fakes recorded.

Test cases:

- A question with matching Chunks returns an Answer whose text is the fake's reply and
  whose Citations are only the Chunks whose numbers were marked.
- The refusal marker returns `found` false, an empty Citation list, and friendly wording
  with no marker text in it.
- A marker pointing at a Chunk that was never given is dropped.
- A reply with no markers returns `found` true with an empty Citation list.
- An empty store returns `found` false and the fake Claude is never called.
- A first question (no history) does not run the rewrite step.
- A follow-up question runs the rewrite step, and the prompt the fake received contains the
  earlier Turns.
- The search runs on the rewritten question, not the raw follow-up.
- Only the last 6 Turns reach the rewrite prompt.
- The numbered Chunks in the prompt carry their Document name and page. Prompt assertions
  check that the prompt *contains* the expected facts, never its exact wording, so that
  improving the prompt does not break tests while behaviour is unchanged.
- `top_k` is honoured when passed.
- Token counts from the reply appear on the Answer.
- A Claude failure is raised, not swallowed.

The real Claude adapter is unit tested the same way Week 1 tests its real adapters: patch
the Anthropic client and assert the adapter sends the configured model and token ceiling,
and reads the reply text and the token counts from the right fields. No network, no cost.
That catches the mapping bugs a fake cannot, which is exactly why `test_adapters.py` exists
for the embedder and the store. End to end against a real Document stays part of ticket 1
as well, because only a real call proves the model id is accepted.

## Out of Scope

- The eval script — 10 to 20 scored questions (spec must-have #8). Its own phase, with its
  own scoring decision.
- A score cut-off before the Claude call. Deferred until the eval script shows it is needed.
- The web chat page and the HTTP endpoint. Later phase; both will call `answer()`.
- Retries and rate-limit handling on the Claude call.
- A per-session spend cap.
- Streaming the Answer token by token.
- Prompt caching.
- Non-PDF Documents, auth, and multi-user work.

## Further Notes

- The fast tests prove the plumbing: numbering, markers, refusal, history, token counts.
  They do not prove answer quality, because the fake Claude returns scripted text. Quality
  is the eval script's job.
- LangGraph was chosen partly as a learning goal, against the lighter plain-function
  option. ADR-0007 records that honestly, together with the two conditional edges that the
  graph genuinely earns.
- Work order is sliced so the first ticket reaches the real Claude on day one; grounding
  edge cases are hardened in the second. Nothing ships to anyone in between.
