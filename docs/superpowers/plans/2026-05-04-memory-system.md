# Memory System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add local, Markdown-first long-term memory with agent-controlled hybrid search and automatic compact/exit hooks.

**Architecture:** `core/memory/` owns storage, BM25, hybrid ranking, optional mem0 dense indexing, and summarization. `app/agent_service.py` wires memory into runtime and `ToolRegistry`; `AgentRuntime` only calls the service boundary. Markdown remains the source of truth under `.minicliagent/`, while dense index state under `.minicliagent/memory_index/` is rebuildable.

**Tech Stack:** Python 3.11, pytest, optional `mem0ai`, existing Anthropic-compatible `ModelRequest`/`ModelResponse`, existing `ToolRegistry`.

---

### Task 1: Settings And Markdown Store

**Files:**
- Modify: `minicliagent/core/config/settings.py`
- Create: `minicliagent/core/memory/__init__.py`
- Create: `minicliagent/core/memory/models.py`
- Create: `minicliagent/core/memory/store.py`
- Modify: `tests/unit/test_settings.py`
- Create: `tests/unit/test_memory_store.py`

- [ ] **Step 1: Write failing settings and store tests**

Add assertions that `Settings.from_env()` exposes `memory_enabled`, memory paths, top-k values, and weights. Add store tests proving `append_entries()` writes `.minicliagent/memory.md`, writes one fragment file, skips empty entries, and `read_documents()` returns searchable memory documents.

Run: `pytest tests/unit/test_settings.py tests/unit/test_memory_store.py -q`
Expected: FAIL because memory fields and store modules do not exist.

- [ ] **Step 2: Implement settings and store**

Add fields to `Settings`: `memory_enabled`, `memory_summary_path`, `memory_dir`, `memory_index_dir`, `memory_dense_weight`, `memory_bm25_weight`, `memory_dense_top_k`, `memory_bm25_top_k`, `memory_final_top_k`. Create `MemoryEntry`, `MemoryDocument`, and `MemoryAppendResult` dataclasses. Implement `MarkdownMemoryStore.append_entries()` and `MarkdownMemoryStore.read_documents()`.

- [ ] **Step 3: Verify Task 1**

Run: `pytest tests/unit/test_settings.py tests/unit/test_memory_store.py -q`
Expected: PASS.

### Task 2: BM25 And Hybrid Ranker

**Files:**
- Create: `minicliagent/core/memory/bm25.py`
- Create: `minicliagent/core/memory/ranker.py`
- Create: `tests/unit/test_memory_bm25.py`
- Create: `tests/unit/test_memory_ranker.py`

- [ ] **Step 1: Write failing retrieval tests**

Add BM25 tests for exact token hits, empty corpus, and top-k. Add hybrid ranker tests for dense/BM25 de-duplication, min-max normalization, equal-score normalization to `1`, missing-side score `0`, formula `0.3 * bm25 + 0.7 * dense`, and final top 6.

Run: `pytest tests/unit/test_memory_bm25.py tests/unit/test_memory_ranker.py -q`
Expected: FAIL because the retrieval modules do not exist.

- [ ] **Step 2: Implement retrieval**

Implement a small local BM25 scorer with deterministic tokenization and no third-party dependency. Implement `fuse_memory_results()` using query-local normalization and the configured weights/top-k.

- [ ] **Step 3: Verify Task 2**

Run: `pytest tests/unit/test_memory_bm25.py tests/unit/test_memory_ranker.py -q`
Expected: PASS.

### Task 3: Memory Service, Optional mem0 Adapter, And Tool

**Files:**
- Create: `minicliagent/core/memory/dense.py`
- Create: `minicliagent/core/memory/service.py`
- Create: `minicliagent/core/tools/builtins/memory.py`
- Modify: `minicliagent/app/agent_service.py`
- Modify: `pyproject.toml`
- Modify: `tests/unit/test_agent_service.py`
- Create: `tests/unit/test_memory_service.py`
- Create: `tests/unit/test_memory_tools.py`

- [ ] **Step 1: Write failing service/tool tests**

Add tests proving `MemoryService.search()` combines dense and BM25 results, degrades when dense is unavailable, returns formatted tool output, and `create_agent_service()` registers `memory_search` when memory is enabled. Add a disabled regression proving the tool is absent and memory directories are not required when `MINICLIAGENT_MEMORY_ENABLED=0`.

Run: `pytest tests/unit/test_memory_service.py tests/unit/test_memory_tools.py tests/unit/test_agent_service.py -q`
Expected: FAIL because the service, tool, and wiring do not exist.

- [ ] **Step 2: Implement service/tool wiring**

Implement `UnavailableDenseMemoryIndex` and `Mem0DenseMemoryIndex` with optional import of `mem0.Memory`; failures return no dense results. Implement `MemoryService.search()` and `MemoryService.remember_session()`. Register `memory_search` in `create_agent_service()` and add `memory_service` to `AgentService`. Add an optional dependency group `memory = ["mem0ai>=0.1.0"]` in `pyproject.toml`.

- [ ] **Step 3: Verify Task 3**

Run: `pytest tests/unit/test_memory_service.py tests/unit/test_memory_tools.py tests/unit/test_agent_service.py -q`
Expected: PASS.

### Task 4: Runtime And CLI Hooks

**Files:**
- Modify: `minicliagent/core/runtime/context_manager.py`
- Modify: `minicliagent/core/runtime/agent_runtime.py`
- Modify: `minicliagent/app/agent_service.py`
- Modify: `minicliagent/cli/main.py`
- Create: `tests/integration/test_runtime_memory_hooks.py`
- Modify: `tests/integration/test_cli_run_command.py`

- [ ] **Step 1: Write failing hook tests**

Add runtime tests proving compacted history triggers `memory_service.remember_session(session_id, messages, "compact_hook")` once per compacted message count and that the system prompt includes a memory-search hint when memory is enabled. Add CLI tests proving interactive `quit` calls `service.finalize_session(session_id)` and one-shot `run --prompt` does not call the exit hook.

Run: `pytest tests/integration/test_runtime_memory_hooks.py tests/integration/test_cli_run_command.py -q`
Expected: FAIL because hooks do not exist.

- [ ] **Step 2: Implement hooks**

Have `ContextManager.prepare_messages()` expose whether history compaction occurred. Add optional `memory_service` to `AgentRuntime`; append a concise system prompt hint when present; call `remember_session()` for compact hooks with duplicate suppression. Add `AgentService.finalize_session()`. In CLI interactive mode, finalize on `quit` or EOF if the service supports it.

- [ ] **Step 3: Verify Task 4**

Run: `pytest tests/integration/test_runtime_memory_hooks.py tests/integration/test_cli_run_command.py -q`
Expected: PASS.

### Task 5: Documentation State And Full Verification

**Files:**
- Modify: `code_spec.md`

- [ ] **Step 1: Update implementation checklist**

Mark completed memory-system items in `code_spec.md` while leaving any intentionally deferred items unchecked.

- [ ] **Step 2: Run focused memory suite**

Run: `pytest tests/unit/test_memory_store.py tests/unit/test_memory_bm25.py tests/unit/test_memory_ranker.py tests/unit/test_memory_service.py tests/unit/test_memory_tools.py tests/integration/test_runtime_memory_hooks.py -q`
Expected: PASS.

- [ ] **Step 3: Run broader regression suite**

Run: `pytest tests/unit tests/integration -q`
Expected: PASS, unless pre-existing unrelated failures appear; record any failures with file/test names and do not claim green if they remain.

- [ ] **Step 4: Check diff hygiene**

Run: `git diff --check`
Expected: no output.

---

### Self-Review

Spec coverage:
- Local mem0 OSS is represented by optional `Mem0DenseMemoryIndex`.
- Markdown-first state is represented by `MarkdownMemoryStore`.
- Agent-controlled lookup is represented by `memory_search`.
- Hybrid retrieval top-k, normalization, weights, and top 6 are covered by ranker tests.
- Compact and exit hooks are covered by runtime/CLI tests.
- Dense failure degradation is covered by service tests.

Placeholder scan:
- No task relies on TBD/TODO placeholders.

Type consistency:
- `MemoryService.search()` and `MemoryService.remember_session()` are the public runtime/tool boundary.
- Dense/BM25 results use `MemorySearchHit` and fused results use `HybridMemoryResult`.
