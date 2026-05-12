# MiniCLIAgent

一个面向学习与工程实践的本地 CLI Agent 项目。

## 快速开始

```bash
uv venv .venv
source .venv/bin/activate
UV_CACHE_DIR=.uv-cache uv pip install -e .
pytest tests/unit tests/integration -v
python -m minicliagent.cli.main run --help
```

## 为什么推荐 uv

`uv` 是一个现代 Python 工具，常用来管理虚拟环境和安装依赖。对这个项目来说，推荐它主要有三个原因：

the benchmark schema and baseline are fixed.

2. 更统一  
   你可以用一套命令处理环境和依赖，不用来回切换不同工具。

3. 更适合教学演示  
   对学习者来说，`uv venv` 和 `uv pip install` 这两步比较直观，命令也更集中。

如果你之前只用过 `python -m venv` 和 `pip`，可以把 `uv` 理解成一个更顺手、更快的替代方案。这个项目仍然是标准 Python 项目，所以核心结构并不会因为使用 `uv` 而改变。

## 环境变量

基于 `.env.example` 创建 `.env`，并至少配置以下变量：

- `ANTHROPIC_API_KEY`
- `ANTHROPIC_BASE_URL`（如果你使用兼容网关）
- `MINICLIAGENT_MODEL`
- `MINICLIAGENT_WORKSPACE`



## 当前可用命令

```bash
python -m minicliagent.cli.main run --prompt "hello"
python -m minicliagent.cli.main run
python -m minicliagent.cli.main skills list

说明：

- `run --prompt "..."`：执行单轮请求；未指定 `--session` 时，会按启动时间生成会话名，例如 `20260504-013245`，同秒撞名时追加 `-2`
- `run`：直接进入交互模式，同一次启动内复用同一个自动会话名，输入 `quit` 或 `exit` 退出
- `run --session <name>`：继续写入指定会话
