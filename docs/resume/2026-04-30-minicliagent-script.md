# MiniCLIAgent 简历讲稿

## 项目定位

MiniCLIAgent 是我为了拆解 Claude Code、OpenClaw、Hermes Agent 这类 agent 系统，自己实现的一个本地 Python CLI coding-agent harness。

我做这个项目的重点不是再包一层聊天接口，而是把一个 coding agent 真正需要的系统层能力做出来：模型负责推理，harness 负责工具调用、状态落盘、上下文控制、任务编排、工作区隔离和可观测性。

目前项目采用 CLI / App / Core / Infra 四层结构，主链路是：

`CLI -> AgentService -> AgentRuntime -> Provider + ToolRegistry -> 本地状态`

也就是说，用户从 CLI 发起请求后，`AgentRuntime` 会读取 session、准备上下文、把工具 schema 下发给 Anthropic 兼容 provider。如果模型返回 tool call，就通过 `ToolRegistry` 分发到文件、shell、skill、task、background、team、worktree 等内置工具，工具结果再写回会话，继续下一轮推理。

## 2-3 分钟主稿

MiniCLIAgent 这个项目我想讲的是一个本地 coding agent 的工程骨架。

我当时参考的是 Claude Code、OpenClaw 和 Hermes Agent 这类系统。它们共同的特点是，模型本身只负责推理，真正决定 agent 能不能稳定工作的，是外层 harness：怎么把工具暴露给模型，怎么保存会话和任务状态，怎么控制上下文膨胀，怎么把长任务和多 agent 协作纳入一个可验证的工程流程。

所以我用 Python 做了一个本地 CLI agent。架构上分成四层：CLI 层只负责命令入口和用户输出；App 层负责组装 runtime、provider、registry 和状态目录；Core 层是核心能力，包括 AgentRuntime、ToolRegistry、ContextManager、skills、tasks、team、worktree；Infra 层负责文件系统、shell、日志这些外部适配。

项目里我最核心的工作有三块。

第一块是 agent runtime 和工具系统。我实现了一个 `AgentRuntime + ToolRegistry` 的闭环：模型请求里会带上工具 schema，模型返回 tool use 后，runtime 根据工具名调用 registry，再把 tool result 按 Anthropic 兼容格式写回会话。目前仓库里有 14 个内置工具入口，覆盖文件读写编辑、shell、skill 加载、任务板、后台任务、team 消息和 git worktree。这里我比较关注协议正确性，比如 tool use 和 tool result 的对应关系、错误结果的回传、transcript 的落盘。

第二块是上下文和 skill 系统。这个项目把 skill 做成类似 Claude Code / OpenClaw 的文件系统能力包，扫描 `<workspace>/skills/**/SKILL.md`，通过 frontmatter 做发现，按需加载正文。runtime 会记录已经加载的 skill，并通过 working memory 注入到系统提示里。上下文方面，我实现了三层策略：先裁剪过长工具结果，再微压缩旧工具结果，最后在消息数过多时做历史摘要，目标是让长会话不会因为工具输出过多而失控。

第三块是工程化协作能力。我做了持久化 task board，任务状态会落到 `.minicliagent/tasks/`，支持 status、owner、priority、labels、blocked_by 和 worktree 绑定；worktree 模块会检测 git repo，把任务和独立工作区绑定起来，避免多任务修改互相污染；background manager 支持后台 shell 执行和结果通知注入；team 模块实现了本地 inbox 和轻量协议，包括审批、关停、任务 claim 这些 request / response 类型。

这个项目和 Claude Code 的对齐点，是它也是 terminal-first，围绕读文件、改文件、跑命令、维护会话和 git 工作流来构建；和 OpenClaw / Hermes 的对齐点，是把 skills、memory/context、工具编排和本地持久化作为 agent 的核心能力，而不是只做一次性的 prompt 调用。当然它不是一个完整商业产品，没有做完整 MCP runtime、企业权限系统和长期自我进化学习，但它覆盖了 coding agent harness 最核心的主链路，而且这些能力都有测试保护。

验证方面，我给它补了 unit test、integration test、runtime fake-provider 测试和可选 live smoke test。当前本地跑 `pytest tests/unit tests/integration -q` 是 80 passed、1 skipped。测试覆盖了 CLI、provider adapter、tool loop、ContextManager、message store、event bus、logging、skills、tasks、background、team 和 worktree。这也是我这个项目最想体现的能力：不只是能 demo，而是能用工程方式把 agent 系统拆清楚、跑通并验证。

## 30 秒精简版

MiniCLIAgent 是我实现的一个本地 Python CLI coding-agent harness，参考了 Claude Code、OpenClaw 和 Hermes Agent 的设计。它不是简单调用一次大模型，而是把一个 agent 的系统层能力做出来：`AgentRuntime` 负责 tool loop，`ToolRegistry` 统一管理工具，`ContextManager` 做上下文压缩，skills 做按需能力加载，task/worktree/background/team 负责工程协作和状态持久化。当前有 14 个内置工具入口，覆盖 7 类能力面，所有状态落在 `.minicliagent/` 下，并通过 80 passed、1 skipped 的测试套件验证。这个项目最能体现我对 agent 工程的理解：模型负责推理，代码负责 harness。

## 面试追问答法

### 1. 为什么要做这个项目？

我想验证一个观点：现在 coding agent 的难点不只是模型能力，而是模型外面的执行系统。真正复杂的是工具协议、上下文管理、状态持久化、错误恢复和工程隔离。所以我没有只做 prompt wrapper，而是从 runtime、tool registry、message store、context manager、worktree 这些模块开始拆。

### 2. 你怎么对齐 Claude Code？

Claude Code 的核心是 terminal-first：理解代码库、读写文件、运行命令、处理 git 工作流。MiniCLIAgent 也按这个方向做了最小闭环：CLI 入口、文件工具、shell 工具、会话落盘、transcript、worktree 和测试验证。区别是 Claude Code 是成熟产品，我这个项目是面向学习和工程验证的最小可审查实现。

### 3. 你怎么对齐 OpenClaw / Hermes Agent？

我主要对齐了两个方向。第一是 skills，把可复用工作流做成 `SKILL.md`，通过描述做发现，按需加载正文，避免每次都把全部 instructions 塞进上下文。第二是持久化和 memory/context，把 session、task、team、worktree、logs 都落在 `.minicliagent/`，让 agent 的行为可以复盘，也能在多轮任务中保存工作状态。

### 4. 这个项目最有技术含量的点是什么？

我认为是 runtime tool loop 和上下文控制。tool loop 不是简单调用函数，而是要保持模型协议正确：assistant 的 tool use、user 的 tool result、错误状态、最终文本都要按 provider 兼容格式回放。上下文控制则要在不丢关键状态的情况下压缩历史和工具输出，否则 agent 做长任务时成本和质量都会恶化。

### 5. 有没有安全设计？

有基础安全边界，但我会诚实说还不是生产级权限系统。文件工具用 `safe_workspace_path` 限制路径不能逃出 workspace；shell runner 对明显危险命令做了拦截，并设置超时和输出截断；worktree 也把任务修改隔离到独立工作区。后续如果继续做，会补更细的 permission mode、命令审批、工具白名单和审计策略。

### 6. team 模块是不是完整多 agent？

不是完整分布式多 agent 系统，我把它定位成轻量级本地协作协议。它有 message bus、inbox、request_id，还有 shutdown、plan approval、task claim 等协议类型。它的价值是先把 agent 之间怎么传任务、怎么确认请求、怎么复盘消息这件事做清楚，而不是一开始就做复杂调度平台。

### 7. 还有哪些不足和下一步？

下一步我会做四件事。第一是更强的 permission system，把 bash、文件写入、worktree 操作分级审批。第二是补完整 MCP runtime，让外部工具接入更标准。第三是把 team 从消息协议推进到真正的 subagent worker，并和 worktree isolation 结合。第四是做更长链路的 coding benchmark，比如跨多文件修改、跑测试、读失败、再修复的闭环评估。

## 简历表述建议

当前源码里直接注册的模型工具入口是 14 个，不建议在面试里强调“27 个工具”，除非能把 CLI 子命令、协议类型或内部能力也一起解释清楚。更稳的说法是：

- 设计 `AgentRuntime + ToolRegistry`，实现 14 个内置工具入口，覆盖文件、shell、skill、task、background、team、worktree 7 类能力面。
- 实现基于 `SKILL.md` 的本地 skill 发现与按需加载，并通过 working memory 和三层上下文压缩控制长会话 token 膨胀。
- 实现 task board 与 git worktree 绑定，使任务状态、独立工作区和本地元数据可以双向关联。
- 建立 event log、JSON log、transcript 和自动化测试体系，当前默认测试套件 80 passed、1 skipped。
