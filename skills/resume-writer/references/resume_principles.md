# 简历编写原则（Agent/CLI Agent 工程师方向）

## 1. 项目描述四段式结构

遵循"背景 → 目标 → 过程 → 结果"逻辑：

- **背景**：项目所属方向、行业痛点、为什么要做。例：*针对现有 CLI Agent 工具跨会话记忆丢失、上下文膨胀失控、多 Agent 协作无标准协议等痛点，设计并实现了本地 CLI Agent 运行时系统。*
- **目标**：技术目标或改进方向（提升记忆召回率、控制上下文膨胀、标准化 Agent 间通信）。例：*目标构建具备长期记忆、上下文控制、多 Agent 协作能力的本地 Agent Harness，实现跨会话知识复用与标准化 Agent 间协议。*
- **过程**：关键技术方案和工程实现细节，明确候选人负责部分、使用工具、面临挑战。例：*设计 AgentRuntime + ToolRegistry 闭环，实现 BM25/Dense 混合记忆检索，构建 MCP stdio 客户端，建立 Team 消息协议。*
- **结果**：量化数据展示最终效果。例：*系统实现 12 个子系统，139 个测试用例全绿，测试代码量超过源码，记忆检索召回率显著提升。*

## 2. 技术标签维度

简历需显式体现与岗位匹配度较高的技术要素，覆盖以下维度：

| 维度 | 关键词示例 |
|------|-----------|
| Agent 架构 | AgentRuntime, Tool Calling, Tool Registry, Provider Adapter, Message Store, Event Bus |
| 记忆/上下文 | BM25, Dense Retrieval, Hybrid Ranker, Context Manager, Context Compression, Working Memory |
| 协议与集成 | MCP (Model Context Protocol), stdio Transport, Tool Discovery, Health Check, Degradation |
| 多 Agent | Message Bus, Teammate Manager, Inbox, Protocol Messages, request_id Correlation |
| 工程协作 | Task Board, Worktree Binding, Background Task, Skill System, Markdown-first |
| 工程质量 | TDD, Unit/Integration/E2E Testing, Structured Logging, Transcript, Dependency Injection |
| 基础设施 | Python, Anthropic SDK, mem0, pytest, Git Worktree, JSON Lines Logging |

## 3. 亮点挖掘与差异化策略

面试官关注候选人主导了什么、有哪些独到之处、是否体现技术判断力：

1. **介绍决策过程**：说明选择某方案的原因，对比过哪些方案，最终决策背后的技术判断。
2. **展示问题解决能力**：描述遇到的技术难点与解决方法（如 mem0 挂了切 BM25、LLM Summarizer 挂了用本地关键词 fallback）。
3. **强调可复用性/通用性**：项目成果若具有通用价值或被团队复用，作为重点亮点。
4. **突出结果与影响力**：用量化指标体现项目价值（139 测试用例、12 子系统、测试代码超源码）。

## 4. 常见误区

| 误区 | 说明 |
|------|------|
| 大而空 | 不要用"负责 Agent 系统开发""参与 AI 工具建设"等泛化描述 |
| 工具堆砌 | 仅列工具名而不解释实际作用与价值 |
| 缺乏结果 | 没有量化指标的项目难以评估价值 |
| 逻辑混乱 | 过程描述过长但缺乏主线 |
| 贬低自己 | 不要用"只是 demo""小项目"等自我矮化表述 |

## 5. 改进建议

- 多用"**设计**""**主导**""**实现**""**优化**"等主动表达，少用"参与""协助"
- 按"背景 → 问题 → 技术方案 → 结果"结构描述
- 明确区分个人贡献与团队成果
- 每个 bullet point 以**动词开头**（设计、实现、优化、构建、集成...）
- 量化一切可量化的内容（子系统数、测试用例数、代码行数、工具数...）
