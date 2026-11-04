[← README](../README_cn.md) · [English](install.md)

# 安装 Durweg

## 💻 系统要求

| 你的电脑 | 需要什么 |
| :--- | :--- |
| **Windows** | • Windows 10 或 11<br>• Python 3.9 或更新；没有的话，安装程序会帮你装 Python 3.12 |
| **Mac** | • `/usr/bin/python3` 是 Python 3.9 或更新：它来自苹果的开发者工具（Command Line Tools），没有的话安装程序会让 macOS 装上<br>• 旧的开发者工具带的是 Python 3.7 或 3.8：用 `/usr/bin/python3 --version` 查看，低于 3.9 就在“系统设置 → 通用 → 软件更新”里更新它 |
| **Linux** | • Python 3.9 或更新、`curl` 和 `tar`<br>• Debian 或 Ubuntu 上，缺的东西安装程序会帮你装（sudo 会要你的系统密码） |

## 🧭 安装

**三种方式，选一种就行（不是先后几步）。** 装好的 Durweg 和 `~/Durweg` 文件夹都一样。

| 你的情况 | 用哪种 |
| :--- | :--- |
| 已经在用 Claude Code | [方式 A：装成 Claude Code 插件](install_cn.md#方式-a装成-claude-code-插件) |
| 已经在用 Codex（Mac、Linux 或 WSL） | [方式 B：装成 Codex 插件](install_cn.md#方式-b装成-codex-插件) |
| 电脑上还没有 AI agent，在 Windows 本身上用 Codex，或者用 Antigravity | [方式 C：用安装程序](install_cn.md#方式-c用安装程序) |

### 方式 A：装成 Claude Code 插件

如果你已经在用 Claude Code（Windows、Mac、Linux、WSL 都行），并且有 Python 3.9 或更新版本和 git：

1. 在 Claude Code 里输入 `/plugin install durweg --marketplace durweg/durweg`。
2. 输入 `/reload-plugins`。
3. 对 Claude 说：`Run write-your-method with durweg.` 它会先问你用哪种语言，然后开始[案例](example_cn.md)。

更新、卸载、旧版 Claude Code 怎么装：见[把 Durweg 装成 Claude Code 插件](install-plugin_cn.md)。

✅ 装好了：下面的方式 B 和 C 不用看，接着看[每天怎么用](every-day_cn.md)。

### 方式 B：装成 Codex 插件

如果你已经在用 Codex CLI（Mac、Linux 或 WSL），并且有 Python 3.9 或更新版本和 git：

1. 在终端里（不是在 Codex 里）运行 `codex plugin marketplace add durweg/durweg`。
2. 运行 `codex plugin add durweg@durweg`。
3. 新开一个 Codex 会话，对它说：`Run write-your-method with durweg.`

Codex 的沙盒里 `~/Durweg` 是只读的，所以往那里写的命令会请你批准。详细说明、更新和卸载：见[把 Durweg 装成 Codex 插件](install-codex-plugin_cn.md)。

✅ 装好了：下面的方式 C 不用看，接着看[每天怎么用](every-day_cn.md)。

### 方式 C：用安装程序

Windows、Mac、Linux 都能用，电脑上还没有 AI agent 也可以。

> 🤖 **嫌麻烦？** 把这句话发给你电脑上的 AI（Claude Code、Codex 等）：
>
> `请按 https://github.com/durweg/durweg/blob/main/docs/install-with-your-ai.md 帮我安装 Durweg。`
>
> 它会自己判断你的电脑、运行安装程序；装好以后，重新启动你的 AI。网页上的聊天 AI 碰不到你的电脑，装不了。

不需要 GitHub 账号。需要 Claude Code 或 Codex 的账号（用量算在你自己的套餐里）；电脑上还没有 agent 的，安装程序会帮你装。已经装了 Antigravity 的，它也会一起用上 Durweg。

**运行安装程序**（按你的电脑选一行）：

| 你的电脑 | 怎么做 |
| :--- | :--- |
| **Windows**<br>（不管有没有 WSL） | • 下载 [`Durweg-Install.bat`](https://github.com/durweg/durweg/releases/latest/download/Durweg-Install.bat)，在 Windows 里双击<br>• 想装进 WSL 也用它：在安装程序里选 WSL，不用自己打开 WSL 输命令 |
| **Mac** | 下载 [`Durweg-Install-macOS.zip`](https://github.com/durweg/durweg/releases/latest/download/Durweg-Install-macOS.zip)，解压后双击 `Durweg-Install.command` |
| **Linux**<br>（不是 Windows 里的 WSL） | 在终端里运行：<br>`curl -fsSL https://raw.githubusercontent.com/durweg/durweg/v1.8.0/install.sh \| bash` |

安装程序先问语言，Windows 上再问装在哪里（Windows 还是 WSL），然后自动装好，在浏览器里打开这个页面，启动你的 agent；它先问你要不要现在一起做[案例](example_cn.md)，不想做就说不要，它会告诉你以后怎么开始。途中遇到的每个提问怎么答：见本页最后的[安装时会遇到的提问](install_cn.md#-安装时会遇到的提问)。

## 💬 安装时会遇到的提问

| 提问 | 怎么选 |
| :--- | :--- |
| **语言** | 选你要 agent 用的语言；以后可以用 `durweg config language` 改 |
| **装在哪里**（Windows） | • 一般选 **Windows**<br>• 也想用需要 Linux 的工作流，选 **WSL**（Windows 里的 Linux） |
| **还没有 WSL** | • 同意管理员授权，重启电脑<br>• 从开始菜单打开一次 "Ubuntu"，设好 Linux 用户名和密码<br>• 再双击一次安装程序；之前的选择它都记着 |
| **“Windows 已保护你的电脑”** | 点 **更多信息 → 仍要运行** |
| **macOS 拦下了安装程序** | • 打开“系统设置 → 隐私与安全性”，点允许<br>• macOS 先装开发者工具的话，等它装完再双击一次 |
| **装 Claude Code 还是 Codex** | • 只在电脑上找不到 agent 时才问；直接回车装 Claude Code，装好以后在浏览器里登录一次<br>• 已经装了 agent、平时用自己的方式（比如一个脚本）启动它：选 **3**，不装新的 |
| **再次运行时问要不要修改** | • 回车：沿用上次的选择（更新或修复）<br>• 输入 `c`：重新选择，重新安装 |
