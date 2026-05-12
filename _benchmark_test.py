#!/usr/bin/env python3
"""Benchmark test for MiniCLIAgent fixes.

Run: uv run python _benchmark_test.py
"""
import sys, os, json, subprocess, time
from pathlib import Path

FIXTURE_ROOT = Path("tests/fixtures")

import urllib.request
url = "https://gitee.com/htxoffical/pico/raw/main/benchmarks/coding_tasks.json"
with urllib.request.urlopen(url, timeout=15) as r:
    benchmark = json.loads(r.read())

PROMPT_BASE = """You are a coding agent. Complete the following task.
- Use edit_file for text edits, NOT bash.
- Use read_file first to see the exact current content.
- IMPORTANT: After edit_file, the tool will verify the change was applied automatically.
- If you receive a 'Verification failed' or 'is_error=True' result, you MUST re-read the file and retry.
- Do NOT say DONE until the file content has been verified changed."""

def restore_fixtures(fixture_name):
    fix_path = FIXTURE_ROOT / fixture_name
    sample = fix_path / "sample.txt"
    readme = fix_path / "README.md"
    if sample.exists():
        sample.write_text("Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n")
    if readme.exists():
        readme.write_text("# Benchmark Fixture\n\nThis is the benchmark fixture.\n")

def get_expected(task, expected_key):
    for a in task.get("assertions", []):
        if a.get("field", "").endswith(expected_key):
            return a.get("expected", "")
    return ""

TASK_MAP = {
    "readme_intro_locked": ("bench_repo_readme", "README.md", "intro"),
    "readme_schema_note": ("bench_repo_readme", "README.md", "note"),
    "sample_beta_locked": ("bench_repo_patch", "sample.txt", "beta"),
    "sample_gamma_locked": ("bench_repo_patch", "sample.txt", "gamma"),
}

all_results = []

for task_id, (fixture_name, file_rel, exp_key) in TASK_MAP.items():
    task = next((t for t in benchmark["tasks"] if t["id"] == task_id), None)
    fix_path = FIXTURE_ROOT / fixture_name
    file_path = fix_path / file_rel
    expected = get_expected(task, exp_key) if task else ""
    workspace_str = str(fix_path)

    restore_fixtures(fixture_name)

    task_desc = task.get("description", "") if task else ""

    full_prompt = f"""{PROMPT_BASE}

Task description:
{task_desc}

Target file: {file_rel}
Working directory: {workspace_str}"""

    env = dict(os.environ)
    env["MINICLIAGENT_WORKSPACE"] = workspace_str

    start = time.time()
    try:
        proc = subprocess.run(
            ["uv", "run", "python", "-m", "minicliagent.cli.main",
             "run", "--prompt", full_prompt],
            capture_output=True, text=True, timeout=60,
            env=env, cwd=workspace_str
        )
        elapsed = time.time() - start
        stdout = proc.stdout[-5000:] if proc.stdout else ""
        stderr = proc.stderr[-500:] if proc.stderr else ""
    except subprocess.TimeoutExpired:
        elapsed = 60
        stdout = "[TIMEOUT]"
        stderr = ""

    actual = file_path.read_text() if file_path.exists() else "[no file]"
    passed = expected in actual

    result = {
        "task_id": task_id,
        "fixture": fixture_name,
        "file": file_rel,
        "passed": passed,
        "elapsed_s": round(elapsed, 1),
        "expected": expected,
        "actual_preview": actual[:200],
        "stdout": stdout,
        "stderr": stderr,
    }
    all_results.append(result)

    status = "PASS" if passed else "FAIL"
    print(f"\n{'='*60}")
    print(f"[{status}] {task_id} ({elapsed:.1f}s)")
    print(f"  Expected: {expected!r}")
    print(f"  Actual:   {actual[:120]!r}")

    if "[TOOL ERROR" in stdout or "is_error=True" in stdout:
        print(f"  [FIX 4] Recovery hint was injected")
    if "File not found" in stdout and not passed:
        print(f"  [FIX 2] 'File not found' error shown to agent")
    if "Text not found" in stdout and not passed:
        print(f"  [FIX 2] 'Text not found' with hint shown to agent")
    if "Edited" in stdout or "edited" in stdout:
        edit_lines = [l.strip() for l in stdout.splitlines() if "Edited" in l or "edited" in l]
        if edit_lines:
            print(f"  [EDIT] {edit_lines[0][:100]}")
    if passed:
        print(f"  [FIX] VERIFIED - change in file!")
    elif elapsed < 5 and not any(x in stdout for x in ["Edited", "edited", "File not found", "Text not found", "is_error"]):
        print(f"  [POSSIBLE HALLUCINATION] Quick completion, no edit attempted")
    if stderr:
        print(f"  stderr: {stderr[:200]!r}")

print(f"\n\n{'='*60}")
print("SUMMARY:")
for r in all_results:
    status = "PASS" if r["passed"] else "FAIL"
    print(f"  [{status}] {r['task_id']} ({r['elapsed_s']}s): expected={r['expected']!r}")
