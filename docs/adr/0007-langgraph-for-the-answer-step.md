# ADR-0007: LangGraph for the answer step

**Date**: 2026-09-27
**Status**: accepted
**Deciders**: Praveen, AI assistant

## Context

The answer step turns a question into an Answer: search for Chunks, build a prompt,
call Claude, read the Citations back. The first version of this is a straight line
with no branching. The project spec itself says a plain chain is enough for a single
retrieval agent, and ADR-0005 warns against building a slot that only one thing fills.

Two forces pull the other way. First, follow-up questions add a real branch: a question
with no history goes straight to the search, a question with history must be rewritten
first. Second, LangGraph is a named learning goal for this project — it is the framework
the owner wants hands-on experience with, and this is the safest place to get it.

## Decision

Build the answer step as a LangGraph graph, held inside the `answer()` front door.
Nothing outside the front door knows the graph exists: the command line now, and the web
layer later, call `answer()` only.

## Alternatives Considered

### Alternative 1: A plain function with no framework
- **Pros**: fewer dependencies, less to read, nothing to learn before editing it.
- **Cons**: the two conditional paths become hand-written `if` statements; no picture of
  the flow to show a reader.
- **Why not**: the learning goal is real and stated. The cost is small and contained by
  keeping the graph behind the front door.

### Alternative 2: LangGraph exposed as the public shape
- **Pros**: callers could add their own nodes.
- **Cons**: every caller — the command line, the later web layer, the eval script — would
  depend on LangGraph, and swapping it out would touch all of them.
- **Why not**: breaks ADR-0005's front-door rule. The graph is an implementation detail.

## Consequences

### Positive
- The two conditional edges (rewrite when history exists, refuse when no Chunks were
  found) are visible as a flow rather than buried in branching code.
- Later steps — a score cut-off, a second retrieval pass — are added as nodes without
  reshaping the caller.
- Hands-on LangGraph experience on a small, low-risk surface.

### Negative
- Two new dependencies (`langgraph` and its LangChain core), about 40 small packages.
- More ceremony than the logic strictly needs today.
- A reader must know LangGraph to edit the inside of `answer()`.

### Risks
- The graph grows into the public shape by accident. Mitigated by the rule in this ADR:
  only `answer()` is importable by callers.
- Framework churn in the LangChain family. Mitigated by using only the graph primitives,
  with the Claude call behind our own seam rather than a LangChain model wrapper.
