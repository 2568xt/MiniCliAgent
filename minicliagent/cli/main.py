from __future__ import annotations

import argparse
import inspect
import sys
from datetime import datetime
from pathlib import Path
from typing import TextIO

from minicliagent.app.agent_service import create_agent_service


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="minicliagent",
        description="A small local CLI agent for learning agent engineering patterns.",
        epilog=(
            "Examples:\n"
            "  minicliagent run --prompt \"read README.md\"\n"
            "  minicliagent skills list\n"
            "  minicliagent tasks create --subject \"demo\" --description \"test\"\n"
            "  minicliagent worktree list"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Send one prompt or start an interactive session.")
    run_parser.add_argument("--prompt")
    run_parser.add_argument("--session")

    tasks_parser = subparsers.add_parser("tasks", help="Manage persistent tasks.")
    tasks_subparsers = tasks_parser.add_subparsers(dest="tasks_command", required=True)
    task_create = tasks_subparsers.add_parser("create", help="Create a task.")
    task_create.add_argument("--subject", required=True)
    task_create.add_argument("--description", default="")
    task_update = tasks_subparsers.add_parser("update", help="Update task status or owner.")
    task_update.add_argument("--task-id", type=int, required=True)
    task_update.add_argument("--status")
    task_update.add_argument("--owner")
    tasks_subparsers.add_parser("list", help="List tasks.")

    skills_parser = subparsers.add_parser("skills", help="Inspect local skills.")
    skills_subparsers = skills_parser.add_subparsers(dest="skills_command", required=True)
    skills_subparsers.add_parser("list", help="List available skills.")
    skill_load = skills_subparsers.add_parser("load", help="Load one skill body.")
    skill_load.add_argument("--name", required=True)

    team_parser = subparsers.add_parser("team", help="Send or read teammate messages.")
    team_subparsers = team_parser.add_subparsers(dest="team_command", required=True)
    team_send = team_subparsers.add_parser("send", help="Send one teammate message.")
    team_send.add_argument("--from", dest="sender", required=True)
    team_send.add_argument("--to", dest="recipient", required=True)
    team_send.add_argument("--content", required=True)
    team_inbox = team_subparsers.add_parser("inbox", help="Read one inbox.")
    team_inbox.add_argument("--name", required=True)

    worktree_parser = subparsers.add_parser("worktree", help="Manage git worktrees.")
    worktree_subparsers = worktree_parser.add_subparsers(dest="worktree_command", required=True)
    worktree_create = worktree_subparsers.add_parser("create", help="Create a worktree.")
    worktree_create.add_argument("--name", required=True)
    worktree_create.add_argument("--branch", required=True)
    worktree_create.add_argument("--task-id", type=int)
    worktree_subparsers.add_parser("list", help="List managed worktrees.")
    return parser


def main(
    argv: list[str] | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        service = create_agent_service()
        if args.command == "run":
            session_id = args.session or _generate_session_id(service.settings.sessions_dir)
            if args.session is None:
                print(f"Session: {session_id}", file=stdout)
            if args.prompt is not None:
                _handle_run_prompt(service, args.prompt, session_id, stdout)
            else:
                try:
                    while True:
                        try:
                            prompt = input("> ").strip()
                        except EOFError:
                            break
                        if not prompt:
                            continue
                        if prompt in {"exit", "quit"}:
                            break
                        _handle_run_prompt(service, prompt, session_id, stdout)
                finally:
                    finalize_session = getattr(service, "finalize_session", None)
                    if finalize_session is not None:
                        finalize_session(session_id)
        elif args.command == "tasks":
            if args.tasks_command == "create":
                task = service.task_service.create_task(args.subject, args.description)
                print(f"#{task.id} {task.subject}", file=stdout)
            elif args.tasks_command == "update":
                task = service.task_service.update_task(
                    args.task_id,
                    status=args.status,
                    owner=args.owner,
                )
                print(f"#{task.id} {task.subject} [{task.status}]", file=stdout)
            elif args.tasks_command == "list":
                for task in service.task_service.list_tasks():
                    print(f"#{task.id} {task.subject}", file=stdout)
        elif args.command == "skills":
            if args.skills_command == "list":
                for skill in service.skill_service.list_skills():
                    print(skill.name, file=stdout)
            elif args.skills_command == "load":
                skill = service.skill_service.load_skill(args.name)
                print(skill.body, file=stdout)
        elif args.command == "team":
            if args.team_command == "send":
                service.team_service.send_message(args.sender, args.recipient, args.content)
                print("sent", file=stdout)
            elif args.team_command == "inbox":
                for message in service.team_service.read_inbox(args.name):
                    print(f"{message.sender}: {message.content}", file=stdout)
        elif args.command == "worktree":
            if args.worktree_command == "create":
                record = service.worktree_service.create(args.name, args.branch, task_id=args.task_id)
                print(record.name, file=stdout)
            elif args.worktree_command == "list":
                for record in service.worktree_service.list_all():
                    print(f"{record.name} [{record.status}]", file=stdout)
        return 0
    except KeyError as exc:
        print(f"Error: Unknown skill '{exc.args[0]}'.", file=stderr)
        return 1
    except FileNotFoundError:
        print("Error: Task not found.", file=stderr)
        return 1
    except RuntimeError as exc:
        if "Worktree manager unavailable" in str(exc):
            print("Error: Worktree is unavailable in the current workspace.", file=stderr)
            return 1
        raise

def _handle_run_prompt(service, prompt: str, session_id: str, stdout: TextIO) -> None:
    streamed = False

    def on_text_delta(text: str) -> None:
        nonlocal streamed
        if not text:
            return
        streamed = True
        stdout.write(text)
        stdout.flush()

    output = _invoke_run_prompt(service, prompt, session_id, on_text_delta=on_text_delta)
    if streamed:
        stdout.write("\n")
        stdout.flush()
        return
    if output:
        print(output, file=stdout)


def _generate_session_id(sessions_dir: Path) -> str:
    sessions_dir.mkdir(parents=True, exist_ok=True)
    base = datetime.now().strftime("%Y%m%d-%H%M%S")
    suffix = 1

    while True:
        session_id = base if suffix == 1 else f"{base}-{suffix}"
        try:
            with (sessions_dir / f"{session_id}.json").open("x", encoding="utf-8") as handle:
                handle.write("[]")
            return session_id
        except FileExistsError:
            suffix += 1


def _invoke_run_prompt(service, prompt: str, session_id: str, on_text_delta) -> str:
    run_prompt = service.run_prompt
    try:
        signature = inspect.signature(run_prompt)
    except (TypeError, ValueError):
        signature = None

    if signature is not None and "on_text_delta" not in signature.parameters:
        return run_prompt(prompt, session_id=session_id)

    return run_prompt(prompt, session_id=session_id, on_text_delta=on_text_delta)


if __name__ == "__main__":
    raise SystemExit(main())
