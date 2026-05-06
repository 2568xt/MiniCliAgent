---
name: resume-writer
description: "基于 MiniCLIAgent 项目生成定制化简历项目经历。结合项目技术亮点与用户目标岗位，按简历编写原则输出高质量项目描述（中英文）。Use when user says '写简历', 'resume', '简历', 'write resume', '项目经历', 'project experience', '简历项目', or asks to generate resume content based on this project."
---

# Resume Writer

基于"写作原则 + 项目亮点 + 用户画像 = 定制化简历"三角模型生成简历项目经历。

## 工作流程

### Phase 1: 加载知识

1. 读取 [references/resume_principles.md](references/resume_principles.md) — 四段式结构、技术标签、亮点挖掘策略、常见误区
2. 读取 [references/project_highlights.md](references/project_highlights.md) — 9 大技术亮点（含话术方向和量化角度）
3. 按需深读 `dev_spec.md`、`code_spec.md` 对应章节或源码补充模块细节

### Phase 2: 用户画像采集

用 `AskUserQuestion` 一次性收集（最多 4 个问题）：

**问题 1 — 目标岗位**（单选）：
- Agent Engineer / Backend Engineer (Python) / LLM Application Engineer / 全栈 AI Engineer
- 决定：技术关键词策略、亮点筛选优先级

**问题 2 — 项目包装方向**（自由文本，无预设选项）：
- 引导用户描述想把项目包装成什么场景。例如："想强调 Agent 工程能力"、"想往多 Agent 协作方向靠"、"想展示底层系统设计能力"、"作为通用 Agent Harness 框架展示"、"想强调记忆/上下文系统"
- 决定：背景段落叙事、项目名称建议、亮点侧重

**问题 3 — 技术侧重**（多选）：
- Agent Runtime / 记忆检索系统 / 上下文管理 / MCP 协议 / Team 协作 / Task+Worktree / 工程化(TDD) / 降级架构
- 决定：哪 3-5 个亮点写入 bullet points

**问题 4 — 特殊要求**（自由文本）：
- 示例："往 Agent 方向靠""强调系统设计""中英双版本""5 条 bullet 以内""量化指标建议帮我给"
- 如用户填写了量化指标需求，在 Phase 3 自动建议合理数值

### Phase 3: 内容生成

#### 3.1 亮点匹配

从 `project_highlights.md` 按岗位筛选 3-5 个亮点：

| 岗位方向 | 优先亮点 |
|---------|---------|
| Agent Engineer | 亮点1(Agent Runtime) → 5(Team) → 2(记忆检索) → 3(上下文) → 4(MCP) |
| Backend / 架构 | 亮点1(Agent Runtime) → 9(降级架构) → 8(工程化) → 3(上下文) → 4(MCP) |
| LLM App Engineer | 亮点2(记忆检索) → 3(上下文) → 1(Agent Runtime) → 8(工程化) |
| 全栈 AI | 亮点1(Agent Runtime) → 2(记忆检索) → 4(MCP) → 6(Task+Worktree) → 8(工程化) |

用户的"技术侧重"多选结果优先覆盖默认排序。

#### 3.2 四段式内容生成

严格遵循 `resume_principles.md` 的**四段式结构**（背景 → 目标 → 过程 → 结果）：

##### 段 1：背景

**必须基于用户在 Q2 提供的包装方向来撰写**。模式：`在[Agent/Coding Agent 方向]中，[具体痛点]导致[具体问题]，[现有方案]无法满足[具体需求]。`

##### 段 2：目标

模式：`为解决[问题]，设计并实现[系统]，具备[核心能力]，达成[预期效果]。`

##### 段 3：过程（Bullet Points）

4-6 条 bullet，每条遵循：
1. **动词开头**：设计 / 实现 / 构建 / 优化 / 集成 / 主导
2. **三段式**：做了什么 → 用了什么技术 → 达成什么效果
3. **夹带关键词**：从技术标签表中选取岗位匹配关键词
4. **量化收尾**：每条附带数字（子系统数 / 测试用例数 / 工具数 / 协议类型数）

##### 段 4：结果

集中展示 3-5 个核心量化指标。模式：`项目完成后，[指标 1]，[指标 2]，[指标 3]。`

#### 3.3 量化指标

基于 MiniCLIAgent 项目实际数据：

| 指标 | 实际数据 |
|------|---------|
| 子系统 | 12 个 |
| 内置工具 | 12+ (bash/read/write/edit/skill/task/team/worktree/background/memory_search) |
| 测试文件 | 55 个 |
| 测试用例 | 139 个 |
| 测试代码量 | 3112 行 (> 源码 2983 行) |
| 源码文件 | 68 个 Python 文件 |
| 协议消息类型 | 6+ (shutdown/plan_approval/task_claim) |
| 记忆检索算法 | 3 种 (BM25 + Dense + Hybrid) |
| 降级路径 | 3 条 |

### Phase 4: 输出格式

```
**[MiniCLIAgent]** | [时间段] | [角色]

**背景**：[2-3 句]

**目标**：[1-2 句]

**过程**：
• [Bullet 1] — 动词开头 + 技术细节 + 效果
• [Bullet 2] — 动词开头 + 工具/方法 + 量化
• [Bullet 3] — 动词开头 + 实践 + 数据
• [Bullet 4] — 动词开头 + 指标 + 影响
• [Bullet 5：可选]

**结果**：[2-3 句汇总量化指标]

**技术栈**：[关键词列表]
```

约束：四段缺一不可，过程段 4-6 条 bullet，每条 ≤ 80 字，结果段 ≥ 3 个量化指标。

### Phase 5: 迭代与面试准备

1. 展示初稿，询问反馈
2. 主动提供面试追问预测（3-5 条），例如：
   - "BM25 的 k1/b 参数怎么选的？为什么用 min-max 归一化而不是 RRF？"
   - "ContextManager 三层压缩分别在什么阈值触发？怎么验证不丢关键信息？"
   - "MCP 客户端怎么处理 tool 名称冲突？"
   - "Team Protocol 的 request_id 怎么关联请求和响应？"
   - "为什么选 Markdown-first 而不是 SQLite 做记忆存储？"

## 放大策略

| 维度 | 允许 | 禁止 |
|------|------|------|
| 业务场景 | 包装为真实 Agent 工程场景 | 伪造公司名/产品名 |
| 量化指标 | 使用项目实际数据 | 脱离项目能力的夸大 |
| 角色 | "设计并主导实现" | 虚构团队规模 |
| 技术深度 | 强调决策与判断力 | 编造未实现的功能 |

**底线**：不声称使用了项目中未实现的技术，不声称完成了标记为"非目标"的功能。

## 反模式检查

- 泛化描述（"负责 Agent 系统开发"）
- 工具堆砌（列工具名不解释作用）
- 缺失量化结果
- 被动语态（"参与"、"协助"）
- 自我矮化（"只是 demo"、"小项目"）
