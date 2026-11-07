[English](README.md) · [中文](README_cn.md)

# Durweg

[💻 Requirements](#-system-requirements) · [🧭 Install](#-install) · [🚀 First run](#-first-run) · [🙋 What you can do](#-what-you-can-do) · [🛠️ Common problems](#%EF%B8%8F-common-problems) · [🙏 Thanks](#-special-thanks) · **[📚 Workflows you can install](https://github.com/durweg/durweg-workflows)**

**Durweg lets the AI agents you already use do what you need on their own, in your own way of working: you write your method down once as a workflow, and the work runs through it step by step; you are asked only where you chose, to decide, to do something yourself or to accept a result.**

At its core are **workflows**: your way of working as steps, each checked before the next one starts. The agent stops only at the steps where you want to confirm, and keeps a record of every run. Start with `Run write-your-method with durweg.` ([first run](#-first-run)).

Durweg calls no model API: the work is done in the Claude Code or Codex sessions you have open. More on each feature: [What Durweg does](docs/features.md).

## 💻 System requirements

| Your computer | What it needs |
| :--- | :--- |
| **Windows** | Windows 10 or 11; Python 3.9 or newer (the installer adds it if missing) |
| **Mac** | Python 3.9 or newer at `/usr/bin/python3` (Apple's developer tools; [details](docs/install.md#-system-requirements)) |
| **Linux** | Python 3.9 or newer, `curl` and `tar` |

## 🧭 Install

**Three ways: pick one (they are not steps in a row).** All give you the same Durweg.

| Your situation | Use |
| :--- | :--- |
| You already use Claude Code | the steps below (a Claude Code plugin) |
| You already use Codex (Mac, Linux or WSL) | [as a Codex plugin](docs/install.md#option-b-as-a-codex-plugin) |
| No AI agent yet, Codex on Windows itself, or Antigravity | [the installer](docs/install.md#option-c-with-the-installer) |

As a Claude Code plugin (Windows, Mac, Linux or WSL, with Python 3.9 or newer and git):

1. Open a terminal and start Claude Code: `claude`.
2. Type `/plugin install durweg --marketplace durweg/durweg`.
3. Type `/reload-plugins`.

All three ways, the questions the installer asks, updating and removing: [Install Durweg](docs/install.md).

## 🚀 First run

Tell your agent: `Run write-your-method with durweg.` It asks which language you want, then helps you write down one way you work (for example a weekly report) as a workflow, runs it once and, if you like, writes it up as a case page.

Done looks like this: the agent tells you the check result is `PASS`, and "Show me my durweg workflows" lists your new workflow. From then on: "Run <name> with durweg." Step by step: [Example: write down your method](docs/example.md); how to start each day: [Every day](docs/every-day.md).

## 🙋 What you can do

| I want to | Where |
| :--- | :--- |
| run my workflows every day | [Every day](docs/every-day.md) |
| install a ready-made workflow | [catalog](https://github.com/durweg/durweg-workflows), then `durweg library add <name>` |
| share a workflow of mine, public or private | [Publishing](docs/publish.md) |
| update Durweg, or remove it | [Updating](docs/update.md) · [Uninstalling](docs/uninstall.md) |
| everything else (writing a workflow by hand, the management page, where my files are …) | [All docs](docs/README.md) |

## 🛠️ Common problems

Installer windows, an agent installed after Durweg, an older Python on a Mac: [Common problems](docs/troubleshooting.md).

## 🙏 Special thanks

Thanks to [moraywang95-svg](https://github.com/moraywang95-svg) and [Qizhe-Xu](https://github.com/Qizhe-Xu) for helping me shape the idea of Durweg, testing it and giving feedback while it was being made 😊

---

License: [MIT](LICENSE).
