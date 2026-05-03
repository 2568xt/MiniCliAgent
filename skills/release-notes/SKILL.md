---
name: release-notes
description: Use when preparing a release summary changelog entry or what changed report from git history and local diffs 也适用于版本说明与发版摘要整理
---

# Release Notes

目标：基于真实 git 历史产出一版可直接发出的变更摘要。

## 取数顺序

1. 用 `bash` 确定范围：
   - `git tag --sort=-creatordate`
   - `git log --oneline --decorate -20`
   - `git diff --stat <from>..<to>`
2. 如果没有 tag，就和用户确认范围，或者默认用最近一次 release commit 到 `HEAD`。
3. 把 commit、diff、README 变化、测试变化合并理解，不要只抄 commit message。

## 建议分类

- `Highlights`
- `Fixes`
- `Developer Experience`
- `Docs`
- `Breaking Changes`

## 写作要求

- 用用户能理解的语言描述结果，不要把内部实现细节原样倒出来
- 真正的 breaking change 要单独拎出
- 不确定的地方标成 `Needs Confirmation`
- 用户要求落盘时，再用 `write_file` 写到目标文档

## 常见坑

- 把未发布的实验提交写进正式 notes
- 把重构描述成用户可感知能力
- 漏掉迁移步骤、配置项变更或测试基线变化
