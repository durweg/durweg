[← README](../README_cn.md) · [English](every-day.md)

# 每天怎么用

1. **打开终端。** Windows：打开 Windows Terminal（Durweg 装在 WSL 里的话，从开始菜单打开 "Ubuntu"）。Mac 或 Linux：打开“终端”。
2. **进入你的项目文件夹：** `cd ~/projects/my-project`（Windows 本机上如 `cd C:\Users\<你>\projects\my-project`）。每次运行的记录都放在这个文件夹的 `runs/` 里。
3. **启动 agent：** 输入 `claude`（Claude Code）或 `codex`（Codex），按回车。
4. **告诉它要做什么：**
   - 运行一个工作流：“用 durweg 运行 weekly-report”。它一步一步执行，某一步的检查没过就停下，在你的方法要你拍板的地方问你。
   - 新建一个工作流：“用 durweg 运行 write-your-method”（就是[案例](example_cn.md)里的那个引导）。
   - 看看有哪些工作流：“列出我的 durweg 工作流”。
