[← README](../README_cn.md) · [English](troubleshooting.md)

# 常见问题

## 🛠️ 一句话答案

- **Windows 10：在安装窗口里登录不了 Claude。** 改在 Windows Terminal 里运行安装程序：打开一个命令提示符标签页，把 `Durweg-Install.bat` 拖进去，按回车（[详细步骤](#windows-10在安装窗口里登录不了-claude)）。
- **装好 Durweg 以后才装了另一个 agent（比如先有 Codex，后装 Claude Code）：** 新装的 agent 还不会用 Durweg。再运行一次安装程序，问要不要修改时按回车，它会给电脑上所有的 agent 都装上 Durweg。
- **agent 已经装了，安装程序却说没有找到：** 你的 agent 不在系统能直接找到的位置（比如要用一个脚本启动）。在“要装哪一个”时选 **3**：Durweg 会装好给 Claude Code 和 Codex 用的部分，你照平常的方式启动 agent，对它说“用 durweg 运行 write-your-method”。
- **Mac：安装程序说需要 Python 3.9 或更新，可电脑上明明有新的：** 终端里排在前面的是一个旧的 Python（比如 Anaconda 自带的 3.8）。让它不再自动打开，再运行一次安装程序就行，不用重装 Python（[详细步骤](#mac安装程序说需要-python-39-或更新)）。

## Windows 10：在安装窗口里登录不了 Claude

Windows 10 的旧式命令行窗口显示不好现代的命令行程序，Claude Code 的登录界面在里面会显示错乱或卡住。不用改 Durweg，换一个窗口运行安装程序即可：

1. 没有 Windows Terminal 的话，先从 Microsoft Store 安装它。
2. 打开 Windows Terminal。
3. 打开一个**命令提示符**标签页：点标签旁边的 ˅，选“命令提示符”。
4. 把 `Durweg-Install.bat` 拖进窗口，按回车。

如果你用的是 PowerShell 标签页，要先输入 `& `（& 加一个空格），再把文件拖进去，按回车；不加的话 PowerShell 只会把路径打印出来。

## Mac：安装程序说需要 Python 3.9 或更新

Durweg 用的是终端最先找到的那个 `python3`。如果你装过 Anaconda，或者从 python.org 装过旧版 Python，它会排在 Mac 自带的 Python 前面。不用重装 Python：

1. 打开终端，运行 `/usr/bin/python3 --version`。
   - **3.9 或更新：** Mac 自带的 Python 没问题，接着做第 2 步。
   - **3.7 或 3.8：** 你的开发者工具太旧了。在“系统设置 → 通用 → 软件更新”里更新 “Command Line Tools”，再做第 2 步。
2. 运行 `which python3`，看排在最前面的是哪个 Python：

   | 路径里有 | 怎么做 |
   | :--- | :--- |
   | `anaconda3` 或 `miniconda3` | 运行 `conda config --set auto_activate_base false`。Conda 还在，要用时 `conda activate` 打开它 |
   | `/Library/Frameworks/Python.framework` | 用文本编辑器打开 `~/.zprofile`，在把旧 Python 加进 `PATH` 的那几行前面加 `#` |

3. 关掉终端，重新打开。`python3 --version` 应该显示 3.9 或更新。
4. 再双击一次 `Durweg-Install.command`。
