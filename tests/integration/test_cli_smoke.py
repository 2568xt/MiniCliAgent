from minicliagent.cli.main import build_parser


def test_cli_parser_accepts_prompt_argument() -> None:
    parser = build_parser()
    args = parser.parse_args(["run", "--prompt", "hello"])

    assert args.command == "run"
    assert args.prompt == "hello"
    assert args.session is None


def test_cli_parser_accepts_explicit_session_argument() -> None:
    parser = build_parser()
    args = parser.parse_args(["run", "--prompt", "hello", "--session", "s1"])

    assert args.command == "run"
    assert args.prompt == "hello"
    assert args.session == "s1"


def test_cli_parser_allows_run_without_prompt() -> None:
    parser = build_parser()
    args = parser.parse_args(["run", "--session", "s1"])

    assert args.command == "run"
    assert args.prompt is None
    assert args.session == "s1"
