[← README](../README.md) · [中文](features_cn.md)

# What Durweg does

**Turn the way you and your AI always work into a workflow: set it up once, and every new project runs on it; the AI delivers step by step, every step is checked automatically, and it stops only where you chose, so you can look at the results and confirm before it goes on.**

For example, once it is set up, every new project runs like this:

```mermaid
flowchart LR
    L["Lead AI<br>splits the work"] --> A1["AI ①"] & A2["AI ②"] & A3["AI ③"]
    A1 & A2 & A3 --> S["AI sums up"]
    S --> Y["You look at the result and confirm"]
```

Each step must pass before work moves on: Durweg checks automatically that the result is there and complete, and when you write the workflow you decide which steps wait for your confirmation (it can be just once, at the end). If a check fails or you request changes, the work is revised and reviewed again. Each step can use existing skills and plugins; Durweg manages the order, checks, your approval and records.

## ✨ Features

| Feature | What you get | More |
| :--- | :--- | :--- |
| **Use the agents you already have open** | • Durweg calls no model API and passes no messages between agents<br>• Each step is done in a Claude Code, Codex or other session you have open; they all read and write the same run record | [Every day](every-day.md) |
| **You decide what it costs** | • The steps are fixed when you write the workflow; no model decides on the fly how many AIs to send out<br>• If you use these agents through a subscription (such as Claude or ChatGPT), there are no extra model API fees (your subscription still has its usage limits) | [Workflow format](workflow-format.md) |
| **Checked automatically, asks you only where you chose** | • Every step is checked automatically for a complete result; if it fails, the work is revised before moving on<br>• You decide which steps wait for your confirmation; it can be just once, at the end | [Workflow format](workflow-format.md) |
| **A record of every step** | • The steps, files, check results and your confirmations of each run are kept in your project's `runs/`<br>• `durweg check` checks the whole record again | [Where your files are](files.md) |
| **Pick up where it stopped** | • Which step a run has reached is saved on disk: if the session closes or the computer crashes, a new agent (it can be a different one) carries on from the step where it stopped<br>• Changes not yet saved at the moment of a crash may be lost | [Where your files are](files.md) |
| **Reuse and share your method** | • Write your way of working down once as a workflow, and every new project runs on it<br>• Keep it in your own library, publish it on GitHub (public or private), or install workflows others made | [Public and private workflows](publish.md#-public-and-private-workflows) |
| **Not tied to one agent** | • Install it as a Claude Code plugin, a Codex plugin, or with the installer<br>• Works on Windows, Mac and Linux | [Install](install.md) |
