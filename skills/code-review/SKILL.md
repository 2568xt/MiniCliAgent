---
name: code-review
description: Use when reviewing local changes pull-request-sized diffs or asking for bug security performance or test-gap analysis 也适用于帮我 review 一下代码
---

# Code Review

目标：给出按严重级别排序、可落地、带证据的 review 结论。

## 先看什么

1. 用 `bash` 看改动范围：
   - `git status --short`
   - `git diff --stat`
   - `git diff --unified=0`
   - `git log --oneline -5`
2. 用户只点名某个文件时，先 `read_file` 精读，再回头看 diff。
3. 能跑就跑最小验证：
   - 相关 `pytest`
   - 相关 lint/type check
   - 任何能直接证明行为的最小命令

## 重点检查

- `Correctness`：逻辑是否会错、边界是否漏掉
- `Regression Risk`：是否破坏现有调用方、配置或数据格式
- `Security`：命令注入、路径穿越、敏感信息泄漏、权限判断缺失
- `Performance`：不必要的全量扫描、重复 I/O、明显高复杂度
- `Maintainability`：命名、重复逻辑、异常处理、死代码
- `Tests`：关键路径是否有验证，失败路径是否覆盖

## 输出要求

- 先列 `Findings`
- 每条都给出具体位置，优先 `path + function/block`
- 说明影响，而不是只贴风格意见
- 分清严重度：`high`, `medium`, `low`
- 没发现问题时，明确说没有 blocking issue，并补充剩余测试风险

## 不该做的事

- 不把纯风格偏好包装成 bug
- 不在没有证据时臆测运行时行为
- 不因为能改就顺手重写整段实现
