[← README](../README.md) · [中文](README_cn.md)

# 📚 Durweg docs

[🧭 Start](#-start) · [🙋 I want to …](#-i-want-to-) · [📄 All pages](#-all-pages)

## 🧭 Start

| Page | What it is for |
| :--- | :--- |
| [What Durweg does](features.md) | the two cores and what you get from each feature |
| [Install Durweg](install.md) | system requirements, the three ways to install, the questions the installer asks |
| [Every day](every-day.md) | open a terminal, go to your project, start your agent, say what to run |
| [Example: write down your method](example.md) | your first workflow from scratch, with a real case |

## 🙋 I want to …

| I want to | How |
| :--- | :--- |
| Write a workflow by hand | [workflow format](workflow-format.md) |
| Check a run | `durweg check <run folder>` |
| Change the language | `durweg config language en` (or `zh`) |
| Install somewhere else (on Windows: into WSL) | Run the installer again and type `c` when it asks whether to change Durweg |
| Compare a run with the agent's own session files | The optional plugin [durweg-audit](https://github.com/durweg/durweg-audit) |
| Find my settings, cases and run records | [Where your files are](files.md) |
| Install a ready-made workflow | Tell your agent "Show me the durweg workflows I can install", then `durweg library add <name>` ([catalogs](workflow-format.md#catalogs)) |
| Browse, add and update workflows in your browser instead of typing commands | `durweg ui` ([the management page](ui.md)) |
| Update Durweg and the workflows you installed | • `durweg update` ([updating](update.md))<br>• As a Claude Code plugin: Durweg itself with `/plugin update durweg` ([plugin](install-plugin.md#-updating-and-removing)) |
| Share a workflow of yours (on GitHub, public or private) | Tell your agent "Publish <name> with durweg" ([publishing](publish.md)) |
| Remove Durweg | • `durweg uninstall`: keeps `~/Durweg` and your runs ([uninstall](uninstall.md))<br>• As a Claude Code plugin: `/plugin uninstall durweg` |

## 📄 All pages

| Page | Kind |
| :--- | :--- |
| [What Durweg does](features.md) | explanation |
| [Install Durweg](install.md) · [as a Claude Code plugin](install-plugin.md) · [as a Codex plugin](install-codex-plugin.md) · [with your AI](install-with-your-ai.md) | how-to |
| [Every day](every-day.md) | how-to |
| [Example: write down your method](example.md) | tutorial |
| [Workflow format](workflow-format.md) | reference |
| [Publishing a workflow of yours](publish.md) (public and private) | how-to |
| [The management page (`durweg ui`)](ui.md) | how-to |
| [Updating](update.md) · [Uninstalling](uninstall.md) | how-to |
| [Where your files are](files.md) | reference |
| [Common problems](troubleshooting.md) | troubleshooting |
