# Spec: "Chat With Your Docs" — Flagship AI Engineer Portfolio Project

Owner: Praveen | Status: draft, ready to build (month 1 of the [portfolio plan](../tickets/004-portfolio-plan.md))
Research basis: [Ticket 001 skill-gap map](001-skill-gap-map.md), last30days research 2026-08-05
(saved to `~/Documents/Last30Days/best-free-open-source-stack-chat-with-your-documents-rag-agent-2026-raw-v3.md`)
Verification pass: 2026-08-08 (free-tier/pricing/memory claims re-checked against current sources;
see corrections folded into §3 and §4 below).

> **Parts of this plan were overtaken by later decisions.** Read the ADRs in
> `docs/adr/` as the live record. Specifically: the backend deploy home is
> Hugging Face Spaces, not Render or Streamlit Cloud (ADR-0006); the frontend is
> Next.js, not Streamlit (ADR-0001); the answer step uses LangGraph, not a plain
> chain (ADR-0007); and the embedding-host question, left open in §4, is settled
> (ADR-0006). The rest of this plan still stands.

## 1. What this project is

Upload your own documents (PDF, txt, markdown, docx). Chat with them. The agent answers
**only from what's in the documents** — no hallucinating, no making things up — and shows
which document/chunk it pulled the answer from (citations). This is your flagship proof
that you can build real LLM/agent systems, not just call an API.

## 2. Why this exact project (ELI5)

- It's broad enough that any hiring manager instantly gets what it does — no domain
  explaining needed.
- It proves the exact skills the market is asking for right now (see Ticket 001): real
  retrieval (RAG), not just prompt-stuffing; grounding/anti-hallucination; a live demo.
- The last30days research (Aug 2026) found real builders' actual stacks and a live
  community debate on how to keep RAG answers grounded — both feed directly into this
  spec's design choices below.

## 3. Requirements

### Must-have (this is what "done" means — no shortcuts)

1. **Upload documents** — PDF at minimum (txt/markdown nice-to-have, not required for v1).
2. **Real retrieval, not prompt-stuffing** — documents get chunked, embedded, stored in a
   vector database, and retrieved by relevance per question (not the whole PDF crammed
   into every prompt).
3. **Chat interface** — ask a question, get an answer, see a running conversation.
4. **Citations** — every answer shows which document/chunk it came from.
5. **Grounded answers** — if the docs don't contain the answer, the agent says so instead
   of guessing. This is the single most-discussed RAG problem in this month's research
   (31-comment [r/LangChain](https://reddit.com/r/LangChain) thread) — solving it well is
   a direct signal to hiring managers.
6. **Live deploy** — a URL anyone can open and try, not "clone and run locally."
7. **Public GitHub repo** with a real README (what it does, why, how it's built, a
   screenshot or short demo clip).
8. **Basic eval script** — 10-20 test questions with expected answers, scored automatically.
   This month's research ranks it the single strongest "actually built with LLMs" signal, and
   real builders (e.g. the `simplysandeepp/Noloop` project) ship it as a core layer, not a bonus.
   It is cheap to add — do not skip it.

### Nice-to-have (add if time allows, not blocking "done")

- Multiple file formats (docx, markdown, plain text).
- Simple usage/cost tracking shown in the UI.
  (The eval script was promoted to must-have #8 — it is the top hiring signal, not optional.)

## 4. Recommended stack (free / open-source first, per this month's research)

| Layer | Pick | Why |
|---|---|---|
| LLM | Claude API (low-cost, pay-as-you-go) | You already know this from harness engineering + Project 1. No free tier exists — new accounts get a ~$5 one-time starter credit, then it's usage-based (Sonnet ~$2/$10 per 1M tokens). A doc-chat demo is tiny token volume, so dev + demo runs a few dollars. Use prompt caching (up to 90% off) on the retrieved-context prompts. |
| Embeddings | `intfloat/e5-base` (sentence-transformers, free, self-hosted) | Confirmed in-use in a real production RAG pipeline found in this month's research. No API cost. **Memory caveat:** e5-base + torch needs ~0.5–1GB RAM just to load, so it will OOM on a 512MB backend (Render free tier). Pick one: co-locate it on Streamlit Cloud (690MB–2.7GB RAM), swap to `all-MiniLM-L6-v2` (~90MB), or use a hosted embedding endpoint so torch never loads on the server. Decide this in Week 1 — it sets your deploy topology. |
| Vector DB | **Qdrant** (free, self-hostable, generous free cloud tier) or **pgvector** (Postgres extension, free) | Both are what real builders are actually using right now, per this month's research. Qdrant is easier to start with (managed free tier); pgvector is the choice if you want everything in one database. |
| Agent/orchestration | **LangGraph** | Most-discussed framework in this month's research for exactly this kind of agent; large community, lots of examples. For a single retrieval agent, a plain retrieve→prompt→answer chain is enough for v1 — LangGraph earns its keep once you add branching or tool loops. If Week 2 runs tight, ship the chain first and document the choice in the README (good engineering-judgment signal). |
| Backend | **FastAPI** (Python) | Standard pairing with LangGraph; free, well-documented. |
| Frontend | Simple Next.js or Streamlit chat UI | Streamlit = faster to build (good for v1); Next.js = looks more "product-grade" if you have the time. |
| Deployment (backend) | **Render** free tier or **Hugging Face Spaces** | Railway dropped its permanent free tier — it now requires a credit card and gives only ~$1/mo credit (unusable for always-on), so avoid it. Render's free tier still works but has 512MB RAM and spins down after 15 min idle (cold starts). Simplest path: skip a separate backend and run everything (UI + embeddings + API) on Streamlit Cloud. |
| Deployment (frontend) | **Vercel** free tier (if Next.js) or bundle with Streamlit Cloud (free) | Free, zero-config for these frameworks. |
| Vector DB hosting | **Qdrant Cloud free tier** (1GB cluster, ~1M vectors @ 768d, no credit card — confirmed Aug 2026) | No self-hosting/server-maintenance needed for v1. Note: free clusters suspend after 1 week idle and are deleted after 4 weeks idle, so open your demo occasionally to keep it warm. |

**Total cost to build and run this: effectively $0**, aside from small Claude API usage during development
and demo (a few dollars at most — the API is pay-as-you-go, not free, but doc-chat token volume is tiny).

## 5. What "impresses a hiring manager" here (from this month's research + Ticket 001)

- **Grounding, not just answering** — showing you solved "don't hallucinate" is a stronger
  signal than the chat feature itself.
- **Citations** — proves you understand *why* retrieval matters, not just that you called
  an LLM.
- **A live demo link** — the single most-repeated finding across all research so far:
  nothing you build counts as proof until a stranger can click it and try it.
- **A real README explaining the "why"** — not just install instructions. What was hard?
  What did you choose and why (e.g. "chose Qdrant over pgvector because...")? This shows
  engineering judgment, not just tutorial-following.

## 6. Suggested build order (fits "1 month, build + deploy" from Ticket 004)

1. Week 1: PDF upload + chunking + embeddings + Qdrant storage. Get retrieval working from
   the command line before touching any UI. **Also decide your embedding-hosting approach now**
   (see the Embeddings memory caveat in §4) — it dictates your Week-3 deploy topology.
2. Week 2: Wire up LangGraph agent + Claude API + citations. Basic grounding (answer only
   from retrieved chunks).
3. Week 3: Chat UI (Streamlit for speed) + deploy backend and frontend.
4. Week 4: Polish — README, screenshot/demo clip, basic eval script if time allows, fix
   rough edges from actually using it yourself.

## 7. Out of scope for v1

Multi-tenant support, user accounts/auth, fine-tuning, multi-agent orchestration beyond a
single retrieval agent, support for non-PDF formats. These can become the *next* project
in the sequence (per Ticket 004's plan — agent-framework project, evals project).
