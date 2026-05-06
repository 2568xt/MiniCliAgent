# 项目技术亮点清单（MiniCLIAgent）

> 从 dev_spec.md、code_spec.md 与源码提炼，供简历编写时按需选取。每个亮点附带"简历话术方向"和"可量化角度"。

---

## 亮点 1：Agent Runtime + Tool Calling 闭环

**技术要点**：
- 实现 `AgentRuntime` 主编排循环：读取 session → 准备上下文 → 下发工具 schema → 调用 provider → 处理 tool loop → 写回 session
- 统一 `ToolRegistry` 注册模型，内置 12+ 工具按职责拆分到 `core/tools/builtins/`
- 完整 Anthropic 协议兼容：tool_use / tool_result 对应关系、错误回传、transcript 落盘
- 支持 `on_text_delta` 流式输出回调

**简历话术方向**：
- "设计并实现 AgentRuntime + ToolRegistry 闭环，支持 tool calling 全链路协议正确性，内置 12+ 工具覆盖文件/shell/skill/task/team/worktree/memory 7 大类能力面"
- "实现 Anthropic 兼容 provider adapter，保持统一请求/响应接口，支持流式输出与多轮 tool loop"

**可量化角度**：内置工具数、支持的工具类别数、协议兼容度、事件类型覆盖数

---

## 亮点 2：混合记忆检索系统（BM25 + Dense + Hybrid Ranker）

**技术要点**：
- 从零实现 BM25 检索器，支持 k1/b 参数可调，中英文混合分词（正则 + CJK 字符识别），IDF 平滑，文档平均长度归一化
- Dense 索引基于 mem0 OSS，Protocol 抽象边界，mem0 不可用时自动降级到纯 BM25
- 自研 Hybrid Ranker：双路候选集合并去重 → 查询内 min-max 归一化 → 加权融合排序（0.3 × BM25 + 0.7 × Dense，权重可配置）
- 写入策略：上下文压缩 Hook + 交互退出 Hook 自动触发记忆总结，LLM 总结 + 本地关键词 Fallback 双重保障离线可用
- Markdown-first 数据原则：Markdown 为真实数据源，索引损坏可从 Markdown 重建

**简历话术方向**：
- "独立实现 BM25 + Dense 混合记忆检索系统，包含标准 BM25 算法、min-max 归一化融合排序、mem0 自动降级策略，实现跨会话知识复用"
- "设计 LLM 自动总结 + 本地关键词 Fallback 双重记忆写入保障，确保离线环境记忆功能不中断"

**可量化角度**：34 个记忆专项测试、检索召回率对比、降级成功率、配置参数数量

---

## 亮点 3：三层上下文管理（ContextManager）

**技术要点**：
- 递进式三层压缩：工具结果裁剪（第一层）→ 微压缩/超长消息截断（第二层）→ 历史消息压缩（第三层）
- 历史溢出时注入摘要占位符，自动触发记忆 Hook 做长期保存
- 保留 working memory：已加载 skill、当前 task、request_id、teammate 状态，压缩不丢失关键上下文
- 所有参数可配置：keep_count / max_chars / history_max_messages

**简历话术方向**：
- "设计递进式三层上下文压缩策略，在 LLM 上下文窗口受限场景下平衡信息保留与 token 消耗"
- "实现 working memory 保留机制，压缩历史消息时不丢失 task/skill/teammate 等关键状态"

**可量化角度**：6 个 ContextManager 专项测试、三层策略覆盖度、可配置参数数

---

## 亮点 4：MCP 协议客户端（Model Context Protocol）

**技术要点**：
- 完整 MCP stdio 客户端实现：子进程生命周期管理、自动重连（可配置次数+延迟）、健康检查、断连降级
- MCP 工具 → 统一 `ToolSpec` 转换，命名空间前缀隔离，内置工具冲突检测
- 按服务器粒度独立启用/禁用、健康状态追踪、诊断信息暴露
- 外部 MCP 工具不可绕过 ToolRegistry 进入执行链路（安全边界）

**简历话术方向**：
- "实现完整 MCP stdio 客户端，支持外部工具的自动发现、命名空间隔离与冲突检测，将 MCP 服务器工具无缝接入 Agent 工具链"
- "设计 MCP 连接失败/超时/断连的自动降级策略，外部工具不可用时不影响 Agent 主链路"

**可量化角度**：20 个 MCP 专项测试、支持的重试次数、诊断信息字段数

---

## 亮点 5：多 Agent Team 协议

**技术要点**：
- 消息总线 + 队友管理器 + 收件箱构成轻量通信基础设施
- 结构化协议消息类型：`shutdown_request/response`、`plan_approval_request/response`、`task_claim/claim_result`
- `request_id` 跨 Agent 请求关联，协议消息 JSON 持久化
- 不做重型分布式系统，强调可读、可测、可审查

**简历话术方向**：
- "设计轻量级 Agent 间通信协议，实现消息总线 + 结构化协议消息 + request_id 关联，支持 shutdown/plan_approval/task_claim 等典型协作模式"
- "建立 Agent 间消息持久化与收件箱机制，使多 Agent 协作行为可审计、可复盘"

**可量化角度**：19 个 Team 专项测试、支持的协议消息类型数

---

## 亮点 6：Task + Worktree 工程化闭环

**技术要点**：
- Task 系统：create/update/list，支持 status/priority/labels/blocked_by 依赖链/worktree 绑定
- Worktree 系统：Git worktree 创建/列出/关闭，自动检测 repo root，元数据持久化
- Task ↔ Worktree 双向绑定，实现"一个任务一个隔离工作区"
- 在指定 worktree 执行命令，避免多任务修改互相污染

**简历话术方向**：
- "设计 Task 与 Git Worktree 深度绑定机制，实现任务状态、独立工作区和本地元数据双向关联"
- "实现 Worktree 生命周期管理，支持自动检测、创建、关闭与命令隔离执行"

**可量化角度**：16 个 Task 测试 + 8 个 Worktree 测试、Task 状态流转完备性

---

## 亮点 7：Background Task 异步执行

**技术要点**：
- 后台 Shell 命令执行，不阻塞 Agent 主循环
- 完整状态机：running → completed / timeout / error / cancelled
- 结果 Drain + 通知自动注入 Agent 对话流
- 支持状态查询与结果取回

**简历话术方向**：
- "实现后台异步任务执行引擎，支持完整状态机流转与结果通知自动注入，Agent 主循环不被阻塞"

**可量化角度**：7 个 Background 专项测试、状态机状态覆盖数

---

## 亮点 8：工程化实践（TDD + 可观测性）

**技术要点**：
- TDD 开发：55 个测试文件、139 个测试用例，测试代码量（3112 行）超过源码量（2983 行）
- 三层测试金字塔：Unit（配置/provider/runtime/tools/memory）+ Integration（CLI 命令/tool loop/memory hook）+ Live Smoke（真实模型链路）
- 结构化 JSON 日志分级输出 + Transcript 完整对话落盘 + Event Bus 事件流
- Tool call / background task / worktree lifecycle 全链路追踪
- 依赖注入 + 显式构造函数 + dataclass 不可变数据结构

**简历话术方向**：
- "遵循 TDD 开发范式，累计编写 139 个测试用例覆盖 12 个子系统，测试代码量超过源码，确保 Agent 核心链路可靠"
- "构建全链路可观测体系：结构化日志 + Transcript + Event Bus + 工具调用追踪，Agent 行为透明可回溯"

**可量化角度**：139 测试用例、55 测试文件、12 子系统覆盖、3112 行测试代码

---

## 亮点 9：降级优先的架构设计

**技术要点**：
- 所有外部依赖具自动降级：mem0 不可用 → 纯 BM25、LLM Summarizer 不可用 → 本地关键词 Fallback、MCP 断连 → 内置工具
- Agent 主链路不受任何外部依赖故障影响
- 降级事件写入 event/log，用户可见错误保持简洁

**简历话术方向**：
- "设计降级优先的架构策略，所有外部依赖（mem0/MCP/LLM Summarizer）不可用时自动降级，确保 Agent 核心链路零中断"

**可量化角度**：3 条降级路径、降级覆盖率 100%
