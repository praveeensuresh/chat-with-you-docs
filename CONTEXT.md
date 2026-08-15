# Chat With Your Docs

A tool where a person uploads their own documents and asks questions about them.
The tool answers only from the uploaded documents and shows where each answer
came from.

## Language

**Document**:
One file a person uploads to ask questions about. PDF for the first version.
_Avoid_: file, doc, upload

**Chunk**:
A small piece of a Document's text that is stored and searched on its own.
Answers are built from Chunks, not from whole Documents.
_Avoid_: segment, fragment

**Citation**:
The proof shown with an answer: which Document, which page, and the exact text
the answer came from.
_Avoid_: source, reference

**Grounded answer**:
An answer built only from the Chunks that were found for the question. If the
Documents do not contain the answer, the tool says so instead of guessing.
_Avoid_: no-hallucination
