# .ngnb Notebook Schema (v0.1) — spec

Top-level JSON:
{
  "schema_version": "ngnb-0.1",
  "metadata": {
    "created_at": "...",
    "author": "...",
    "kernel": "python3.10",
    "default_dtype": "pandas",
    "session_settings": {
      "timeout": 20,
      "resource_limits": {"memory":"512m","cpu_quota":50000}
    }
  },
  "cells": [
    {
      "id": "<uuid>",
      "type": "python" | "sql" | "markdown" | "ui",
      "source": "string",
      "meta": { ... }  // cell-type dependent metadata
    }
  ]
}

Cell type metadata:
- python:
  meta: { "tags": ["test"], "timeout": 20 }
- sql:
  meta: {
    "connection": "duckdb:///data.db" | "postgres://user:pass@host/db",
    "result": "var_name",       # variable to bind in session
    "dtype": "pandas" | "polars",
    "explain": false
  }
- ui:
  meta: {
    "widget": "slider" | "select" | "table" | "chat",
    "bind": "var_name",
    "props": { "min": 0, "max": 100, "step": 1 }
  }

Execution semantics:
- SQL cell: executed separately and result (DataFrame) is bound to session variable named `result`.
- Python cell: executed in the same session where SQL-bound variables are available via name lookup.
- UI cell: renders widgets in UI; bindings are two-way. Widget changes can trigger a re-run of dependent cells.

RAG / Chat Indexing:
- Notebook may include "index" instructions in metadata to send outputs/documents to vector DBs (chroma/lancedb) for retrieval during chat.

Persistence:
- Notebooks stored as .ngnb JSON. Converters available to convert to annotated .py scripts for CI and production.
