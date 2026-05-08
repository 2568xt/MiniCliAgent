# MiniCLIAgent 开发规格说明

## 1. 文档目标

本文档定义 MiniCLIAgent 的产品边界、运行时结构、模块职责和工程约束。

它服务于三个目标：

1. 说明这个项目到底要构建什么
2. 给后续实现和测试提供统一边界
3. 为后续维护与扩展提供一致的设计基线

本文档描述的是正式项目规格，不是开发过程记录，也不是个人简历说明。

## 2. 项目定位

MiniCLIAgent 是一个面向本地开发环境的 Python CLI Agent 项目。

它的定位是：

- 一个可运行、可测试、可扩展的本地 agent harness
- 一个强调工具调用、状态落盘、任务管理和工作区隔离的实验平台
- 一个可作为 agent 工程参考实现的本地项目

它不是：

- 图形化工作流平台
- 远程 SaaS Agent 服务
- 复杂的企业权限编排系统
- 全功能多模型管理平台

项目的核心原则是：

> 模型负责推理，代码负责 harness。

## 3. 设计目标

### 3.1 功能目标

1. 提供一个基于 Anthropic SDK 风格接口的本地 CLI Agent 运行时
2. 支持 tool calling，并通过统一的 `ToolRegistry` 管理工具
3. 支持 `skills / tasks / team / worktree / background tasks`
4. 支持会话消息持久化与上下文压缩
5. 支持在本地 git 仓库中进行 task 与 worktree 绑定
6. 支持本地长期记忆，并通过 agent 可控的工具检索跨会话信息

### 3.2 工程目标

1. 模块边界清晰
2. 默认行为可读、可测、可维护
3. 运行时主链路、状态面和工具系统保持可审查、可验证
4. 扩展新工具、新状态或新 provider 时尽量是加法式修改

## 4. 非目标

当前阶段不做以下内容：

1. Web GUI 或桌面 GUI
2. 完整 MCP runtime
3. 多 provider 全量统一抽象
4. 企业级权限系统
5. 分布式任务调度
6. 持续常驻的 daemon / cron 系统
7. Honcho 或其他重型外部记忆服务
8. 每轮对话原文的无选择自动长期写入
9. 作为独立平台完整托管/编排 MCP 服务器生命周期

## 5. 总体架构

项目采用四层结构：

- `CLI`
- `App`
- `Core`
- `Infra`

四层的关系是：

- `CLI` 负责命令入口和用户可见输出
- `App` 负责组装服务和用例流程
- `Core` 负责 agent 运行时与领域逻辑
- `Infra` 负责文件系统、shell、git、日志等外部实现

### 5.1 分层职责

#### CLI 层

职责：

- 解析参数
- 调用 `AgentService`
- 输出人类可读结果
- 将常见错误转换为友好的 CLI 提示

不负责：

- agent loop
- provider 协议细节
- 业务规则实现

#### App 层

职责：

- 组装 runtime、services、registry、state 目录
- 处理面向用户的 use case
- 连接 CLI 与 Core

典型对象：

- `AgentService`
- `TaskService`
- `SkillService`
- `TeamService`
- `WorktreeService`
- `MCPService`

#### Core 层

职责：

- 定义运行时主循环
- 定义 provider 抽象与请求/响应模型
- 定义工具系统
- 定义上下文压缩、task、skill、team、worktree 等核心能力

这是项目的主体层。

#### Infra 层

职责：

- 文件路径安全处理
- shell 命令执行
- git worktree 操作
- 结构化日志与 transcript 落盘

Infra 负责“怎么做”，不负责“为什么做”。

## 6. 运行时结构图

下面这张图描述一次典型 `run --prompt` 调用的运行路径。

```mermaid
flowchart TD
    U[用户 / CLI 命令] --> CLI[cli.main]
    CLI --> APP[AgentService]
    APP --> RT[AgentRuntime]

    RT --> STORE[MessageStore]
    RT --> CTX[ContextManager]
    RT --> REG[ToolRegistry]
    RT --> LLM[AnthropicProvider]

    LLM --> MODEL[LLM / Compatible Gateway]
    MODEL --> LLM

    REG --> TOOLS[Built-in Tools]
    TOOLS --> FILES[read_file / write_file / edit_file]
    TOOLS --> TASKS[task_create / task_update / task_list]
    TOOLS --> SKILLS[list_skills / load_skill]
    TOOLS --> BG[background_run / background_check]
    TOOLS --> TEAM[team_send / team_inbox]
    TOOLS --> WT[worktree_create / worktree_list]
    TOOLS --> MEM[memory_search]
    TOOLS --> MCP[MCP Tools via MCPService]
    APP --> MCPSVC[MCPService]
    MCPSVC --> MCPSRV[MCP Servers (stdio)]
    MCPSVC --> REG

    RT --> EVENTS[EventBus / Logger / Transcript]
    APP --> STATE[.minicliagent state root]
    STATE --> SESS[sessions/]
    STATE --> TASKDIR[tasks/]
    STATE --> TEAMDIR[team/]
    STATE --> WTDIR[worktrees/]
    STATE --> MEMORY[memory.md / memory/ / memory_index/]
    STATE --> LOGDIR[logs/]
```

### 6.1 一次运行的最小闭环

一次最小运行包含以下步骤：

1. CLI 读取命令与参数
2. `AgentService` 组装 runtime、services、MCPService 和依赖
3. `AgentRuntime` 读取 session 消息
4. `ContextManager` 准备上下文
5. `AnthropicProvider` 发起模型请求
6. 如果模型请求工具，则通过 `ToolRegistry` 执行
7. 工具结果回写到 session
8. 如果模型需要跨会话信息，可主动调用 `memory_search`
9. transcript、events、logs 落盘
10. 返回最终文本给 CLI

## 7. 核心模块规格

### 7.1 AgentRuntime

`AgentRuntime` 是运行时主编排对象。

职责：

- 构造 `ModelRequest`
- 调用 provider
- 处理 tool loop
- 写入消息存储
- 注入 background 通知
- 记录 loaded skills 与 working memory
- 在上下文压缩或交互退出时触发长期记忆总结 hook
- 输出最终 turn 结果

约束：

- 不直接处理 CLI 参数
- 不直接操作 git
- 不直接知道 `.env` 的细节
- 不直接依赖 mem0 SDK，应通过 memory service/provider 边界调用

### 7.2 LLM Provider

当前主 provider 为 `AnthropicProvider`。

要求：

- 接收统一的 `ModelRequest`
- 返回统一的 `ModelResponse`
- 支持 tool schema 下发
- 支持 Anthropic 兼容接口
- 对已知兼容网关做必要的 URL 归一化
- 通过 `MCPService` 接入 MCP 服务器，暴露为可调用工具来源
- 支持多 MCP 服务器并存接入与独立管理
- MCP 服务器通过 stdio 连接方式接入，由 `core/mcp/transport.py` 负责连接管理
- MCP 通过适配层实现，不改变主 provider 的统一请求/响应接口
- MCP 服务器连接失败、超时或不可用时，自动降级为仅保留本地内置工具，不中断主运行时
- MCP 工具发现结果转换为统一 `ToolSpec`，经 `MCPService.register_tools()` 进入 registry

设计原则：

- Anthropic-first 路径已落地，provider adapter 边界保留
- MCP 只作为工具扩展面，不作为 agent 主循环的运行时核心依赖

### 7.3 ToolRegistry

`ToolRegistry` 是工具系统的统一入口。

职责：

- 注册 `ToolSpec`
- 提供工具列表给 provider adapter
- 执行工具并返回 `ToolResult`
- 聚合本地内置工具与外部 MCP 服务器暴露的工具

要求：

- 工具声明必须显式包含 `name / description / input_schema / handler`
- 工具扩展应尽量只通过注册完成
- 内置工具应按职责拆分到 `core/tools/builtins/`
- `edit_file` 应支持 `replace_all` 参数控制单次替换或全局替换
- `bash` 工具必须集成危险命令检测：通过正则匹配 `rm -rf /`、fork bomb、`mkfs`、`dd` 写设备等危险模式，通过词边界正则匹配 `sudo`、`shutdown`、`reboot` 等高危子串，命中即拦截
- MCP 工具应在注册层完成命名空间隔离、冲突检测与可用性标记
- MCP 工具名应支持服务器前缀或命名空间前缀，避免与内置工具冲突
- 外部 MCP 工具不可直接绕过 registry 进入 runtime 执行链路
- MCP 工具调用应支持按服务器粒度启停与禁用

### 7.4 ContextManager

`ContextManager` 负责控制上下文规模。

当前策略分三层：

1. 工具结果裁剪
2. 旧工具结果微压缩
3. 历史消息压缩（含被截断段落的 tool call 名称与参数摘要注入）

同时保留 working memory，例如：

- 已加载的 skill
- 当前 task 状态
- request_id
- teammate 相关状态

约束：

- 不在 `messages[]` 中注入不兼容的 `role=system`
- provider 特定限制应在运行时链路中被正确处理

### 7.5 Skill System

skill 系统负责从本地工作区发现与加载 `SKILL.md`。

要求：

- skill 扫描路径为 `<workspace>/skills/**/SKILL.md`
- SKILL.md frontmatter 优先使用 PyYAML 解析，安装不可用时自动回退手动 key:value 解析
- 支持 `list_skills`
- 支持 `load_skill`
- 支持基础 matcher
- runtime 应记录已加载 skill

### 7.6 Task System

task 系统负责持久化任务状态。

要求：

- 支持 `create / update / list`
- 任务数据存放在 `.minicliagent/tasks/`
- 支持 `status / owner / priority / labels / blocked_by / worktree`

设计目标：

- 结构简单
- 易读
- 便于直接检查 JSON 状态

### 7.7 Background Tasks

background 系统负责后台 shell 执行。

要求：

- 支持启动后台任务
- 支持查询状态
- 支持结果 drain
- 至少支持 `running / completed / timeout / error / cancelled`

### 7.8 Team System

team 系统负责轻量级 agent 间消息与协议。

要求：

- 支持基础 inbox 消息收发（两阶段读取协议：read_inbox 将消息移至 staging 文件，ack_inbox 确认后删除，未 ack 的消息在下次读取时恢复，实现崩溃保护）
- 支持 `request_id`
- 支持协议消息类型，例如：
  - `shutdown_request / shutdown_response`
  - `plan_approval_request / plan_approval_response`
  - `task_claim / task_claim_result`

设计原则：

- 先实现可读、可测的本地协议
- 不把它做成复杂的分布式消息系统

### 7.9 Worktree System

worktree 系统负责把 task 与 git 工作区隔离结合起来。

要求：

- 自动检测 repo root
- 创建和列出 worktree
- 记录 worktree 元数据
- 支持 task 与 worktree 双向绑定
- 支持在指定 worktree 执行命令
- close 操作必须捕获异常，失败时设置 close_failed 状态并通过事件总线通知，不抛异常中断调用方

约束：

- 非 git 工作区下要返回可读错误
- 不应把 git 原生命令输出直接泄漏给最终用户

### 7.10 Memory System

memory 系统负责跨会话长期记忆。

第一版后端选择：

- 使用本地 mem0 OSS 作为 dense 检索索引能力
- 不接入 Honcho
- 不提供多记忆后端切换 UI

数据原则：

- 采用 Markdown-first
- `.minicliagent/memory.md` 是长期记忆汇总文件
- `.minicliagent/memory/` 保存每次 hook 生成的会话记忆片段
- `.minicliagent/memory_index/` 保存 mem0、SQLite 或其他检索索引派生状态
- Markdown 文件是真实数据源，索引损坏时应能从 Markdown 重建

读取要求：

- 注册 `memory_search` 工具
- agent 自己判断什么时候调用 `memory_search`
- runtime 不应每轮自动把长期记忆注入上下文
- system prompt 可以轻量提示：需要跨会话信息时先查长期记忆

写入要求：

- 在上下文压缩时触发 `compact_hook`
- 在交互式 `run` 退出时触发 `exit_hook`
- hook 应让 agent/provider 总结本次会话中值得长期保存的事实、偏好和项目约定
- 如果 hook 判断没有值得记住的内容，不写入
- 写入自动追加，不要求用户交互确认
- 写入内容不应是原始 transcript dump
- 本地总结器关键词匹配使用词边界正则（`\bprefer\b` 等），避免子串误命中（如 "like" 误匹配 "alike"）
- 写入前应做基础文本去重，避免明显重复条目

混合检索要求：

- dense 检索使用 mem0 或其本地向量索引，取 `dense_top_k = 4`
- BM25 检索扫描 `.minicliagent/memory.md` 与 `.minicliagent/memory/*.md`，取 `bm25_top_k = 4`
- 对 dense 与 BM25 的分数分别进行查询内归一化
- dense 与 BM25 的候选集合并去重
- 只被一路命中的结果，另一路归一化分数按 `0` 处理
- 融合分数公式为 `0.3 * normalized_bm25 + 0.7 * normalized_dense`
- 最终按融合分数排序，取 `final_top_k = 6`
- 返回结果应包含来源、内容摘要、原始分数、归一化分数和融合分数

归一化约束：

- 默认使用查询内 min-max 归一化到 `0..1`
- 如果某一路所有命中分数相同，则该路命中的候选归一化为 `1`
- 未命中的候选归一化为 `0`

降级要求：

- mem0 或 dense index 不可用时，应降级到 BM25 检索
- mem0 初始化配置失败时，应尝试 `Memory()` 空构造作为中间回退，仍失败才最终降级为不可用索引
- BM25 不可用或记忆文件不存在时，应返回空结果而不是中断 agent 主链路
- 降级事件应写入 event/log，用户可见错误保持简洁

配置要求：

- `MINICLIAGENT_MEMORY_ENABLED`：默认 `1`
- `MINICLIAGENT_MEMORY_DENSE_WEIGHT`：默认 `0.7`
- `MINICLIAGENT_MEMORY_BM25_WEIGHT`：默认 `0.3`
- `MINICLIAGENT_MEMORY_DENSE_TOP_K`：默认 `4`
- `MINICLIAGENT_MEMORY_BM25_TOP_K`：默认 `4`
- `MINICLIAGENT_MEMORY_FINAL_TOP_K`：默认 `6`

设计原则：

- memory 系统应通过 `MemoryService` / provider 边界接入 runtime
- `AgentRuntime` 不直接读写 Markdown 文件
- `ToolRegistry` 只负责暴露 `memory_search` 工具
- 第一版优先实现可读、可测、可降级的本地记忆闭环

实现收尾要求：

- CLI 记忆链路测试应尽量覆盖真实 `create_agent_service` 组装路径，而不只依赖纯 mock service
- 记忆摘要在外部 provider 不可用时应具备本地或降级策略，避免离线环境导致 exit/compact hook 整体失败
- `memory_search` 的降级、命中与排序行为应保留足够诊断信息，便于排查 dense / BM25 / hybrid 结果差异
- 记忆系统的测试说明与设计约束需要与实现保持同步更新

## 8. 状态目录约定

所有本地状态统一放在 `.minicliagent/` 下。

目录约定如下：

```text
.minicliagent/
├─ sessions/
├─ tasks/
├─ team/
├─ worktrees/
├─ logs/
├─ memory.md
├─ memory/
└─ memory_index/
```

说明：

- `sessions/` 保存会话消息
- `tasks/` 保存任务 JSON
- `team/` 保存本地消息与 inbox 数据
- `worktrees/` 保存 worktree 元数据
- `logs/` 保存事件、结构化日志和 transcript
- `memory.md` 保存长期记忆汇总
- `memory/` 保存按 hook/session 切分的长期记忆片段
- `memory_index/` 保存可重建的检索索引派生状态

## 9. 仓库结构要求

正式产品代码位于：

- `minicliagent/`

参考样例代码位于：

- `examples/learn-claude-code/`

要求：

- 正式运行时不得依赖样例脚本作为主入口
- 样例材料可以保留，但边界必须清晰

## 10. 测试策略

项目测试分为三层：

### 10.1 Unit Tests

覆盖：

- 配置
- provider adapter
- runtime 局部逻辑
- tools
- skills
- tasks
- team
- worktree
- memory store / BM25 / hybrid ranker
- logging / transcript

### 10.2 Integration Tests

覆盖：

- CLI 命令
- runtime tool loop
- state 持久化
- runtime 与事件/日志联动
- `memory_search` 工具链路
- 交互退出和上下文压缩的 memory hook
- 多 session 记忆评估数据集
- CLI 真实记忆写入/退出链路

### 10.3 Live Tests

覆盖：

- 真实模型链路
- 真实工具编排
- 真实用户场景

要求：

- 默认测试不依赖 live provider
- live smoke test 通过显式环境变量开启

## 11. 文档要求

项目至少维护以下文档：

- `dev_spec.md`：开发规格说明
- `code_spec.md`：实现状态清单
- `README.md`：中文首页说明
- `docs/getting-started/learning-path.md`：学习路径
- `docs/getting-started/`：演示 notebook（coding-demo、engineering-demo、mini-demo）
- `docs/testing/`：测试报告
- `docs/resume/`：会话恢复
- `docs/superpowers/`：高级能力说明

文档目标：

- 让工程边界清晰
- 让实现状态可追踪
- 让测试结果可复盘

## 12. MCP 接入约束

MCP 接入只作为工具扩展能力，不改变本项目的主定位与运行范式。

接入要求：

1. 支持通过配置声明一个或多个 MCP 服务器
2. 支持多服务器并存接入与独立管理
3. 支持 stdio 等明确可控的本地连接方式优先
4. 支持启动时发现 MCP 工具并转换为本地 `ToolSpec`
5. 支持工具命名空间前缀，避免与内置工具冲突
6. 支持 MCP 服务器健康检查、连接重试与降级关闭
7. 支持按服务器粒度启用/禁用
8. 支持记录 MCP 工具调用日志、错误日志与健康状态
9. 支持在运行时列出可用 MCP 工具，但不强制自动调用
10. 支持对单个 MCP 工具设置超时与最大返回大小限制
11. 支持在配置或启动失败时给出简洁可读错误
12. 支持在连接失败、超时或断连后自动降级到本地工具集合

不支持的内容：

- 不在本项目中实现完整 MCP host 平台
- 不负责统一托管远端 MCP 服务器生命周期
- 不把 MCP 工具接入做成必须依赖
- 不把 MCP 连接失败视为主 agent 不可运行的条件
- 不要求 agent 在每轮推理中自动刷新 MCP 工具列表

## 13. 设计约束

1. 不为了“未来可能需要”而提前引入重抽象
2. 默认优先可读性和可验证性
3. 新增功能优先沿用现有分层与模式
4. 用户可见错误必须尽量简洁、明确
5. 参考实现不等于原型代码，仍需保持工程纪律
6. MCP 相关实现必须保持可降级、可关闭、可诊断

## 14. 当前阶段结论

当前版本的开发方向应保持为：

- 一个本地可运行的、Anthropic-first 的 CLI Agent 项目
- 一个通过 `skills / tasks / background / team / worktree` 展示 agent harness 设计的实践项目
- 一个可作为本地 agent harness 参考实现的工程项目

后续所有实现工作，均应以本规格作为边界，而不是继续向无上限的“大而全 agent 平台”扩张。
