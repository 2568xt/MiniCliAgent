# Streaming Output Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `minicliagent run` print assistant text incrementally as model text blocks arrive instead of waiting for the full turn to finish.

**Architecture:** Add an optional streaming callback from the Anthropic provider into the runtime turn loop, keep the existing aggregated `ModelResponse` contract for storage and tool execution, and wire the CLI to flush stdout on each text fragment while preserving one-shot behavior for non-streaming callers.

**Tech Stack:** Python, Anthropic SDK, argparse CLI, existing runtime/tool loop, pytest

---

### Task 1: Add runtime and CLI streaming tests

**Files:**
- Modify: `tests/unit/test_agent_service.py`
- Modify: `tests/integration/test_agent_runtime_loop.py`
- Modify: `tests/integration/test_cli_smoke.py`

- [ ] **Step 1: Write a failing runtime test for callback delivery**

```python
fragments: list[str] = []
result = runtime.run_turn("s1", "hello", on_text_delta=fragments.append)
assert fragments == ["hel", "lo"]
assert result.output_text == "hello"
```

- [ ] **Step 2: Run runtime-focused tests to verify failure**

Run: `pytest tests/integration/test_agent_runtime_loop.py tests/unit/test_agent_service.py -q`
Expected: FAIL because `run_turn()` and `run_prompt()` do not accept a streaming callback yet.

- [ ] **Step 3: Write a failing CLI test for incremental stdout writes**

```python
stream = io.StringIO()
exit_code = cli_main.main(["run", "--prompt", "hello"], stdout=stream)
assert stream.getvalue() == "hel\nlo\n"
```

Use a fake service/provider that emits two text fragments before returning the full response.

- [ ] **Step 4: Run CLI-focused tests to verify failure**

Run: `pytest tests/integration/test_cli_smoke.py -q`
Expected: FAIL because `main()` does not accept injected stdout and still prints only after the turn completes.

### Task 2: Implement provider and runtime streaming

**Files:**
- Modify: `minicliagent/core/llm/base.py`
- Modify: `minicliagent/core/llm/types.py`
- Modify: `minicliagent/core/llm/anthropic_provider.py`
- Modify: `minicliagent/core/runtime/agent_runtime.py`
- Modify: `minicliagent/app/agent_service.py`

- [ ] **Step 1: Add an optional text-delta callback type to the LLM layer**
- [ ] **Step 2: Teach `AnthropicProvider` to use the SDK streaming API when a callback is supplied**
- [ ] **Step 3: Keep collecting full text and tool calls so the runtime contract stays unchanged**
- [ ] **Step 4: Thread the callback through `AgentRuntime.run_turn()` and `AgentService.run_prompt()`**
- [ ] **Step 5: Re-run the focused runtime tests**

Run: `pytest tests/integration/test_agent_runtime_loop.py tests/unit/test_agent_service.py -q`
Expected: PASS

### Task 3: Implement CLI flushing behavior

**Files:**
- Modify: `minicliagent/cli/main.py`
- Modify: `tests/integration/test_cli_smoke.py`

- [ ] **Step 1: Let `main()` accept injectable `stdout`/`stderr` streams for tests**
- [ ] **Step 2: Pass a flushing callback into `run_prompt()` for the `run` command**
- [ ] **Step 3: Print a trailing newline only when at least one fragment streamed**
- [ ] **Step 4: Preserve old behavior for non-streaming commands**
- [ ] **Step 5: Re-run CLI tests**

Run: `pytest tests/integration/test_cli_smoke.py tests/integration/test_cli_error_handling.py -q`
Expected: PASS

### Task 4: Final verification

**Files:**
- No code changes expected

- [ ] **Step 1: Run the focused regression suite**

Run: `pytest tests/integration/test_agent_runtime_loop.py tests/integration/test_cli_smoke.py tests/integration/test_cli_error_handling.py tests/unit/test_agent_service.py tests/unit/test_anthropic_provider.py -q`
Expected: PASS

- [ ] **Step 2: Manually inspect the streaming code paths**

Review:
- `minicliagent/core/llm/anthropic_provider.py`
- `minicliagent/core/runtime/agent_runtime.py`
- `minicliagent/cli/main.py`

- [ ] **Step 3: Report the new behavior and any remaining limits**

Limits to mention:
- Tool-result output remains turn-based; only assistant text blocks stream.
- Non-CLI callers still receive the final aggregated string through `run_prompt()`.
