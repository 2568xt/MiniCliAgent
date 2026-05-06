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

1. 更快  
   创建虚拟环境和安装依赖通常比传统 `venv + pip` 更快。

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

## 架构说明

项目结构遵循 `dev_spec.md` 中定义的分层：

- `minicliagent/cli`：命令行入口
- `minicliagent/app`：负责组装运行时依赖的应用服务
- `minicliagent/core`：runtime、tools、skills、tasks、team、worktree 等核心领域逻辑
- `minicliagent/infra`：文件系统、shell、日志等基础设施适配层

## 当前可用命令

```bash
python -m minicliagent.cli.main run --prompt "hello"
python -m minicliagent.cli.main run
python -m minicliagent.cli.main tasks create --subject "demo" --description "test"
python -m minicliagent.cli.main tasks update --task-id 1 --status completed
python -m minicliagent.cli.main tasks list
python -m minicliagent.cli.main skills list
python -m minicliagent.cli.main skills load --name demo
python -m minicliagent.cli.main team send --from lead --to worker --content "hello"
python -m minicliagent.cli.main team inbox --name worker
python -m minicliagent.cli.main worktree list
```

说明：

- `run --prompt "..."`：执行单轮请求；未指定 `--session` 时，会按启动时间生成会话名，例如 `20260504-013245`，同秒撞名时追加 `-2`
- `run`：直接进入交互模式，同一次启动内复用同一个自动会话名，输入 `quit` 或 `exit` 退出
- `run --session <name>`：继续写入指定会话

## 测试

运行默认测试套件：

```bash
pytest tests/unit tests/integration -q
```

只在你明确要访问真实模型接口时，再运行可选的 live smoke test：

```bash
RUN_ANTHROPIC_SMOKE=1 pytest tests/integration/test_anthropic_smoke.py -v
```

详细测试报告：

- `docs/testing/2026-04-25-industrial-test-report.md`

学习路径：

- `docs/getting-started/learning-path.md`
- `docs/getting-started/mini-demo.ipynb`
- `docs/getting-started/engineering-demo.ipynb`
- `docs/getting-started/coding-demo.ipynb`

## 文档地图

如果你是第一次进入这个项目，建议按下面顺序阅读：

1. `README.md`  
   先了解项目定位、基础命令和测试方式。

2. `dev_spec.md`  
   了解项目的正式规格，包括目标、边界、分层和运行时结构图。

3. `code_spec.md`  
   查看当前代码已经实现到什么程度。

4. `docs/getting-started/learning-path.md`  
   按学习路径实际跑一遍项目，建立对主链路的直觉。

5. `docs/getting-started/mini-demo.ipynb`  
   用 notebook 方式分步骤体验最小 demo，更适合展示和教学。

6. `docs/getting-started/engineering-demo.ipynb`  
   用 notebook 方式体验 `task + worktree + team` 这条更工程化的链路。

7. `docs/getting-started/coding-demo.ipynb`  
   用 notebook 方式体验一个最小的 `read -> edit -> verify` 编码闭环。

8. `docs/testing/2026-04-25-industrial-test-report.md`  
   查看这个项目目前已经被验证过哪些能力，以及真实测试中发现过哪些问题。

## 仓库结构

旧的教程型代码仓库被保留在 `examples/learn-claude-code/` 里，作为参考实现。当前正式项目代码位于 `minicliagent/`。
