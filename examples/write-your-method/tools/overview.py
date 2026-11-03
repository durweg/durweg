#!/usr/bin/env python3
"""write-your-method, after each step: a table of this run's files, so the user sees where everything is.

  overview.py RUN

Lists what exists so far: each step's file (in RUN/steps/), the workflow built from the design
(RUN/generated/<name>/), its copy in the library (~/Durweg/workflows/<name>/, $DURWEG_HOME if set),
the renamed one (RUN/named/<name>/) and the case page. Each row says what it is and where it is.
Written in the language of ~/Durweg/config.json (zh or en). Reads only; standard library only.
"""
import json
import os
import sys
from pathlib import Path

STEP_FILES = [   # (file in RUN/steps, step number, what it is in en, in zh)
    ("1-method.md", 1, "your method: the core, how you do it, where it goes wrong, where you decide",
     "你的做法：核心、怎么做、常出问题的地方、你决定的地方"),
    ("2-check.md", 2, "existing tools that were found, and your choice", "查到的现成工具和你的选择"),
    ("3-review.md", 3, "your method back, and the suggestions you took", "复述你的做法，以及你采纳的建议"),
    ("3-steps.json", 3, "the steps of the new workflow", "新工作流的步骤"),
    ("4-register.json", 4, "where the workflow was put in your library", "工作流放进方法库的位置"),
    ("5-try.json", 5, "the first run of the new workflow", "新工作流的第一次运行"),
    ("6-name.json", 6, "the final name", "正式名字"),
    ("6-lessons.md", 6, "your lessons for the case page", "案例页里你的经验"),
    ("6-case.json", 6, "whether a case page was made", "有没有做案例页"),
]

HEAD = {"en": ("Step", "What", "Where"), "zh": ("步骤", "是什么", "在哪")}
TEXT = {
    "en": {"generated": "the workflow built from your design (made by step 4; do not edit by hand)",
           "library": "its copy in your library: on this computer only, private, not uploaded",
           "named": "the workflow under its final name", "case": "the case page (open it by double-clicking)",
           "decision": "your words when you confirmed", "all": "all of this run", "folder": "folder"},
    "zh": {"generated": "按你的设计生成的工作流（第 4 步生成，不要手改）",
           "library": "方法库里的那一份：只在这台电脑上，私人的，没有上传",
           "named": "改成正式名字后的工作流", "case": "案例页（双击打开）",
           "decision": "你确认时的原话", "all": "这次运行的全部记录", "folder": "文件夹"},
}


def language():
    home = Path(os.environ.get("DURWEG_HOME") or Path.home() / "Durweg")
    try:
        lang = json.loads((home / "config.json").read_text(encoding="utf-8")).get("language")
    except (OSError, ValueError, AttributeError):
        lang = None
    return lang if lang in TEXT else "en"


def rows(run, lang):
    t = TEXT[lang]
    home = Path(os.environ.get("DURWEG_HOME") or Path.home() / "Durweg")
    out = [("", t["all"], f"{run}/")]
    for name, n, en, zh in STEP_FILES:
        p = run / "steps" / name
        if p.is_file():
            out.append((str(n), en if lang == "en" else zh, f"steps/{name}"))
    if any((run / "steps").glob("*.decision.json")):
        out.append(("", t["decision"], "steps/*.decision.json"))
    try:
        name = json.loads((run / "steps/3-steps.json").read_text(encoding="utf-8"))["name"]
    except (OSError, ValueError, KeyError, TypeError):
        name = None
    if name and (run / "generated" / name).is_dir():
        out.append(("4", t["generated"], f"generated/{name}/"))
    try:
        lib = json.loads((run / "steps/4-register.json").read_text(encoding="utf-8"))["library_path"]
    except (OSError, ValueError, KeyError, TypeError):
        lib = str(home / "workflows" / name) if name and (home / "workflows" / name).is_dir() else None
    if lib:
        out.append(("4", t["library"], f"{lib}/"))
    for d in sorted((run / "named").glob("*")) if (run / "named").is_dir() else []:
        out.append(("6", t["named"], f"named/{d.name}/"))
    for c in sorted((run / "case").glob("*.html")) if (run / "case").is_dir() else []:
        out.append(("6", t["case"], f"case/{c.name}"))
    return out


def table(run, lang=None):
    lang = lang or language()
    h = HEAD[lang]
    lines = [f"| {h[0]} | {h[1]} | {h[2]} |", "| :--- | :--- | :--- |"]
    lines += [f"| {a} | {b} | `{c}` |" for a, b, c in rows(Path(run).resolve(), lang)]
    return "\n".join(lines)


def main(argv):
    if len(argv) != 1:
        sys.exit(__doc__)
    if hasattr(sys.stdout, "reconfigure"):          # Windows consoles default to a legacy code page
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass
    print(table(argv[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
