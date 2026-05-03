---
name: systematic-debugging
description: Use when a command test feature or workflow is failing flaky regressed or behaving unexpectedly and when the user asks to debug reproduce or find root cause 也适用于测试失败与线上回归排查
---

# Systematic Debugging

目标：先稳定复现，再缩小范围，最后用最小改动修掉根因。

## 基本流程

1. **抓住失败信号**
   - 先记录报错、退出码、失败用例、输入条件。
   - 用 `bash` 复现一次，不要一上来就改代码。
2. **缩小搜索面**
   - 用 `rg -n` 找错误文本、关键函数、最近相关模块。
   - 用 `git diff`, `git log --oneline`, `git blame` 看最近变更。
3. **确认根因**
   - 区分“症状”和“根因”。
   - 如果有多个猜测，逐个排除，不同时改两处以上。
4. **最小修复**
   - 优先局部补丁，避免借排障顺手做大重构。
   - 需要多步时，用 `task_create`/`task_update` 跟踪。
5. **回归验证**
   - 复跑最小失败命令。
   - 再跑受影响范围内最关键的一组测试或命令。

## 常用动作

- 复现：`bash`
- 定位：`rg`, `read_file`
- 修补：`edit_file`, `write_file`
- 长命令：`background_run`, `background_check`

## 输出格式

- `Symptom`
- `Root Cause`
- `Fix`
- `Verification`
- `Residual Risk`

## 约束

- 没复现前，不宣称“已经定位”。
- 没验证前，不宣称“已经修复”。
- 如果问题可能污染主工作区，先用 `worktree_create` 做隔离验证。
