---
name: readme-refresh
description: Use when a repository README is missing outdated inconsistent with the current codebase or needs a demo-ready refresh 也适用于补齐快速开始和命令说明
---

# README Refresh

目标：把 README 调整成“新人五分钟能跑通、演示时一眼能看懂”的状态。

## 工作顺序

1. 先读现有 `README.md`。
2. 再读真正 authoritative 的文件：
   - 入口命令
   - `pyproject.toml` 或 `package.json`
   - 关键测试文件
   - 配置与环境变量定义
3. 用代码库事实修正文档，不凭空发明命令、脚本或能力。

## 建议覆盖的段落

- 项目是干什么的
- 最小启动步骤
- 关键命令
- 环境变量
- 测试方式
- 目录结构
- 常见演示路径

## MiniCLIAgent 提示

- 需要核实命令时先用 `bash --help` 或实际执行只读命令。
- 大段改写前先用 `read_file` 提取当前结构，再用 `edit_file` 做局部更新。
- 如果 README 明显落后于代码，优先修“会误导用户”的部分。

## 验收标准

- README 里的命令在仓库里都找得到依据
- 路径、模块名、环境变量与代码一致
- 读者不用翻很多源码就能开始使用或演示
