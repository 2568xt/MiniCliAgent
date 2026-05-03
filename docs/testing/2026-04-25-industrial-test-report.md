# MiniCLIAgent 工业级测试报告

- 文档日期：2026-04-25
- 项目版本：当前工作区版本
- 测试对象：`minicliagent/`
- 测试类型：单元测试、集成测试、真实模型链路测试、真实用户场景压测
- 测试结论：当前版本已经通过核心自动化测试与多轮真实场景验证，具备进入下一阶段真实编码任务打磨的基础条件

## 1. 测试目标

本轮测试的目标不是只验证模块是否“能跑”，而是验证以下工业级要求是否成立：

1. 核心能力是否有自动化回归保障
2. CLI -> App -> Runtime -> Provider -> Tool 的整条执行链路是否闭环
3. 持久化状态是否与 agent 最终回复一致
4. 在真实模型调用条件下，多步工具编排是否稳定
5. `task / skill / background / team / worktree` 是否能完成跨模块联动

## 2. 测试环境

### 2.1 运行环境

- 工作目录：`/Users/yuanzilin/Minicliagent`
- Shell：`zsh`
- Python：项目当前解释器环境
- 时区：`Asia/Shanghai`
- 模型接入：Anthropic SDK 兼容链路
- 实际验证配置：`.env` 中配置的 `MiniMax-M2.7`

### 2.2 关键环境变量

- `ANTHROPIC_API_KEY`
- `ANTHROPIC_BASE_URL`
- `MINICLIAGENT_MODEL`
- `MINICLIAGENT_WORKSPACE`

说明：

- 当前实现已经修复 `.env` 覆盖 shell 环境变量的问题
- 当前实现已经兼容 `MiniMax` 的 Anthropic 风格 base URL 归一化

## 3. 测试范围

### 3.1 自动化覆盖范围

已纳入自动化测试的模块包括：

- 配置与环境优先级
- Provider 与 tool adapter
- AgentRuntime tool loop
- ContextManager 三层压缩相关行为
- Message store / transcript / event bus / logging
- 文件工具、shell 工具
- skill loader / matcher / service / tools
- task board / service / tools
- background manager / background tools / runtime 通知
- team protocols / message bus / service / tools / teammate manager
- worktree manager / service / CLI
- CLI smoke / CLI 子命令集成

### 3.2 真实链路覆盖范围

已做 live 验证的链路包括：

- `run --prompt` 单轮调用
- `run --prompt` 多轮 session 调用
- 实际模型触发 `read_file / write_file / edit_file`
- 实际模型触发 `list_skills / load_skill`
- 实际模型触发 `task_create / task_update / task_list`
- 实际模型触发 `background_run / background_check`
- 实际模型触发 `team_send / team_inbox`
- 实际模型触发 `worktree_create / worktree_list`

## 4. 自动化测试结果

### 4.1 主测试套件

执行命令：

```bash
pytest tests/unit tests/integration -q
```

执行结果：

```text
71 passed, 1 skipped
```

结论：

- 当前默认自动化测试套件全部通过
- 唯一 skip 项为显式受控的 live smoke test，不属于失败

### 4.2 可选 live smoke test

执行命令：

```bash
RUN_ANTHROPIC_SMOKE=1 pytest tests/integration/test_anthropic_smoke.py -v
```

说明：

- 该用例默认跳过
- 只有在明确允许消耗真实模型额度时才执行
- 本轮测试中，真实模型链路通过 CLI live 场景进行了替代性验证

## 5. 真实用户场景测试结果

以下测试全部在临时工作区中进行，并使用真实 `run --prompt` 驱动模型调工具，不使用 fake provider。

### 5.1 基础能力压测

| 场景 | 输入目标 | 期望结果 | 实际结果 | 结论 |
|---|---|---|---|---|
| 文件读取 | 读取 `notes.txt` 第二行 | 返回精确文本 | `SECOND_LINE` | 通过 |
| 文件写入+编辑 | 创建 `scratch.txt` 并替换内容 | 文件最终为 `alpha/gamma` | 返回 `DONE`，外部核验文件正确 | 通过 |
| skill 调用 | 列出并加载 `demo` skill | 提取部署码 | `SKY-42` | 通过 |
| task 创建 | 创建 `Check parser` 任务 | 返回任务行 | `#1 Check parser [pending]` | 通过 |
| task 更新 | 更新 task 1 为 `in_progress` | 返回更新后结果 | `#1 Check parser [in_progress]` | 通过 |
| background | 后台执行 `echo BG_OK` | 检测完成 | `BG_OK completed` | 通过 |
| team | alice 发信给 bob 并读取 inbox | 返回 inbox 行 | `alice: ship it` | 通过 |
| worktree | 创建 `feat-docs` worktree | 返回对应 worktree 条目 | `feat-docs active` | 通过 |

补充核验：

- `scratch.txt` 外部核验内容为 `alpha|gamma`
- `task_1.json` 外部核验包含 `owner=alice`
- `worktree list` 外部核验输出为 `feat-docs [active]`

### 5.2 复杂组合场景压测

| 场景 | 覆盖能力 | 实际结果 | 结论 |
|---|---|---|---|
| 多轮 session 记忆 | 同一 session 两轮读取同一 spec | 第 1 轮 `Parser Hardening`，第 2 轮 `alice` | 通过 |
| skill + task + edit 联动 | 加载 skill、抽取信息、建 task、改代码 | 返回 `DONE`，`app.py` 被改为 `text.strip().lower()` | 通过 |
| background + team 联动 | 后台任务完成后发 team 消息并读取 inbox | `alice: background finished` | 通过 |
| worktree + task binding | 创建绑定 task 的 worktree 并核验双向状态 | 返回 `feat-lower active`，任务与 worktree 元数据同步 | 通过 |

补充核验：

- `task_1.json` 中 `worktree` 字段已写入 `feat-lower`
- `worktrees/index.json` 中记录了 `task_id: 1`
- `worktree list` 外部核验输出为 `feat-lower [active]`

## 6. 本轮测试中发现并修复的问题

以下问题均来自真实执行，不是静态推断。

### 6.1 环境变量优先级错误

现象：

- `create_agent_service()` 使用 `load_dotenv(override=True)`
- 导致 shell 显式传入的 `MINICLIAGENT_WORKSPACE` 被 `.env` 覆盖
- 真实用户无法通过环境变量切换工作区

修复：

- 改为 `load_dotenv(override=False)`

影响：

- 修复 CLI 在临时工作区、测试工作区和外部调用场景下的可控性

### 6.2 MiniMax Anthropic 兼容地址错误

现象：

- 使用 `ANTHROPIC_BASE_URL=https://api.minimaxi.com/v1` 时，真实请求返回 `404`

修复：

- 在 `AnthropicProvider` 中增加 MiniMax base URL 归一化逻辑
- 统一落到 `https://api.minimaxi.com/anthropic`

影响：

- 修复真实 provider 的基础连通性

### 6.3 Tool loop 协议错误

现象：

- runtime 在工具调用后只持久化 assistant 文本，没有回放 `tool_use` block
- 服务端收到后无法将 `tool_result` 关联到先前的 `tool_use_id`
- 真实请求报错：`tool result's tool id not found`

修复：

- `AgentRuntime` 改为按 Anthropic 兼容格式保存 assistant `tool_use` content block

影响：

- 修复多步工具调用闭环

### 6.4 Working memory 注入位置错误

现象：

- `ContextManager` 通过 `messages[]` 注入 `role=system`
- Anthropic 兼容接口只接受顶层 `system` 字段，不接受消息列表中的 `system`
- 真实请求报错：`invalid chat setting`

修复：

- working memory 改为拼接进顶层 `system prompt`
- 历史压缩摘要不再使用消息级 `system role`

影响：

- 修复带 skill / working memory 的 live 对话链路

### 6.5 Worktree 原生命令输出泄漏

现象：

- `git worktree add` 的 stdout 直接泄漏进最终 agent 回复

修复：

- `WorktreeManager` 的 git 子进程调用改为 `capture_output=True`

影响：

- 清理最终用户可见输出，避免污染 agent 回复

## 7. 当前质量结论

基于本轮自动化结果和 live 场景验证，可以给出如下结论：

### 7.1 已验证成立

- 代码层自动化回归基础盘完整
- CLI 到 provider 的整条主链路可用
- Anthropic 兼容 provider 下的多步工具调用可用
- `task / skill / background / team / worktree` 单点能力可用
- 多轮 session 和记忆注入在当前实现下可用
- 持久化状态与最终回复能够对齐

### 7.2 当前可支持的工程使用方式

- 本地 CLI agent 交互
- 小型任务编排
- 本地 skill 驱动工作流
- 任务板与 worktree 绑定式开发
- 轻量级团队消息协作

## 8. 剩余风险

虽然当前版本已达到“可进入下一阶段实战”的水平，但仍存在以下工程风险：

1. 长上下文退化风险  
   目前已验证基础 working memory 与压缩路径，但尚未做超长多轮对话耐久压测。

2. provider 兼容性风险  
   当前主要验证对象为 Anthropic 兼容链路与 MiniMax 兼容配置，尚未覆盖多 provider 行为差异。

3. 真实编码闭环深水区风险  
   目前已验证简单文件编辑与 worktree 管理，尚未系统验证“跨多文件修改 -> 运行测试 -> 读取失败 -> 再修复”的长链路。

4. team protocol 深度风险  
   当前 `team send/inbox` 已验证，`approval / shutdown / task claim` 仍需要更强的 live 协议流测试。

## 9. 建议的下一阶段测试

建议下一轮测试扩展到以下四组：

1. 长上下文耐久压测  
   连续 15 到 30 轮对话，验证压缩后信息保真度。

2. 真实编码闭环压测  
   在 worktree 中完成一个小型 bugfix，要求 agent 自主读文件、修改、运行测试、再汇报。

3. 异常恢复压测  
   故意输入不存在的文件、skill、task id，验证 agent 的错误恢复与降级行为。

4. team protocol live 压测  
   验证 `plan_approval`、`shutdown`、`task_claim` 等协议流的真实运行质量。

## 10. 最终结论

截至 2026-04-25，本项目已经通过以下两类关键门槛：

- 自动化测试门槛：`71 passed, 1 skipped`
- 真实模型驱动的用户场景门槛：基础能力与复杂组合场景均通过

因此，可以将当前版本定义为：

**具备工业级 agent 项目的基础质量门槛，已经适合进入真实任务级验证和后续工程化打磨阶段。**
