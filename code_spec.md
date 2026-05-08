# MiniCLIAgent 实现状态清单

本文档用于把 [`dev_spec.md`](/Users/yuanzilin/Minicliagent/dev_spec.md) 落成一份持续更新的实现清单。它关注的是当前代码实现状态，而不是目标愿景或开发过程说明。

维护规则如下：

- 已完成项打 `- [x]`
- 未完成项保持 `- [ ]`
- 每完成一个里程碑，立即回写本文件
- 章节结构尽量与 `dev_spec.md` 保持一致

## 1. 项目基础

- [x] 建立正式 `pyproject.toml`
- [x] 建立 `minicliagent/` 包
- [x] 建立 `CLI / App / Core / Infra` 基础目录
- [ ] 建立 `.env.example`
- [x] 建立基础 `README.md`

## 2. 配置与状态目录

- [x] 建立 `Settings` 类型化配置
- [x] 统一 `.minicliagent/` 状态目录约定
- [x] 建立 `sessions/` 持久化目录
- [x] 建立 `tasks/` 持久化目录
- [x] 建立 `team/` 持久化目录
- [x] 建立 `worktrees/` 持久化目录
- [x] 建立 `logs/` 目录与日志初始化

## 3. Provider 与运行时

- [x] 建立 `LLMProvider` 抽象
- [x] 建立 `AnthropicProvider`
- [x] 建立 `tool_adapter`
- [x] 建立基础 `AgentRuntime`
- [x] runtime 可将 tool schema 发给 provider
- [x] runtime 支持 session message 持久化
- [x] runtime 事件流
- [x] runtime 后台通知注入
- [x] MCP 配置项与服务器声明结构
- [x] MCP stdio 连接适配与会话初始化
- [x] MCP 工具发现、转换为 `ToolSpec` 与注册
- [x] MCP 工具命名空间前缀与冲突检测
- [x] MCP 工具启停控制与按服务器粒度禁用
- [x] MCP 连接失败 / 超时 / 断连降级策略
- [x] MCP 工具调用日志、错误日志与健康检查
- [x] MCP 单工具超时与最大返回大小限制（截断时显示原始长度）
- [x] MCP 调试与诊断信息输出

## 4. 工具系统

- [x] 建立 `ToolSpec`
- [x] 建立 `ToolResult`
- [x] 建立 `ToolRegistry`
- [x] 注册 `bash`
- [x] 注册 `read_file`
- [x] 注册 `write_file`
- [x] 注册 `edit_file`
- [x] `edit_file` 支持 `replace_all` 参数控制全局替换
- [x] bash 工具集成危险命令检测与拦截（防 rm -rf /、fork bomb、sudo 等）
- [x] 注册 `list_skills`
- [x] 注册 `load_skill`
- [x] 注册 `task_create`
- [x] 注册 `task_list`
- [x] 注册 `task_update`
- [x] 注册 background task tools
- [x] 注册 teammate tools
- [x] 注册 worktree tools

## 5. Skill 系统

- [x] 建立 `SkillSummary`
- [x] 建立 `SkillDocument`
- [x] 建立本地 `SkillLoader`
- [x] 支持 skill list
- [x] 支持 skill load
- [x] 支持 PyYAML 解析 SKILL.md frontmatter，安装不可用时回退手动解析
- [x] 建立 `SkillService`
- [x] skill matcher
- [x] runtime 记录已加载 skill
- [x] skill 注入大小限制
- [x] skill 加载事件追踪

## 6. Task 系统

- [x] 建立 `TaskRecord`
- [x] 建立 `TaskBoard`
- [x] 支持 task create
- [x] 支持 task update
- [x] 支持 task list
- [x] 建立 `TaskService`
- [x] task dependency / blocked_by 流转完善
- [x] task priority / labels 完善
- [x] task 与 worktree 绑定

## 7. 上下文管理

- [x] 建立 `ContextManager`
- [x] 支持旧 tool result 微压缩
- [x] 支持长文本消息裁剪
- [x] 完整第一层：工具结果裁剪策略
- [x] 完整第二层：微压缩策略
- [x] 完整第三层：会话压缩策略（含 tool call 摘要注入）
- [x] 保留 working memory（task / skill / request_id / teammate 状态）

## 8. 记忆系统

- [x] 建立 `core/memory/` 模块
- [x] 建立 `MemoryService`
- [x] 建立 Markdown-first memory store
- [x] 建立 `.minicliagent/memory.md` 汇总文件写入逻辑
- [x] 建立 `.minicliagent/memory/` 会话记忆片段写入逻辑
- [x] 建立 `.minicliagent/memory_index/` 派生索引目录约定
- [x] 接入本地 mem0 OSS 作为 dense 检索索引
- [x] 建立 BM25 检索器
- [x] 建立 hybrid ranker
- [x] dense top-k 默认为 4
- [x] BM25 top-k 默认为 4
- [x] 融合排序公式为 `0.3 * normalized_bm25 + 0.7 * normalized_dense`
- [x] final top-k 默认为 6
- [x] 注册 `memory_search` 工具
- [x] runtime system prompt 提示 agent 可主动查询长期记忆
- [x] runtime 不每轮自动注入长期记忆
- [x] 上下文压缩时触发 memory compact hook
- [x] 交互式 `run` 退出时触发 memory exit hook
- [x] hook 自动追加值得长期保存的记忆
- [x] mem0 不可用时降级到 BM25
- [x] mem0 初始化配置失败时回退 `Memory()` 空构造再降级
- [x] `LocalMemorySummarizer` 关键词匹配使用词边界正则避免误命中
- [x] 记忆功能关闭时不影响 `run` 主链路

## 9. CLI

- [x] 建立 `run` 命令
- [x] `run` 支持 `--prompt`
- [x] `run` 支持 `--session`
- [x] 建立 `tasks create`
- [x] 建立 `tasks list`
- [x] 建立 `skills list`
- [x] 建立 `tasks update`
- [x] 建立 `skills load`
- [x] 建立 `team` 子命令
- [x] 建立 `worktree` 子命令

## 10. 后台任务

- [x] 建立 `BackgroundManager`
- [x] 支持后台命令执行
- [x] 支持状态：`running/completed/timeout/error/cancelled`
- [x] 支持结果 drain
- [x] 支持查询后台任务状态

## 11. Team / 多 Agent

- [x] 建立 message bus（含两阶段读取 + staging 崩溃保护 + ack 确认）
- [x] 建立 teammate manager
- [x] 建立协议消息类型
- [x] 建立 `request_id` 关联机制
- [x] 支持 `shutdown_request / shutdown_response`
- [x] 支持 `plan_approval_request / plan_approval_response`
- [x] 支持 `task_claim / task_claim_result`

## 12. Worktree

- [x] 建立 repo root 检测
- [x] 建立 worktree manager
- [x] 建立 worktree metadata 持久化
- [x] 支持 task <-> worktree 绑定
- [x] 支持在指定 worktree 执行命令
- [x] 支持 worktree closeout（含异常处理与 close_failed 状态）

## 13. 可观测性

- [x] 建立结构化日志
- [x] 建立 transcript 持久化
- [x] 建立 tool call tracing
- [x] 建立 background task tracing
- [x] 建立 worktree lifecycle events

## 14. 测试

- [x] 建立 unit tests 基础盘
- [x] 建立 integration tests 基础盘
- [x] runtime loop fake-provider 测试
- [x] CLI smoke 测试
- [x] skill/task/tool tests
- [x] background tasks tests
- [x] teammate protocol tests
- [x] worktree tests
- [x] Anthropic smoke test
- [x] memory store tests
- [x] BM25 检索 tests
- [x] hybrid ranker tests
- [x] `memory_search` tool tests
- [x] memory hook integration tests
- [x] memory disabled regression tests
- [x] multi-session memory evaluation dataset test
- [x] CLI memory flow integration test
- [x] CLI 记忆链路尽量覆盖真实 `create_agent_service` 组装路径
- [x] 记忆摘要 provider 不可用时的本地 fallback / 降级策略
- [x] `memory_search` 降级与排序诊断信息增强

## 15. 文档与收口

- [x] 建立 `dev_spec.md`
- [x] 建立 `code_spec.md`
- [x] 建立 foundation plan 文档
- [x] README 完整 Quick Start 与架构说明
- [x] `learn-claude-code` 与正式包边界清理
- [x] 迁移到 `examples/learn-claude-code/`
