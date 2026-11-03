#!/usr/bin/env python3
"""Gates of write-your-method (plan 2.7, V1-R-005). Read only.

  check_generated.py check RUN      step 2: at most 3 existing tools, a choice of use / build on / build my own
  check_generated.py design RUN     the design: a usable name, unique step ids, 2-12 steps
  check_generated.py build RUN      generated/<name>/ is a valid Durweg workflow and matches the
                                    confirmed design: same steps in the same order, a user gate
                                    exactly where the design asks the user, every instruction found
  check_generated.py register RUN   the copy registered in the library is the frozen generated one
  check_generated.py name RUN       step 6: a usable final name; a renamed copy is the generated workflow under that name
  check_generated.py case RUN       the case page is exactly what make_case.py builds from this run's
                                    record (no hand edits); the copy in ~/Durweg/cases is not checked,
                                    the user may move or share it

Uses the platform's own checks through $DURWEG_PLATFORM (set by durweg for command gates).
Exit 1 with one line per problem.
"""
import hashlib
import json
import os
import re
import sys
from pathlib import Path

ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def load(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        sys.exit(f"cannot read {p}: {e}")


def tree_digest(folder):
    h = hashlib.sha256()
    for p in sorted(Path(folder).rglob("*")):
        if p.is_file():
            h.update(p.relative_to(folder).as_posix().encode() + b"\0" + p.read_bytes())
    return h.hexdigest()


def design(run):
    d, errs = load(run / "steps/3-steps.json"), []
    if not ID.match(str(d.get("name", ""))):
        errs.append(f"name {d.get('name')!r}: use lower-case letters, digits and - (it becomes the command name)")
    steps = d.get("steps") or []
    if not 2 <= len(steps) <= 12:
        errs.append(f"{len(steps)} steps: a method has 2 to 12 steps")
    ids = [s.get("id") for s in steps]
    for i in ids:
        if not ID.match(str(i)):
            errs.append(f"step id {i!r}: use lower-case letters, digits and -")
    if len(set(ids)) != len(ids):
        errs.append("step ids must be different")
    return errs


def build(run):
    errs = design(run)
    if errs:
        return errs
    d = load(run / "steps/3-steps.json")
    out = run / "generated" / d["name"]
    if not (out / "workflow.json").is_file():
        return [f"generated/{d['name']}/workflow.json is missing: run tools/generate.py"]
    others = [p.name for p in (run / "generated").iterdir() if p.name != d["name"]]
    if others:
        errs.append(f"generated/ holds other folders too: {others}")
    platform = os.environ.get("DURWEG_PLATFORM")
    if not platform:
        return errs + ["DURWEG_PLATFORM is not set (run this as a durweg gate)"]
    sys.path.insert(0, platform)
    from durweg import workflow
    from durweg.util import WfError
    try:
        wf = workflow.load(out)
        workflow.snapshot_sources(wf)
    except WfError as e:
        return errs + [f"generated workflow is not valid: {e}"]
    want = [(s["id"], bool(s.get("user"))) for s in d["steps"]]
    have = [(sid, wf.has_user(sid)) for sid in wf.order]
    if [i for i, _ in have] != [i for i, _ in want]:
        errs.append(f"steps {[i for i, _ in have]} differ from the confirmed design {[i for i, _ in want]}")
    for (sid, u), (_, w) in zip(have, want):
        if u != w:
            errs.append(f"step {sid}: user confirmation is {'there' if u else 'missing'}, the design says {w}")
    for sid in wf.order:
        text = workflow.instructions(out, wf.step(sid)["instructions"])
        if text.startswith("(section") or text.startswith("(instructions file"):
            errs.append(f"step {sid}: {text}")
    if d.get("title") != wf.data.get("title"):
        errs.append("the title differs from the design")
    return errs


def register(run):
    rec, errs = load(run / "steps/4-register.json"), []
    d = load(run / "steps/3-steps.json")
    if rec.get("name") != d.get("name"):
        errs.append(f"registered name {rec.get('name')!r} is not the design's {d.get('name')!r}")
    frozen = tree_digest(run / "generated" / d["name"])
    if rec.get("digest") != frozen:
        errs.append("the registered copy is not the generated workflow of this run (digest differs)")
    if not str(rec.get("library_path", "")).strip():
        errs.append("library_path is missing")
    return errs


CHOICE = re.compile(r"^- Choice:\s*(use existing|build on .+|build my own)\s*$", re.M | re.I)


def check(run):
    t = (run / "steps/2-check.md").read_text(encoding="utf-8")
    m = re.search(r"^## Existing tools\s*$(.*?)(?=^## |\Z)", t, re.M | re.S)
    tools = [l for l in (m.group(1) if m else "").splitlines() if l.strip().startswith("- ")]
    errs = []
    if not tools:
        errs.append("'## Existing tools': list what was found (at most 3), or one line saying nothing was found")
    if len(tools) > 3:
        errs.append(f"{len(tools)} existing tools: show at most 3, the closest ones")
    if not CHOICE.search(t):
        errs.append("'## Choice' needs '- Choice: use existing', '- Choice: build on <tool>' or '- Choice: build my own'")
    return errs


def name(run):
    rec = load(run / "steps/6-name.json")
    d = load(run / "steps/3-steps.json")
    errs = []
    if not ID.match(str(rec.get("name", ""))):
        return [f"name {rec.get('name')!r}: use lower-case letters, digits and -"]
    if rec["name"] == d["name"]:
        return []                                   # kept the name used so far
    out = run / "named" / rec["name"]
    if not (out / "workflow.json").is_file():
        return [f"named/{rec['name']}/ is missing: run tools/rename.py"]
    if load(out / "workflow.json").get("id") != rec["name"]:
        errs.append("the renamed workflow's id is not the new name")
    if rec.get("digest") != tree_digest(out):
        errs.append("the renamed copy changed after rename.py wrote it")
    return errs


def case(run):
    rec = load(run / "steps/6-case.json")
    if rec.get("made") is False:
        return []                                   # the user chose not to write a case
    if rec.get("made") is not True:
        return ["steps/6-case.json: 'made' must be true or false"]
    page = run / str(rec.get("html", ""))
    if not page.is_file():
        return [f"{rec.get('html')} is missing: run tools/make_case.py"]
    data = page.read_bytes()
    errs = []
    if hashlib.sha256(data).hexdigest() != rec.get("sha256"):
        errs.append("the case page changed after make_case.py wrote it")
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import make_case
    try:
        again = make_case.page(run, load(run / "case/inputs.json")).encode("utf-8")
    except (KeyError, TypeError, ValueError, OSError) as x:
        return errs + [f"cannot rebuild the case page from this run's record: {x}"]
    if data != again:
        errs.append("the case page is not what make_case.py builds from this run's record (edited by hand?)")
    return errs                 # the copy in ~/Durweg/cases is the user's to move or share


def main(argv):
    if len(argv) != 2 or argv[0] not in ("check", "design", "build", "register", "name", "case"):
        sys.exit(__doc__)
    run = Path(argv[1]).resolve()
    errs = {"check": check, "design": design, "build": build, "register": register, "name": name,
            "case": case}[argv[0]](run)
    for e in errs:
        print(e)
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
