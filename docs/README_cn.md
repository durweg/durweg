[← README](../README_cn.md) · [English](README.md)

# 📚 Durweg 文档

[🧭 开始](#-开始) · [🙋 我想……](#-我想) · [📄 全部页面](#-全部页面)

## 🧭 开始

| 页面 | 用来做什么 |
| :--- | :--- |
| [Durweg 能做什么](features_cn.md) | 每个特点能给你什么 |
| [安装 Durweg](install_cn.md) | 系统要求、三种安装方式、安装时会遇到的提问 |
| [每天怎么用](every-day_cn.md) | 打开终端、进项目文件夹、启动 agent、说要运行什么 |
| [案例：写下你的方法](example_cn.md) | 从头做第一个工作流，附一个真实案例 |

## 🙋 我想……

| 我想 | 怎么做 |
| :--- | :--- |
| 手写一个工作流 | [工作流格式](workflow-format_cn.md) |
| 核对一次运行 | `durweg check <运行文件夹>` |
| 改语言 | `durweg config language zh`（或 `en`） |
| 装到别的地方（在 Windows 上改装进 WSL） | 再运行一次安装程序，它问要不要修改时输入 `c` |
| 把一次运行和 agent 自己的会话记录对照 | 可选插件 [durweg-audit](https://github.com/durweg/durweg-audit) |
| 找到我的设置、案例和运行记录 | [文件放在哪里](files_cn.md) |
| 装一个别人做好的工作流 | 对 agent 说“给我看看能装哪些 durweg 工作流”，然后 `durweg library add <名字>`（[目录](workflow-format_cn.md#目录)） |
| 在浏览器里浏览、加入、更新工作流，不用敲命令 | `durweg ui`（[管理页](ui_cn.md)） |
| 更新 Durweg 和装好的工作流 | • `durweg update`（[更新](update_cn.md)）<br>• 装成 Claude Code 插件的：Durweg 本身用 `/plugin update durweg` 更新（[插件](install-plugin_cn.md#-更新和卸载)） |
| 分享你自己的工作流（放到 GitHub，公开或私有） | 对 agent 说“用 durweg 发布 <名字>”（[发布](publish_cn.md)） |
| 卸载 | • `durweg uninstall`：保留 `~/Durweg` 和你的运行记录（[卸载](uninstall_cn.md)）<br>• 装成 Claude Code 插件的：`/plugin uninstall durweg` |

## 📄 全部页面

| 页面 | 类型 |
| :--- | :--- |
| [Durweg 能做什么](features_cn.md) | 说明 |
| [安装 Durweg](install_cn.md) · [装成 Claude Code 插件](install-plugin_cn.md) · [装成 Codex 插件](install-codex-plugin_cn.md) · [让 AI 帮你装](install-with-your-ai.md)（英文） | 操作 |
| [每天怎么用](every-day_cn.md) | 操作 |
| [案例：写下你的方法](example_cn.md) | 教程 |
| [写一个工作流（格式）](workflow-format_cn.md) | 参考 |
| [发布你自己的工作流](publish_cn.md)（公开和私密） | 操作 |
| [管理页（`durweg ui`）](ui_cn.md) | 操作 |
| [更新 Durweg 和工作流](update_cn.md) · [卸载](uninstall_cn.md) | 操作 |
| [文件放在哪里](files_cn.md) | 参考 |
| [常见问题](troubleshooting_cn.md) | 排错 |
