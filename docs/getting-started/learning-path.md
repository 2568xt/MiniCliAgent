# MiniCLIAgent 学习路径

这份文档不是完整手册，而是一条更适合初学者的上手路线。

如果你第一次接触 agent 工程，最容易犯的错是一下子读太多代码、加太多功能，最后反而不知道这个项目的主线是什么。更好的方法是：先跑起来，看到状态落盘，再回头读代码。

这个项目最值得先理解的，不是某个单独模块，而是下面这条链路：

`CLI -> AgentService -> AgentRuntime -> Provider + Tools -> 本地状态`

只要你先把这条链路跑通，后面的 `skill / task / background / team / worktree` 都会容易很多。

## 一、5 分钟上手

先只做三件事：

```bash
uv venv .venv
source .venv/bin/activate
UV_CACHE_DIR=.uv-cache uv pip install -e .
python -m minicliagent.cli.main --help
pytest tests/unit tests/integration -q
python -m minicliagent.cli.main run --prompt "Reply with OK only."
```

你应该看到：

- CLI 帮助正常输出
- 默认测试通过
- agent 能完成一次最小对话

如果这三步都通了，说明这个项目的基础链路已经是健康的。

如果你更喜欢“边点边看”的展示方式，可以直接打开：

- `docs/getting-started/mini-demo.ipynb`
- `docs/getting-started/engineering-demo.ipynb`
- `docs/getting-started/coding-demo.ipynb`

这两份 notebook 分别负责：

- `mini-demo.ipynb`：最小主链路体验
- `engineering-demo.ipynb`：`task + worktree + team` 工程化链路体验
- `coding-demo.ipynb`：最小 `read -> edit -> verify` 编码闭环体验

## 二、第一轮体验顺序

建议你按下面顺序体验，不要跳。

### 1. 先看 CLI 长什么样

```bash
python -m minicliagent.cli.main --help
```

这一步的目标不是记命令，而是先知道项目有哪些能力面：

- `run`
- `tasks`
- `skills`
- `team`
- `worktree`

### 2. 跑一次最小对话

```bash
python -m minicliagent.cli.main run --prompt "Reply with OK only."
```

这一步只验证一件事：模型链路是否可用。

如果这一步失败，不要急着看 task 或 worktree，先把 `.env` 和 provider 连通性解决掉。

如果你更喜欢交互方式，也可以直接运行：

```bash
python -m minicliagent.cli.main run
```

进入交互模式后，输入 `quit` 或 `exit` 退出。

### 3. 看看项目怎么落状态

先创建一个 task：

```bash
python -m minicliagent.cli.main tasks create --subject "demo" --description "learn task board"
python -m minicliagent.cli.main tasks list
```

然后去看这些目录：

- `.minicliagent/tasks/`
- `.minicliagent/sessions/`
- `.minicliagent/logs/`

这一步很重要，因为它能帮你建立一个工程化直觉：

这个项目不是把一切都藏在内存里，而是把关键状态落到了本地，便于调试、复盘和学习。

### 4. 让 agent 真正调一次工具

```bash
python -m minicliagent.cli.main run --prompt "Read README.md and tell me the project name."
```

你可以把这一步理解成第一次真正看到 agent 在“读文件而不是胡猜”。

重点观察两件事：

1. 最终输出是不是和文件内容一致
2. `.minicliagent/sessions/` 里有没有把对话过程存下来

### 5. 再体验工程化能力

先试最轻的两组：

```bash
python -m minicliagent.cli.main skills list
python -m minicliagent.cli.main team send --from lead --to worker --content "hello"
python -m minicliagent.cli.main team inbox --name worker
```

如果当前工作区本身是 git repo，再继续试：

```bash
python -m minicliagent.cli.main worktree list
python -m minicliagent.cli.main worktree create --name demo --branch wt/demo
```

## 三、推荐阅读顺序

不建议一开始按目录从上往下扫。更适合学习的顺序是：

1. `README.md`
2. `dev_spec.md`
3. `code_spec.md`
4. `docs/testing/2026-04-25-industrial-test-report.md`
5. `minicliagent/cli/main.py`
6. `minicliagent/app/agent_service.py`
7. `minicliagent/core/runtime/agent_runtime.py`
8. `minicliagent/core/runtime/context_manager.py`
9. `minicliagent/core/tools/builtins/`

读到这里，你已经能理解主干了。之后再去看：

- `core/tasks/`
- `core/skills/`
- `core/team/`
- `core/worktree/`

这样不会一开始就陷进太多细节。

## 四、第一次读代码时看什么

### `cli/main.py`

看命令是怎么进来的，参数怎么分发。

### `app/agent_service.py`

看项目是怎么把 runtime、provider、tool registry、task board、skill loader 这些东西装起来的。

### `core/runtime/agent_runtime.py`

看 agent loop 的最核心闭环：

- 读 session
- 准备上下文
- 发请求给 provider
- 执行 tool
- 写回消息和 transcript

### `core/tools/builtins/`

看“能力”是怎么被注册进去的。这个目录最适合用来理解工具式 agent 的设计。

## 五、常见坑

### 1. `MINICLIAGENT_WORKSPACE` 没切对

如果你在临时目录里测试，一定要显式设置：

```bash
export MINICLIAGENT_WORKSPACE=/path/to/your/workspace
```

否则你以为 agent 在操作测试目录，实际上可能还在默认工作区里运行。

### 2. 非 git 工作区不能创建 worktree

`worktree` 功能要求当前 workspace 本身是 git repo。

现在 CLI 已经会返回可读错误，不再直接抛 traceback，但你还是要知道这是能力前提，不是 bug。

### 3. skill 不会自动出现

本地 skill 来自：

```text
<workspace>/skills/**/SKILL.md
```

如果 `skills list` 为空，先检查目录结构，而不是先怀疑 runtime。

### 4. 最小对话成功，不代表多步工具链一定正常

`run --prompt "Reply with OK only."` 只说明 provider 基础链路通了。

真正能体现 agent 工程质量的，是这些场景：

- 文件读取与编辑
- task 创建与更新
- background task
- worktree 绑定

## 六、第一次动手改什么最合适

第一次不要改 runtime 主循环，也不要直接扩 provider 抽象。

更合适的练手点是：

- 修改 CLI help 文案
- 给 task list 增加一点展示信息
- 给 skill loader 增加一条失败测试
- 给 README 或学习文档补一个小例子

这些改动足够小，但能完整练到一轮工程动作：

1. 读现有实现
2. 写或补测试
3. 改代码
4. 跑验证
5. 回看文档

## 七、建议的学习方式

最有效的方式不是只读代码，而是这个顺序：

1. 先跑命令
2. 再看落盘状态
3. 再读对应代码
4. 最后做一个很小的改动

如果你能完成这四步，这个项目对你来说就不只是“看过”，而是真正走过一遍 agent 工程的最小闭环了。
