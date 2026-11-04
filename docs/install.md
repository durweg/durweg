[← README](../README.md) · [中文](install_cn.md)

# Install Durweg

## 💻 System requirements

| Your computer | What it needs |
| :--- | :--- |
| **Windows** | • Windows 10 or 11<br>• Python 3.9 or newer; if it is missing, the installer installs Python 3.12 for you |
| **Mac** | • Python 3.9 or newer at `/usr/bin/python3`; it comes with Apple's developer tools (Command Line Tools), which the installer asks macOS to install if they are missing<br>• Older developer tools bring Python 3.7 or 3.8; check with `/usr/bin/python3 --version` and, if it is older than 3.9, update them in System Settings → General → Software Update |
| **Linux** | • Python 3.9 or newer, `curl` and `tar`<br>• On Debian or Ubuntu the installer installs what is missing (sudo asks for your password) |

## 🧭 Install

**Three ways: pick one (they are not steps in a row).** All give you the same Durweg and the same `~/Durweg` folder.

| Your situation | Use |
| :--- | :--- |
| You already use Claude Code | [Option A: as a Claude Code plugin](install.md#option-a-as-a-claude-code-plugin) |
| You already use Codex (on Mac, Linux or WSL) | [Option B: as a Codex plugin](install.md#option-b-as-a-codex-plugin) |
| No AI agent on your computer yet, Codex on Windows itself, or Antigravity | [Option C: with the installer](install.md#option-c-with-the-installer) |

### Option A: as a Claude Code plugin

If you already use Claude Code (on Windows, Mac, Linux or WSL) and have Python 3.9 or newer and git:

1. In Claude Code, type `/plugin install durweg --marketplace durweg/durweg`.
2. Type `/reload-plugins`.
3. Tell Claude: `Run write-your-method with durweg.` It first asks which language you want, then
   starts the [example](example.md).

Updating, removing and an older Claude Code:
[Installing Durweg as a Claude Code plugin](install-plugin.md).

✅ Done: skip Options B and C below and go on with [Every day](every-day.md).

### Option B: as a Codex plugin

If you already use the Codex CLI (on Mac, Linux or WSL) and have Python 3.9 or newer and git:

1. In a terminal (not inside Codex), run `codex plugin marketplace add durweg/durweg`.
2. Run `codex plugin add durweg@durweg`.
3. Start a new Codex session and tell it: `Run write-your-method with durweg.`

Codex keeps `~/Durweg` read-only in its sandbox, so it asks you to approve the commands that write
there. Details, updating and removing: [Installing Durweg as a Codex plugin](install-codex-plugin.md).

✅ Done: skip Option C below and go on with [Every day](every-day.md).

### Option C: with the installer

For Windows, Mac and Linux, also when you have no AI agent yet.

> 🤖 **Rather not do it yourself?** Send this to the AI on your computer (Claude Code, Codex …):
>
> `Please install Durweg for me as described in https://github.com/durweg/durweg/blob/main/docs/install-with-your-ai.md`
>
> It finds out which computer you have and runs the installer; when it is done, start your AI again. An AI chat in the browser cannot reach your computer and cannot do this.

You need no GitHub account. You need an account for Claude Code or Codex (use counts against your
own plan); if neither is on your computer yet, the installer installs one. If you have Antigravity, it gets
Durweg too.

**Run the installer** (pick the row for your computer):

| Your computer | What to do |
| :--- | :--- |
| **Windows**<br>(with or without WSL) | • Download [`Durweg-Install.bat`](https://github.com/durweg/durweg/releases/latest/download/Durweg-Install.bat) and double-click it in Windows<br>• To install into WSL, use it too and choose WSL in the installer; you do not open WSL or type commands yourself |
| **Mac** | Download [`Durweg-Install-macOS.zip`](https://github.com/durweg/durweg/releases/latest/download/Durweg-Install-macOS.zip), unzip it and double-click `Durweg-Install.command` |
| **Linux**<br>(not WSL on Windows) | In a terminal, run:<br>`curl -fsSL https://raw.githubusercontent.com/durweg/durweg/v1.8.0/install.sh \| bash` |

The installer asks for your language first (on Windows also where to install: Windows or WSL),
sets everything up, opens this page in your browser, starts your agent, which first asks whether to walk you through the [example](example.md) now; say no, and it tells you how to start it later.
What to answer at each question on the way: see [Questions during installation](install.md#-questions-during-installation)
at the end of this page.

## 💬 Questions during installation

| Question | What to choose |
| :--- | :--- |
| **Language** | The language your agent will use; change it later with `durweg config language` |
| **Where to install** (Windows) | • Usually **Windows**<br>• **WSL** (Linux inside Windows) if you also want workflows that need Linux |
| **No WSL yet** | • Approve the administrator prompt and restart<br>• Open "Ubuntu" from the Start menu once to choose a Linux user name and password<br>• Double-click the installer again; it remembers your choices |
| **"Windows protected your PC"** | Click **More info → Run anyway** |
| **macOS blocked the installer** | • Open System Settings → Privacy & Security and allow it<br>• If macOS installs its developer tools first, double-click the file again when that has finished |
| **Claude Code or Codex** | • Asked only when no agent is found; press Enter for Claude Code, then log in to it once in your browser<br>• You already have an agent and start it your own way (for example with a script): choose **3**; nothing new is installed |
| **Asked on a second run whether to change Durweg** | • Enter: keep the last choices (update or repair)<br>• `c`: choose again and install Durweg anew |
