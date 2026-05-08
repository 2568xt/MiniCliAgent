from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from minicliagent.app.skill_service import SkillService
from minicliagent.app.task_service import TaskService
from minicliagent.app.team_service import TeamService
from minicliagent.app.worktree_service import WorktreeService
from minicliagent.core.config.settings import Settings
from minicliagent.core.llm.anthropic_provider import AnthropicProvider
from minicliagent.core.llm.types import TextDeltaCallback
from minicliagent.core.memory.dense import Mem0DenseMemoryIndex, UnavailableDenseMemoryIndex
from minicliagent.core.memory.service import MemoryService, ProviderMemorySummarizer
from minicliagent.core.memory.store import MarkdownMemoryStore
from minicliagent.core.mcp import MCPService
from minicliagent.core.runtime.agent_runtime import AgentRuntime
from minicliagent.core.runtime.background_manager import BackgroundManager
from minicliagent.core.runtime.event_bus import EventBus
from minicliagent.core.runtime.message_store import FileMessageStore
from minicliagent.core.skills.loader import SkillLoader
from minicliagent.core.skills.matcher import SkillMatcher
from minicliagent.core.team.bus import MessageBus
from minicliagent.core.tasks.board import TaskBoard
from minicliagent.core.tools.builtins.background import background_check_tool, background_run_tool
from minicliagent.core.tools.builtins.bash import run_bash_command
from minicliagent.core.tools.builtins.files import edit_text_file, read_text_file, write_text_file
from minicliagent.core.tools.builtins.memory import memory_search_tool
from minicliagent.core.tools.builtins.skills import list_skills_tool, load_skill_tool
from minicliagent.core.tools.builtins.tasks import task_create_tool, task_list_tool, task_update_tool
from minicliagent.core.tools.builtins.team import team_inbox_tool, team_send_tool
from minicliagent.core.tools.builtins.worktree import worktree_create_tool, worktree_list_tool
from minicliagent.core.tools.models import ToolSpec
from minicliagent.core.tools.registry import ToolRegistry
from minicliagent.core.worktree.manager import WorktreeManager, detect_repo_root
from minicliagent.infra.logging.setup import JsonLogger, TranscriptRecorder


@dataclass
class AgentService:
    settings: Settings
    runtime: AgentRuntime
    task_service: TaskService
    skill_service: SkillService
    team_bus: MessageBus
    team_service: TeamService
    worktree_service: WorktreeService
    memory_service: MemoryService | None = None

    def run_prompt(self, prompt: str, session_id: str = "default", on_text_delta: TextDeltaCallback | None = None) -> str:
        return self.runtime.run_turn(session_id=session_id, user_input=prompt, on_text_delta=on_text_delta).output_text

    def finalize_session(self, session_id: str) -> None:
        if self.memory_service is None:
            return
        messages = self.runtime.message_store.get(session_id)
        if messages:
            self.memory_service.remember_session(session_id, messages, "exit_hook")


def create_agent_service(env: dict[str, str] | None = None) -> AgentService:
    load_dotenv(override=False)
    merged_env = dict(os.environ)
    if env:
        merged_env.update(env)
    settings = Settings.from_env(merged_env)
    for path in [settings.state_root, settings.sessions_dir, settings.tasks_dir, settings.team_dir, settings.worktrees_dir, settings.logs_dir]:
        path.mkdir(parents=True, exist_ok=True)
    if settings.memory_enabled:
        settings.memory_dir.mkdir(parents=True, exist_ok=True)
        settings.memory_index_dir.mkdir(parents=True, exist_ok=True)

    inbox_dir = settings.team_dir / "inbox"
    skill_loader = SkillLoader([settings.workspace_root / "skills"])
    task_board = TaskBoard(settings.tasks_dir)
    skill_matcher = SkillMatcher(skill_loader)
    event_bus = EventBus(settings.logs_dir / "events.jsonl")
    logger = JsonLogger(settings.logs_dir / "app.jsonl")
    transcript_recorder = TranscriptRecorder(settings.logs_dir / "transcripts")
    background_manager = BackgroundManager(settings.workspace_root, event_bus=event_bus)
    team_bus = MessageBus(inbox_dir)
    repo_root = detect_repo_root(settings.workspace_root)
    worktree_manager = WorktreeManager(repo_root, settings.worktrees_dir, event_bus=event_bus) if repo_root else None
    provider = AnthropicProvider(model=settings.model, base_url=merged_env.get("ANTHROPIC_BASE_URL") or None)

    memory_service = None
    if settings.memory_enabled:
        try:
            dense_index = Mem0DenseMemoryIndex(settings.memory_index_dir)
        except Exception:
            dense_index = UnavailableDenseMemoryIndex()
        memory_service = MemoryService(
            store=MarkdownMemoryStore(settings.memory_summary_path, settings.memory_dir),
            dense_index=dense_index,
            dense_weight=settings.memory_dense_weight,
            bm25_weight=settings.memory_bm25_weight,
            dense_top_k=settings.memory_dense_top_k,
            bm25_top_k=settings.memory_bm25_top_k,
            final_top_k=settings.memory_final_top_k,
            summarizer=ProviderMemorySummarizer(provider, logger=logger),
            logger=logger,
        )

    registry = ToolRegistry()
    team_service, worktree_service = _register_builtin_tools(registry, settings, skill_loader, task_board, background_manager, team_bus, repo_root, worktree_manager, event_bus, logger)
    mcp_service = MCPService(settings.mcp_servers, logger=logger)
    mcp_service.register_tools(registry)
    if memory_service is not None:
        registry.register(ToolSpec(name="memory_search", description="Search long-term memory.", input_schema={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}, handler=lambda query: memory_search_tool(memory_service, query), tags={"builtin", "memory"}))

    runtime = AgentRuntime(provider=provider, tool_registry=registry, system_prompt="You are MiniCLIAgent, a local coding agent.", message_store=FileMessageStore(settings.sessions_dir), background_manager=background_manager, event_bus=event_bus, logger=logger, transcript_recorder=transcript_recorder)
    task_service = TaskService(board=task_board)
    skill_service = SkillService(loader=skill_loader, matcher=skill_matcher, max_skill_chars=4000)
    return AgentService(settings=settings, runtime=runtime, task_service=task_service, skill_service=skill_service, team_bus=team_bus, team_service=team_service, worktree_service=worktree_service, memory_service=memory_service)


def _register_builtin_tools(registry, settings, skill_loader, task_board, background_manager, team_bus, repo_root, worktree_manager, event_bus, logger):
    registry.register(ToolSpec(name="bash", description="Run a shell command inside the workspace.", input_schema={"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}, handler=lambda command: run_bash_command(settings.workspace_root, command), tags={"builtin", "shell"}))
    registry.register(ToolSpec(name="read_file", description="Read a UTF-8 text file from the workspace.", input_schema={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}, handler=lambda path: read_text_file(settings.workspace_root, path), tags={"builtin", "fs"}))
    registry.register(ToolSpec(name="write_file", description="Write a UTF-8 text file inside the workspace.", input_schema={"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}, handler=lambda path, content: write_text_file(settings.workspace_root, path, content), tags={"builtin", "fs"}))
    registry.register(ToolSpec(name="edit_file", description="Replace the first matching text block in a workspace file.", input_schema={"type": "object", "properties": {"path": {"type": "string"}, "old_text": {"type": "string"}, "new_text": {"type": "string"}, "replace_all": {"type": "boolean"}}, "required": ["path", "old_text", "new_text"]}, handler=lambda path, old_text, new_text, replace_all=False: edit_text_file(settings.workspace_root, path, old_text, new_text, replace_all), tags={"builtin", "fs"}))
    registry.register(ToolSpec(name="list_skills", description="List available local skills.", input_schema={"type": "object", "properties": {}}, handler=lambda: list_skills_tool(skill_loader), tags={"builtin", "skills"}))
    registry.register(ToolSpec(name="load_skill", description="Load a local skill by name.", input_schema={"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}, handler=lambda name: _load_skill_with_events(name, skill_loader, event_bus, logger), tags={"builtin", "skills"}))
    registry.register(ToolSpec(name="task_create", description="Create a persistent task.", input_schema={"type": "object", "properties": {"subject": {"type": "string"}, "description": {"type": "string"}}, "required": ["subject", "description"]}, handler=lambda subject, description: task_create_tool(task_board, subject, description), tags={"builtin", "tasks"}))
    registry.register(ToolSpec(name="task_list", description="List persistent tasks.", input_schema={"type": "object", "properties": {}}, handler=lambda: task_list_tool(task_board), tags={"builtin", "tasks"}))
    registry.register(ToolSpec(name="task_update", description="Update task status or owner.", input_schema={"type": "object", "properties": {"task_id": {"type": "integer"}, "status": {"type": "string"}, "owner": {"type": "string"}}, "required": ["task_id"]}, handler=lambda task_id, status=None, owner=None: task_update_tool(task_board, task_id, status=status, owner=owner), tags={"builtin", "tasks"}))
    registry.register(ToolSpec(name="background_run", description="Run a shell command in the background.", input_schema={"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}, handler=lambda command: background_run_tool(background_manager, command), tags={"builtin", "background"}))
    registry.register(ToolSpec(name="background_check", description="Check one background task or list all background tasks.", input_schema={"type": "object", "properties": {"task_id": {"type": "string"}}}, handler=lambda task_id=None: background_check_tool(background_manager, task_id), tags={"builtin", "background"}))
    team_service = TeamService(bus=team_bus)
    registry.register(ToolSpec(name="team_send", description="Send a team message.", input_schema={"type": "object", "properties": {"sender": {"type": "string"}, "recipient": {"type": "string"}, "content": {"type": "string"}}, "required": ["sender", "recipient", "content"]}, handler=lambda sender, recipient, content: team_send_tool(team_service, sender, recipient, content), tags={"builtin", "team"}))
    registry.register(ToolSpec(name="team_inbox", description="Read a teammate inbox.", input_schema={"type": "object", "properties": {"recipient": {"type": "string"}}, "required": ["recipient"]}, handler=lambda recipient: team_inbox_tool(team_service, recipient), tags={"builtin", "team"}))
    if worktree_manager is not None:
        worktree_service = WorktreeService(manager=worktree_manager, task_board=task_board)
        registry.register(ToolSpec(name="worktree_create", description="Create a git worktree.", input_schema={"type": "object", "properties": {"name": {"type": "string"}, "branch": {"type": "string"}, "task_id": {"type": "integer"}}, "required": ["name", "branch"]}, handler=lambda name, branch, task_id=None: worktree_create_tool(worktree_service, name, branch, task_id), tags={"builtin", "worktree"}))
        registry.register(ToolSpec(name="worktree_list", description="List git worktrees managed by MiniCLIAgent.", input_schema={"type": "object", "properties": {}}, handler=lambda: worktree_list_tool(worktree_service), tags={"builtin", "worktree"}))
    else:
        worktree_service = WorktreeService(manager=None)  # type: ignore[arg-type]
    return team_service, worktree_service


def _load_skill_with_events(name, skill_loader, event_bus, logger):
    result = load_skill_tool(skill_loader, name)
    if not result.is_error:
        event_bus.emit("skill_loaded", {"name": name})
        logger.log("info", "skill_loaded", skill=name)
    return result
