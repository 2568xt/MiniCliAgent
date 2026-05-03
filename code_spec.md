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
- [x] 建立 `.env.example`
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

## 4. 工具系统

- [x] 建立 `ToolSpec`
- [x] 建立 `ToolResult`
- [x] 建立 `ToolRegistry`
- [x] 注册 `bash`
- [x] 注册 `read_file`
- [x] 注册 `write_file`
- [x] 注册 `edit_file`
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
- [x] 完整第三层：会话压缩策略
- [x] 保留 working memory（task / skill / request_id / teammate 状态）

## 8. CLI

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

## 9. 后台任务

- [x] 建立 `BackgroundManager`
- [x] 支持后台命令执行
- [x] 支持状态：`running/completed/timeout/error/cancelled`
- [x] 支持结果 drain
- [x] 支持查询后台任务状态

## 10. Team / 多 Agent

- [x] 建立 message bus
- [x] 建立 teammate manager
- [x] 建立协议消息类型
- [x] 建立 `request_id` 关联机制
- [x] 支持 `shutdown_request / shutdown_response`
- [x] 支持 `plan_approval_request / plan_approval_response`
- [x] 支持 `task_claim / task_claim_result`

## 11. Worktree

- [x] 建立 repo root 检测
- [x] 建立 worktree manager
- [x] 建立 worktree metadata 持久化
- [x] 支持 task <-> worktree 绑定
- [x] 支持在指定 worktree 执行命令
- [x] 支持 worktree closeout

## 12. 可观测性

- [x] 建立结构化日志
- [x] 建立 transcript 持久化
- [x] 建立 tool call tracing
- [x] 建立 background task tracing
- [x] 建立 worktree lifecycle events

## 13. 测试

- [x] 建立 unit tests 基础盘
- [x] 建立 integration tests 基础盘
- [x] runtime loop fake-provider 测试
- [x] CLI smoke 测试
- [x] skill/task/tool tests
- [x] background tasks tests
- [x] teammate protocol tests
- [x] worktree tests
- [x] Anthropic smoke test

## 14. 文档与收口

- [x] 建立 `dev_spec.md`
- [x] 建立 `code_spec.md`
- [x] 建立 foundation plan 文档
- [x] README 完整 Quick Start 与架构说明
- [x] `learn-claude-code` 与正式包边界清理
- [x] 迁移到 `examples/` 或 `legacy/`
