---
name: plan-grill
description: Use when a plan design or implementation approach needs pressure testing before coding and when the user asks to challenge assumptions find blind spots or review risks 也适用于方案评审与风险检查
---

# Plan Grill

目标：在动手之前，把方案里的隐含假设、缺失约束和高风险点挑出来。

## 什么时候用

- 用户说“帮我 challenge 一下方案”
- 用户给了实现思路，但还没写代码
- 需求看起来简单，但改动面可能不止一个模块
- 需要在 `spec -> plan -> implementation` 之间补一轮风险审视

## 工作方式

1. 先用现有上下文判断哪些问题已经能从代码库得到答案。
2. 能自己验证的，优先用 `bash`、`read_file`、`rg` 查证，不把本可确认的问题丢回给用户。
3. 仍然不清楚的风险点，一次只追一个关键问题。
4. 覆盖下面五个角度：
   - 目标是否清晰
   - 约束是否明确
   - 边界和失败模式是否定义
   - 验证方式是否可执行
   - 有没有更小、更稳的落地路径

## 输出结构

按下面顺序给结论：

1. `Most Likely Gaps`：最可能漏掉的点
2. `Failure Modes`：最可能出问题的路径
3. `Recommended Shape`：建议采用的实现形状
4. `Open Questions`：必须补齐的少量问题

## MiniCLIAgent 提示

- 方案较大时，用 `task_create` 拆成可跟踪事项。
- 风险高但范围可隔离时，用 `worktree_create` 先开独立工作区验证。
- 不要把它做成泛泛而谈的头脑风暴。每条质疑都要对应具体行为、模块、数据流或验证动作。
