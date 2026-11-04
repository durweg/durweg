[English](README.md) · [中文](README_cn.md)

# Durweg

[💻 系统要求](#-系统要求) · [🧭 安装](#-安装) · [🚀 第一次运行](#-第一次运行) · [🙋 你能做什么](#-你能做什么) · [🛠️ 常见问题](#%EF%B8%8F-常见问题) · [🙏 特别感谢](#-特别感谢) · **[📚 可以安装的工作流](https://github.com/durweg/durweg-workflows)**

**Durweg 让你已经在用的 AI agent 按你自己的做法，把你要的事自动做完：你把方法写成一次工作流，以后的活就一步一步照着走；只在你选定的地方来找你——要你定、要你亲手做，或者要你验收。**

它有两个核心：

| 核心 | 做什么 | 从哪开始 |
| :--- | :--- | :--- |
| **工作流** | • 你的做法写成步骤，每一步检查通过才往下走<br>• 只在你要确认的那几步停下来，每次运行都有记录 | `用 durweg 运行 write-your-method。`（[第一次运行](#-第一次运行)） |
| **自动化** | • 需求变成你自己看板（私有 GitHub Project）上的卡，agent 一张接一张做，每张由另一个 agent 审<br>• 要你定、要你做、要你验收的，停在那里等你回来 | 插件 [durweg-todo](https://github.com/durweg/durweg-todo) |

Durweg 不调用模型 API：活在你开着的 Claude Code 或 Codex 会话里做。每个特点详细说明：[Durweg 能做什么](docs/features_cn.md)。

## 💻 系统要求

| 你的电脑 | 需要 |
| :--- | :--- |
| **Windows** | Windows 10 或 11；Python 3.9 或更新（没有的话安装程序会装） |
| **Mac** | `/usr/bin/python3` 是 Python 3.9 或更新（苹果开发者工具带的；[详细](docs/install_cn.md#-系统要求)） |
| **Linux** | Python 3.9 或更新、`curl` 和 `tar` |

## 🧭 安装

**三种方式，选一种（不是要依次做的步骤）。** 装好的都是同一个 Durweg。

| 你的情况 | 用 |
| :--- | :--- |
| 已经在用 Claude Code | 下面的步骤（装成 Claude Code 插件） |
| 已经在用 Codex（Mac、Linux 或 WSL） | [装成 Codex 插件](docs/install_cn.md#方式-b装成-codex-插件) |
| 还没有 AI agent、在 Windows 本身上用 Codex，或用 Antigravity | [安装程序](docs/install_cn.md#方式-c用安装程序) |

装成 Claude Code 插件（Windows、Mac、Linux 或 WSL，需要 Python 3.9 或更新和 git）：

1. 打开终端，启动 Claude Code：`claude`。
2. 输入 `/plugin install durweg --marketplace durweg/durweg`。
3. 输入 `/reload-plugins`。

三种方式的全部步骤、安装程序会问什么、更新和卸载：[安装 Durweg](docs/install_cn.md)。

## 🚀 第一次运行

对 agent 说：`用 durweg 运行 write-your-method。` 它先问你要用哪种语言，然后帮你把一种做法（比如写周报）写成工作流，运行一次；你愿意的话，再写成一页案例。

做完的样子：agent 告诉你检查结果是 `PASS`，问它“列出我的 durweg 工作流”能看到你的新工作流。以后就说：“用 durweg 运行 <名字>。” 一步一步的说明：[案例：写下你的方法](docs/example_cn.md)；每天怎么开始：[每天怎么用](docs/every-day_cn.md)。

## 🙋 你能做什么

| 我想 | 去哪看 |
| :--- | :--- |
| 每天运行我的工作流 | [每天怎么用](docs/every-day_cn.md) |
| 让 agent 按看板干活，只在需要时找我 | [durweg-todo](https://github.com/durweg/durweg-todo) |
| 装一个现成的工作流 | [目录](https://github.com/durweg/durweg-workflows)，然后 `durweg library add <名字>` |
| 分享我的工作流，公开或私密 | [发布](docs/publish_cn.md) |
| 更新或卸载 Durweg | [更新](docs/update_cn.md) · [卸载](docs/uninstall_cn.md) |
| 其他（手写工作流、管理页、文件在哪……） | [全部文档](docs/README_cn.md) |

## 🛠️ 常见问题

安装窗口、装好 Durweg 后才装的 agent、Mac 上旧的 Python：[常见问题](docs/troubleshooting_cn.md)。

## 🙏 特别感谢

感谢 [moraywang95-svg](https://github.com/moraywang95-svg) 和 [Qizhe-Xu](https://github.com/Qizhe-Xu) 在 Durweg 做出来的过程中帮我把概念成型、测试，还有提意见 😊

---

MIT 许可证：[LICENSE](LICENSE)。
