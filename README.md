# Chat With Your Docs

Ask questions about your own PDF documents and get answers that come only from those documents.

This repo builds the backend pipeline first: load a PDF, break it into chunks, store it in Qdrant, and retrieve the right chunks for any question. The command line lets you test the whole pipeline before a web UI is added.

---

## How it works

1. You give it a PDF file.
2. It reads the PDF page by page and cuts each page into small pieces called chunks (about 800 characters each).
3. It turns each chunk into a list of numbers (an embedding) using the `e5-base` model.
4. It stores those numbers in Qdrant (a vector database).
5. When you ask a question, it turns the question into numbers the same way and finds the closest chunks.
6. It prints each matching chunk with the document name, page number, and text.

---

## Setup

### 1. Copy the environment file

```bash
cp backend/.env.example backend/.env
```

Open `backend/.env` and fill in your values:

```
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
QDRANT_COLLECTION=documents
EMBEDDING_MODEL=intfloat/e5-base
ANTHROPIC_API_KEY=
```

For local development, leave `QDRANT_URL` as `http://localhost:6333` and `QDRANT_API_KEY` empty.

### 2. Start Qdrant

```bash
docker compose up -d
```

This starts a local Qdrant server on port 6333.

### 3. Install backend dependencies

```bash
cd backend
uv sync
```

---

## CLI commands

All commands run from inside the `backend/` folder.

---

### `ingest` — Load a PDF into the store

```
uv run python -m app.cli ingest <path-to-pdf>
```

This reads the PDF, splits it into chunks, embeds each chunk, and stores everything in Qdrant.

**Example:**

```bash
uv run python -m app.cli ingest ~/documents/machine-learning-paper.pdf
```

**Output:**

```
Stored 42 chunks from 'machine-learning-paper.pdf'
```

**What it tells you:**

- `42` is the number of chunks that were stored.
- `machine-learning-paper.pdf` is the document name used in search results and citations.

**Error cases:**

```bash
uv run python -m app.cli ingest /tmp/missing.pdf
# File not found: /tmp/missing.pdf

uv run python -m app.cli ingest notes.txt
# Not a PDF file: notes.txt
```

---

### `search` — Ask a question

```
uv run python -m app.cli search "<your question>" [--top-k N]
```

This turns your question into an embedding and finds the closest chunks in the store.

**Example:**

```bash
uv run python -m app.cli search "What is gradient descent?"
```

**Output:**

```
[machine-learning-paper.pdf, page 3] Gradient descent is an optimization algorithm used to minimize a loss function by moving in the direction of the steepest descent...
[machine-learning-paper.pdf, page 7] In practice, stochastic gradient descent (SGD) processes one random sample at a time, which is much faster than computing the full gradient...
[machine-learning-paper.pdf, page 12] The learning rate controls how large each step is during gradient descent. A rate that is too high causes the algorithm to overshoot...
[machine-learning-paper.pdf, page 4] Variants of gradient descent include momentum, RMSProp, and Adam, each designed to speed up convergence...
[machine-learning-paper.pdf, page 9] Batch gradient descent computes the gradient over the entire dataset before taking a step, which is accurate but slow on large datasets...
```

Each line shows: `[document name, page number]` followed by the chunk text.

**Control how many results come back with `--top-k`:**

```bash
uv run python -m app.cli search "What is gradient descent?" --top-k 3
```

**Output:**

```
[machine-learning-paper.pdf, page 3] Gradient descent is an optimization algorithm...
[machine-learning-paper.pdf, page 7] In practice, stochastic gradient descent (SGD)...
[machine-learning-paper.pdf, page 12] The learning rate controls how large each step is...
```

`--top-k` defaults to 5. Set it to any number — if fewer chunks exist than your `--top-k`, all of them are returned.

**When nothing matches:**

```bash
uv run python -m app.cli search "What is the weather like?"
# No results found.
```

---

### `reset` — Wipe the store

```
uv run python -m app.cli reset
```

This deletes all stored chunks from Qdrant and recreates the collection empty. Useful when you want to start fresh.

**Example:**

```bash
uv run python -m app.cli reset
```

**Output:**

```
Store cleared.
```

After a reset, a search returns no results:

```bash
uv run python -m app.cli search "anything"
# No results found.
```

---

## Re-ingesting a file

You can run `ingest` on the same file more than once. The old chunks are deleted first and then the new ones are written. You will never get duplicate results.

```bash
uv run python -m app.cli ingest ~/documents/report.pdf
# Stored 30 chunks from 'report.pdf'

# Edit the PDF, then re-ingest:
uv run python -m app.cli ingest ~/documents/report.pdf
# Stored 25 chunks from 'report.pdf'
```

The chunk count changed because the edited PDF was shorter. The old 30 chunks are gone.

---

## Running the tests

```bash
cd backend
uv run pytest
```

All tests run fast with no model download or live Qdrant server — they use in-memory fakes.

---

## Project layout

```
backend/
  app/
    cli.py              # Typer CLI (ingest / search / reset)
    config.py           # Settings read from .env
    pipeline/
      ingest.py         # ingest() front door: PDF -> chunks -> store
      search.py         # search() front door: question -> hits
      adapters.py       # Real e5-base embedder + real Qdrant store
      seams.py          # Protocols (Embedder, VectorStore) and data types
      fakes.py          # In-memory fakes used in tests
  tests/
    test_ingest.py
    test_search.py
    test_adapters.py
    test_cli.py
    test_fakes.py
frontend/               # Next.js UI (coming later)
docker-compose.yml      # Runs Qdrant locally
```

---

## Diagrams and decisions

Open these in a browser to see the system as a picture:

- [Architecture](docs/diagrams/architecture.html) — the parts and how they connect.
- [Data flow](docs/diagrams/dataflow.html) — a PDF's path from file to stored Chunk, and a question's path to its Hits.

The written record lives beside them:

- [`CONTEXT.md`](CONTEXT.md) — what each word in this project means.
- [`docs/adr/`](docs/adr/README.md) — every decision, why it was made, and what was rejected.
