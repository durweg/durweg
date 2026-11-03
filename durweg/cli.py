"""durweg: run a workflow step by step, with gates and a checked record (design 3)."""

import argparse
import datetime
import json
import os
import re
import sys
from pathlib import Path

from . import gates, library, workflow
from .state import STATE, RunState, replay
from .util import PLUGIN_LABEL, RunLock, WfError, now, plugin_host, plugin_root, sha256_json, write_json

SLUG = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def detect_agent():
    if os.environ.get("CLAUDECODE"):
        return "claude", os.environ.get("CLAUDE_CODE_SESSION_ID")
    codex = {k: v for k, v in os.environ.items() if k.startswith("CODEX_")}
    if codex:
        return "codex", codex.get("CODEX_THREAD_ID") or codex.get("CODEX_SESSION_ID")
    return "unknown", None


def ok(st, n, extra=""):
    ev = st.events[n - 1]
    print(f"ok run={st.id} event={n} {ev['type']} {ev.get('step', '')}".rstrip())
    if extra:
        print(extra)


class Run:
    """An opened run: state, snapshot workflow, replay. Use inside the run lock."""

    def __init__(self, run_dir):
        self.st = RunState(run_dir)
        self.dir = self.st.dir
        self.wf = workflow.load_snapshot(self.dir, self.st.start["workflow"]["manifest"])
        self.rp = replay(self.wf, self.st.events)
        if self.rp.violations:
            raise WfError("the event log is not valid; run `durweg check`:\n  " + "\n  ".join(self.rp.violations))

    def refuse(self, ev_type, step, reason):
        self.st.append({"t": now(), "type": "refused", "command": ev_type, "step": step, "reason": reason})
        raise WfError(f"refused run={self.st.id}: {reason}")

    def legal(self, ev):
        why = self.rp.why_not(ev)
        if why:
            self.refuse(ev["type"], ev.get("step"), why)

    def show_step(self, sid):
        s = self.wf.step(sid)
        snap = self.dir / workflow.SNAP
        lines = [f"== step {self.wf.index(sid)} {sid}: {s['title']} (round {self.rp.round[sid]})",
                 f"artifacts: {', '.join(s['artifacts'])}",
                 "gates: " + ", ".join(g["type"] for g in s["gates"])]
        if self.wf.has_user(sid):
            lines.append("user gate: write the proposal, `durweg propose`, show it to the user, then "
                         "`durweg confirm --quote \"<their words>\" [--set key=value]`, then `durweg done`")
        lines += ["", workflow.instructions(snap, s["instructions"])]
        return "\n".join(lines)

    def next_hint(self):
        for sid in self.wf.order:
            if self.rp.status[sid] == "pending" and all(self.rp.status[n] == "done" for n in self.wf.needs(sid)):
                return f"next: durweg begin {self.dir} {sid}"
        if all(v == "done" for v in self.rp.status.values()):
            return f"all steps done: durweg check {self.dir}"
        return ""


# -- commands --------------------------------------------------------------------------
def cmd_start(a):
    if not SLUG.match(a.slug):
        raise WfError(f"slug must match {SLUG.pattern}")
    src, lib_name = library.resolve(a.workflow)
    runs = Path(a.runs).expanduser().resolve()
    run_id = f"{datetime.date.today().isoformat()}_{a.slug}"
    run_dir = runs / run_id
    # plan v1.1 C4: whatever named the folder (library name, alias, absolute or relative path),
    # load, source state and snapshot happen under that folder's lock, so an update that swaps it
    # is either wholly before or wholly after: the snapshot and the commit belong together
    with library.source_lock(src):
        wf = workflow.load(src)
        workflow.check_platform(wf)
        files = workflow.snapshot_sources(wf)
        kind, commit, dirty = workflow.repo_state(wf, files, a.dev)
        if run_dir.exists():
            raise WfError(f"{run_dir} already exists; use another slug, for example {a.slug}-2")
        (run_dir / ".wf").mkdir(parents=True)
        manifest = workflow.make_snapshot(wf, run_dir, files)
    agent, session = detect_agent()
    data = {"format": 1, "run": run_id, "events": [{
        "n": 1, "t": now(), "type": "start",
        "workflow": {"id": wf.id, "source": str(wf.root), "source_kind": kind, "commit": commit,
                     "dev": bool(a.dev), "dirty": dirty, "manifest": manifest,
                     "digest": sha256_json(manifest)},
        "trial": bool(a.trial), "agent": a.agent or agent, "session": a.session or session,
        "library": lib_name}]}
    write_json(run_dir / STATE, data)
    (run_dir / "steps").mkdir(exist_ok=True)
    run = Run(run_dir)
    note = library.record_run(run_dir, wf.id, lib_name, data["events"][0]["t"])
    ok(run.st, 1, f"run directory: {run_dir}" + ("\n(dev run: not usable for acceptance)" if a.dev else "")
       + f"\n{run.next_hint()}" + (f"\n{note}" if note else ""))


def with_run(fn):
    def wrapped(a):
        run_dir = Path(a.run).expanduser().resolve()
        if not (run_dir / STATE).is_file():
            raise WfError(f"{a.run} is not a Durweg run (no {STATE})")
        lock = RunLock(run_dir)
        with lock:
            if lock.note:
                print("note:", lock.note)
            fn(Run(run_dir), a)
    return wrapped


@with_run
def cmd_begin(run, a):
    run.wf.step(a.step)
    run.legal({"type": "begin", "step": a.step})
    n = run.st.append({"t": now(), "type": "begin", "step": a.step, "round": run.rp.round[a.step] + 1})
    run.rp.apply(run.st.events[-1])
    ok(run.st, n, run.show_step(a.step))


@with_run
def cmd_propose(run, a):
    run.wf.step(a.step)
    run.legal({"type": "propose", "step": a.step})
    files = [f for f in gates.artifact_files(run.dir, run.wf, a.step) if f != run.wf.decision_path(a.step)]
    if not files:
        run.refuse("propose", a.step, f"step {a.step}: no proposal files yet ({', '.join(run.wf.step(a.step)['artifacts'])})")
    d = gates.proposal_digest(run.dir, run.wf, a.step)
    n = run.st.append({"t": now(), "type": "propose", "step": a.step, "round": run.rp.round[a.step],
                       "proposal_digest": d, "files": files})
    ok(run.st, n, "now show exactly this version to the user; any change to it needs a new `durweg propose`")


def parse_set(pairs):
    out = {}
    for p in pairs or []:
        k, sep, v = p.partition("=")
        if not sep or not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", k):
            raise WfError(f"--set takes KEY=VALUE, got '{p}'")
        out[k] = v
    return out


@with_run
def cmd_confirm(run, a):
    run.wf.step(a.step)
    values = parse_set(a.set)
    if not a.quote.strip():
        raise WfError("--quote must be the user's own words")
    p = run.rp.propose.get(a.step)
    run.legal({"type": "confirm", "step": a.step, "proposal_event": p["n"] if p else None})
    if gates.proposal_digest(run.dir, run.wf, a.step) != p["proposal_digest"]:
        run.refuse("confirm", a.step, f"step {a.step}: the proposal changed after `durweg propose` "
                                      f"(event {p['n']}); propose again and show it to the user")
    # The decision file first, then the event (WP-C-004): a crash in between leaves a decision
    # file that no confirm event backs, which the next confirm overwrites and done/check reject;
    # never a committed confirm without its decision file.
    n = len(run.st.events) + 1
    write_json(run.dir / run.wf.decision_path(a.step), {"confirm_event": n, "values": values})
    run.st.append({"t": now(), "type": "confirm", "step": a.step, "round": run.rp.round[a.step],
                   "proposal_event": p["n"], "quote": a.quote, "set": values})
    ok(run.st, n, f"next: durweg done {run.dir} {a.step}")


@with_run
def cmd_done(run, a):
    sid = a.step
    run.wf.step(sid)
    c = run.rp.confirm.get(sid)
    ev = {"type": "done", "step": sid}
    if run.wf.has_user(sid):
        ev["confirm_event"] = c["n"] if c else None
    run.legal(ev)
    problems = gates.evaluate(run.dir, run.wf, sid, run.rp)
    if problems:
        run.refuse("done", sid, f"step {sid}: gates not passed:\n  " + "\n  ".join(problems))
    ev.update({"t": now(), "round": run.rp.round[sid],
               "artifacts_digest": gates.artifacts_digest(run.dir, run.wf, sid),
               "files": gates.artifact_files(run.dir, run.wf, sid)})
    if run.wf.has_user(sid):
        ev["proposal_digest"] = run.rp.propose[sid]["proposal_digest"]
    n = run.st.append(ev)
    run.rp.apply(run.st.events[-1])
    ok(run.st, n, run.next_hint())


@with_run
def cmd_reopen(run, a):
    sid = a.step
    run.wf.step(sid)
    if not a.reason.strip():
        raise WfError("--reason is required")
    run.legal({"type": "reopen", "step": sid})
    reset = sorted(run.wf.dependents(sid), key=run.wf.order.index)
    reset = [d for d in reset if run.rp.status[d] != "pending"]
    n = run.st.append({"t": now(), "type": "reopen", "step": sid, "round": run.rp.round[sid] + 1,
                       "reason": a.reason, "reset": reset})
    run.rp.apply(run.st.events[-1])
    ok(run.st, n, (f"back to pending: {', '.join(reset)}\n" if reset else "") + run.show_step(sid))


def find_open_runs(base):
    out = []
    for p in sorted(Path(base).glob("*/" + STATE)):
        rd = p.parent.parent
        try:
            st = RunState(rd)
            wf = workflow.load_snapshot(rd, st.start["workflow"]["manifest"])
            if any(v != "done" for v in replay(wf, st.events).status.values()):
                out.append(rd)
        except WfError:
            out.append(rd)
    return out


def cmd_status(a):
    if a.run:
        run_dir = Path(a.run).expanduser().resolve()
    else:
        found = find_open_runs(Path("runs"))
        if len(found) != 1:
            if not found:
                print("no unfinished run under ./runs")
            else:
                print("more than one unfinished run; name one:\n  " + "\n  ".join(map(str, found)))
            return 0 if not found else 1
        run_dir = found[0]
    run = Run(run_dir)
    s = run.st.start
    ident = (s['workflow'].get('commit') or "")[:10] or "files " + s['workflow'].get('digest', '')[:10]
    print(f"run {run.st.id} · workflow {s['workflow']['id']} @ {ident}"
          f"{' · dev' if s['workflow']['dev'] else ''}{' · trial' if s['trial'] else ''} · agent {s['agent']}")
    for sid in run.wf.order:
        mark = {"done": "x", "active": ">", "pending": " "}[run.rp.status[sid]]
        print(f"  [{mark}] {run.wf.index(sid)} {sid} (round {run.rp.round[sid]})")
    refused = [e for e in run.st.events if e["type"] == "refused"]
    if refused:
        print(f"  refusals so far: {len(refused)}")
    hint = run.next_hint()
    if run.rp.active:
        hint = f"active: {run.rp.active}"
    print(hint)
    return 0


def cmd_render(a):
    run = Run(Path(a.run).expanduser().resolve())
    s = run.st.start
    out = [f"# Run {run.st.id}", "",
           f"Workflow `{s['workflow']['id']}` at `{s['workflow']['commit']}`, agent {s['agent']}, "
           f"started {s['t']}. Generated by `durweg render`; the record is `steps/` and `.wf/state.json`.", ""]
    if s["trial"]:
        out += ["> **Trial run.** Choices made here are trial choices, not formal decisions.", ""]
    for sid in run.wf.order:
        st = run.wf.step(sid)
        out += [f"## {run.wf.index(sid)}. {st['title']} ({run.rp.status[sid]}, round {run.rp.round[sid]})", ""]
        for rel in gates.artifact_files(run.dir, run.wf, sid) + (
                [run.wf.decision_path(sid)] if run.wf.has_user(sid) and
                (run.dir / run.wf.decision_path(sid)).is_file() else []):
            p = run.dir / rel
            if rel.endswith(".md"):
                out += [f"### `{rel}`", "", p.read_text(encoding="utf-8").rstrip(), ""]
            elif rel.endswith(".json") and p.stat().st_size < 200_000:
                out += [f"### `{rel}`", "", "```json", p.read_text(encoding="utf-8").rstrip(), "```", ""]
            else:
                out += [f"- `{rel}`"]
        c = run.rp.confirm.get(sid)
        if c:
            out += [f"User confirmed (event {c['n']}, {c['t']}): “{c['quote']}”", ""]
    (run.dir / "run.md").write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
    print(f"wrote {run.dir / 'run.md'}")
    return 0


JSON_SCHEMA = 1


def emit(obj):
    """--json: stdout holds exactly one JSON object (plan durweg-ui UI-R-009)."""
    print(json.dumps(dict({"schema": JSON_SCHEMA, "ok": True}, **obj), ensure_ascii=False))
    return 0


def _library_list_json():
    from . import catalog
    items = []
    for name, e in sorted(library.entries().items()):
        p = Path(e["path"])
        try:
            plats, valid = list(workflow.load(p).data.get("platforms") or workflow.PLATFORMS), True
        except WfError:
            plats, valid = None, False
        items.append({"name": name, "path": str(p), "platforms": plats, "valid": valid,
                      "url": catalog.gitops.redact(e["url"]) if e.get("url") else None,
                      "builtin": library.is_builtin(name, e) or (e.get("source") == "plugin" and p.exists()),
                      "comes_with": "durweg" if library.is_builtin(name, e) else e.get("plugin")})
    return emit({"items": items})


def _available_json():
    from . import catalog
    lib = library.entries()
    cats = catalog.enabled()
    items, notes = [], []
    for cid in sorted(cats):
        found, note = catalog.read(cid, cats[cid])
        if note:
            notes.append(note)
        for name, e in sorted((found or {}).items()):
            as_ = next((n for n, le in sorted(lib.items()) if le.get("url") and catalog.same_url(le["url"], e["url"])), None)
            plats = None
            if as_:
                try:
                    plats = list(workflow.load(Path(lib[as_]["path"])).data.get("platforms") or workflow.PLATFORMS)
                except WfError:
                    plats = None
            items.append({"ref": f"{cid}:{name}", "catalog": cid, "name": name, "title": e["title"],
                          "summary": e["summary"], "installed_as": as_, "platforms": plats,
                          # the same name already in the library from elsewhere (own folder, other address)
                          "name_in_library": name in lib and not as_})
    return emit({"catalogs_on": sorted(cats), "items": items, "notes": notes})


def cmd_library(a):
    if a.json and a.action == "list":
        return _library_list_json()
    if a.json and a.action == "available":
        return _available_json()
    if a.action in ("add", "remove") and not a.target:
        raise WfError(f"durweg library {a.action} needs a "
                      f"{'name, <catalog>:<name>, folder or git address' if a.action == 'add' else 'name'}")
    if a.action == "add":
        name, path, note = library.add(a.target, a.name)
        if a.json:
            return emit({"name": name, "path": str(path), "note": note})
        if note:
            print(f"note: {note}", file=sys.stderr)
        print(f"added {name}: {path}\nrun it with: durweg start {name} <name-of-this-run>")
    elif a.action == "remove":
        path = library.remove(a.target)
        if a.json:
            return emit({"name": a.target, "folder_kept": str(path)})
        print(f"removed {a.target} from the library (the folder {path} is kept)")
    elif a.action == "available":
        return _available()
    elif a.action == "update":
        return _update([a.target] if a.target else None, quiet=a.quiet, as_json=a.json)
    else:
        items = library.entries()
        if not items:
            print(f"the library is empty ({library.home() / 'library.json'})")
        for name, e in sorted(items.items()):
            p = Path(e["path"])
            try:
                plats = ", ".join(workflow.load(p).data.get("platforms") or workflow.PLATFORMS)
                state = ""
            except WfError:
                plats, state = "?", "  (missing or invalid)"
            print(f"{name:20} {plats:24} {p}{state}")
    return 0


def _available():
    """Plan v1.1 C1: what the enabled catalogs offer, as <catalog>:<name>."""
    from . import catalog
    installed = [e.get("url") for e in library.entries().values() if e.get("url")]
    cats = catalog.enabled()
    if not cats:
        print("no catalog is switched on; `durweg catalog add public` switches the public one on")
        return 0
    shown = 0
    for cid in sorted(cats):
        items, note = catalog.read(cid, cats[cid])
        if note:
            print(f"note: {note}", file=sys.stderr)
        for name, e in sorted((items or {}).items()):
            mark = "  (installed)" if any(catalog.same_url(u, e["url"]) for u in installed) else ""
            print(f"{cid + ':' + name:32} {e['summary'] or e['title']}{mark}")
            shown += 1
    if shown:
        print("install one with: durweg library add <catalog>:<name>  (or just <name> if only one catalog has it)")
    else:
        print("no workflows to show")
    # the way to make one's own comes with Durweg, so no catalog lists it (user 2026-10-31)
    print('to make your own: tell your agent "Run write-your-method with durweg." (it comes with Durweg)')
    return 0


def _normal_skip(detail):
    """A skip that needs no attention: the user's own folder, or the example in the plugin."""
    return detail.startswith("your own folder") or detail.startswith("comes with the")


def update_data(names):
    """Plan v1.1 C5: the catalogs, then every workflow Durweg cloned (or only `names`).
    {"catalogs": [{id, state, reason, had}], "items": [{name, status, detail}], "counts": {...}}."""
    from . import catalog
    cats = []
    if not names:
        for cid, entry in sorted(catalog.enabled().items()):
            had = (catalog.cache_dir(cid) / "catalog.json").is_file()
            reason = catalog.refresh(cid, entry["url"])
            cats.append({"id": cid, "state": "refreshed" if not reason else "kept" if had else "missing",
                         "reason": reason, "had": had})
    items = [{"name": n, "status": s, "detail": d} for n, s, d in library.update(names)]
    counts = {k: sum(1 for it in items if it["status"] == k) for k in ("updated", "unchanged", "skipped", "failed")}
    return {"catalogs": cats, "items": items, "counts": counts,
            "attention": [it["name"] for it in items
                          if it["status"] == "failed" or (it["status"] == "skipped" and not _normal_skip(it["detail"]))]}


def _update(names, quiet=False, as_json=False):
    """Print update_data. Exit 0 even when some were skipped or failed: those are reported, the rest
    is done (--json: ok is false when any failed). quiet (the installers): only what changed or needs attention."""
    d = update_data(names)
    if as_json:
        return emit(dict(d, ok=not d["counts"]["failed"]))
    for c in d["catalogs"]:
        if c["state"] == "kept":
            print(f"catalog {c['id']}: not refreshed ({c['reason']}); the last copy is kept")
        elif c["state"] == "missing" and not quiet:      # never used yet: the installers need not say so (V11-C-010)
            print(f"catalog {c['id']}: not downloaded yet ({c['reason']})")
        elif c["state"] == "refreshed" and not quiet:
            print(f"catalog {c['id']}: refreshed")
    shown = 0
    for it in d["items"]:
        if quiet and (it["status"] == "unchanged" or (it["status"] == "skipped" and _normal_skip(it["detail"]))):
            continue
        print(f"{it['name']:23} {it['status']:9} {it['detail']}")
        shown += 1
    if not d["items"] and not names and not quiet:
        print("the library is empty")
    if shown or not quiet:
        print("summary: " + ", ".join(f"{d['counts'][k]} {k}" for k in ("updated", "unchanged", "skipped", "failed")))
    if d["attention"]:
        print("warning: some were not updated; the reasons are on their lines", file=sys.stderr)
    return 0


def cmd_update(a):
    from . import selfupdate
    return selfupdate.main_update(as_json=a.json)


def cmd_publish(a):
    """Plan v1.1 D5/C7: without --yes only shows what would happen."""
    from . import publish
    vis = "public" if a.public else "private" if a.private else None
    p = publish.prepare(a.name, visibility=vis, repo=a.repo, license_choice=a.license, case=a.case,
                        catalog_answer=a.catalog, language_ok=a.language_ok, english_readme_answer=a.english_readme)
    if not a.yes:
        print(publish.show(p))
        return 0
    for line in publish.publish(p):
        print(line)
    return 0


def cmd_catalog(a):
    from . import catalog
    if a.action == "create-private":
        from . import publish
        owner = publish.login()
        what, why_not = publish.private_plan(owner)
        if why_not:
            raise WfError(why_not)
        if not a.yes:
            if a.json:
                return emit({"preview": True, "account": owner, "would": what})
            print(f"would {what}\nnothing was done yet; with the user's yes, run it again with --yes")
            return 0
        cid = publish.create_private(owner, adopt=what.startswith("use "))
        if a.json:
            return emit({"preview": False, "id": cid, "url": catalog.gitops.redact(catalog.configured()[cid]["url"])})
        print(f"your private catalog is {cid}: {catalog.gitops.redact(catalog.configured()[cid]['url'])}\n"
              f"on another computer: durweg catalog add {cid} <this address>")
        return 0
    if a.action == "list" and a.json:
        return emit({"items": [{"id": cid, "on": not e.get("disabled"), "url": catalog.gitops.redact(e["url"]),
                                "fetched": e.get("fetched")} for cid, e in sorted(catalog.configured().items())]})
    if a.action == "list":
        for cid, e in sorted(catalog.configured().items()):
            state = "off" if e.get("disabled") else "on"
            print(f"{cid:16} {state:4} {catalog.gitops.redact(e['url'])}"
                  f"{'  (last downloaded ' + e['fetched'] + ')' if e.get('fetched') else ''}")
        return 0
    if not a.id:
        raise WfError(f"durweg catalog {a.action} needs a name")
    if a.action == "add":
        url, reason = catalog.add(a.id, a.url)
        if a.json:
            return emit({"id": a.id, "url": catalog.gitops.redact(url), "note": reason})
        print(f"catalog {a.id} is on: {catalog.gitops.redact(url)}")
        if reason:
            print(f"note: it could not be downloaded now ({reason}); `durweg library available` tries again",
                  file=sys.stderr)
    else:
        public_off = catalog.remove(a.id)
        if a.json:
            return emit({"id": a.id, "result": "switched off" if public_off else "removed"})
        if public_off:
            print("the public catalog is switched off; `durweg catalog add public` switches it on again")
        else:
            print(f"removed catalog {a.id} (workflows installed from it stay in the library)")
    return 0


def cmd_runs(a):
    if a.rebuild:
        n = library.rebuild(a.rebuild)
        print(f"found {n} run(s) under {a.rebuild}; index: {library.home() / 'runs.json'}")
        return 0
    rows = library.runs()
    if not rows:
        print("no runs recorded yet")
    for r in rows:
        rd = Path(r["path"])
        try:
            run = Run(rd)
            done = sum(1 for v in run.rp.status.values() if v == "done")
            state = "done" if done == len(run.wf.order) else f"{done}/{len(run.wf.order)} steps"
        except (WfError, OSError, ValueError, KeyError):
            state = "missing" if not rd.exists() else "unreadable"
        print(f"{r.get('started', '')[:16]:16}  {r.get('library') or r.get('workflow') or '?':20} {state:12} {rd}")
    return 0


def cmd_config(a):
    """Show or change ~/Durweg/config.json (the language agents use to talk to you)."""
    p = library.home() / "config.json"
    try:
        cfg = json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}
    except ValueError:
        raise WfError(f"{p} cannot be read; fix or delete it")
    if a.key:
        if a.key == "language" and a.value in ("en", "zh"):
            cfg["language"] = a.value
            msg = f"language: {a.value} (agents use it from their next step on)"
        elif a.key == "publish-owner" and a.value:
            if a.value == "none":
                cfg.pop("publish_owner", None)
                msg = "publish-owner: not set (durweg publish uses your GitHub account)"
            elif re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}", a.value):
                cfg["publish_owner"] = a.value
                msg = f"publish-owner: {a.value} (new workflows from durweg publish go to {a.value}/durweg-<name>)"
            else:
                raise WfError("durweg config publish-owner <GitHub user or organization> | none")
        else:
            raise WfError("durweg config language en|zh, or durweg config publish-owner <owner>|none")
        p.parent.mkdir(parents=True, exist_ok=True)
        write_json(p, cfg)
        print(msg)
    else:
        lang = cfg.get("language")
        print(f"{p}\nlanguage: " + (lang or "en (not set yet; run: durweg config language en|zh)"))
        print("publish-owner: " + (cfg.get("publish_owner") or "not set (your GitHub account)"))
    return 0


def cmd_plugin_workflows(a):
    for name, result in library.follow_plugin(a.plugin, a.folders):
        print(f"{name:23} {result}")
    return 0


def cmd_example(a):
    library.point_example(a.path)
    return 0


def cmd_coexist(a):
    from .util import coexist_lines
    for line in coexist_lines():
        print(line)
    return 0


def cmd_doctor(a):
    from . import doctor
    rep = doctor.report()
    if a.json:
        return emit(rep)
    print(doctor.show(rep))
    return 0


def cmd_ui(a):
    from . import ui
    return ui.run(no_browser=a.no_browser)


def cmd_uninstall(a):
    from .uninstall import uninstall
    for line in uninstall(dry_run=a.dry_run):
        print(line)
    return 0


def cmd_check(a):
    from .check import check
    return check(Path(a.run).expanduser().resolve())


def cmd_audit(a):
    """The audit is the optional plugin durweg-audit; this only says so and fails, so that a
    missing plugin is never taken for a passed audit (plan V1-R-004)."""
    print("durweg audit is an optional plugin: install durweg-audit "
          "(https://github.com/durweg/durweg-audit), then run: durweg-audit <run> --transcript <files>",
          file=sys.stderr)
    return 5


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):         # Windows consoles default to a legacy code page
        if hasattr(stream, "reconfigure") and (stream.encoding or "").lower() not in ("utf-8", "utf8"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass
    ap = argparse.ArgumentParser(prog="durweg", description=__doc__)
    from . import __version__
    root = plugin_root()
    ap.add_argument("--version", action="version",
                    version=f"durweg {__version__}" + (PLUGIN_LABEL[plugin_host(root)] if root else ""))
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("start", help="start a run of a workflow")
    p.add_argument("workflow", help="a name in the library, or a folder with workflow.json (./name, /path)")
    p.add_argument("slug")
    p.add_argument("--runs", default="runs", help="directory that holds runs (default ./runs)")
    p.add_argument("--trial", action="store_true", help="a trial run: its choices are not formal decisions")
    p.add_argument("--dev", action="store_true", help="allow uncommitted workflow files (not for acceptance)")
    p.add_argument("--agent")
    p.add_argument("--session")
    for name in ("begin", "propose", "done"):
        p = sub.add_parser(name)
        p.add_argument("run")
        p.add_argument("step")
    p = sub.add_parser("confirm")
    p.add_argument("run")
    p.add_argument("step")
    p.add_argument("--quote", required=True, help="the user's own words, verbatim")
    p.add_argument("--set", action="append", metavar="KEY=VALUE", help="a decision from the user's answer")
    p = sub.add_parser("reopen")
    p.add_argument("run")
    p.add_argument("step")
    p.add_argument("--reason", required=True)
    p = sub.add_parser("library", help="the method library in ~/Durweg")
    p.add_argument("action", choices=["add", "list", "remove", "available", "update"])
    p.add_argument("target", nargs="?",
                   help="add: a name, <catalog>:<name>, a folder (./name) or a git address; remove: a name; "
                        "update: a name (all when left out)")
    p.add_argument("--name")
    p.add_argument("--quiet", action="store_true", help="update: show only what changed or needs attention")
    p.add_argument("--json", action="store_true", help="print one JSON object (for programs)")
    p = sub.add_parser("update", help="update Durweg itself to the newest release, then the catalogs and workflows")
    p.add_argument("--json", action="store_true", help="print one JSON object (for programs)")
    p = sub.add_parser("publish", help="put one of your workflows on GitHub (shows first; --yes does it)")
    p.add_argument("name", help="a workflow in your library, from your own folder")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--public", action="store_true")
    g.add_argument("--private", action="store_true")
    p.add_argument("--repo", help="owner/name on GitHub (default: <publish-owner or you>/durweg-<name>)")
    p.add_argument("--language-ok", action="store_true",
                   help="public: keep CJK text in examples, trigger words or labels of the English pages on purpose")
    p.add_argument("--english-readme", choices=["add", "skip"],
                   help="public, README not in English: add one first, or skip and publish as it is")
    p.add_argument("--license", help="MIT, Apache-2.0, CC-BY-4.0 or none (when the folder has no LICENSE)")
    p.add_argument("--case", help="a case page from ~/Durweg/cases/ to include")
    p.add_argument("--catalog", choices=["yes", "no"], help="public: propose it to the public catalog; "
                                                             "private: add it to your private catalog")
    p.add_argument("--yes", action="store_true", help="the user said yes to what was shown: do it")
    p = sub.add_parser("catalog", help="the catalogs of workflows that can be installed by name")
    p.add_argument("action", choices=["add", "list", "remove", "create-private"])
    p.add_argument("id", nargs="?", help="the catalog's name (public is the public catalog)")
    p.add_argument("url", nargs="?", help="add: the catalog's git address")
    p.add_argument("--yes", action="store_true", help="create-private: the user said yes to what was shown")
    p.add_argument("--json", action="store_true", help="print one JSON object (for programs)")
    p = sub.add_parser("runs", help="list the runs started on this computer")
    p.add_argument("--rebuild", metavar="FOLDER", help="scan FOLDER for runs and add them to the index")
    p = sub.add_parser("config", help="show or change your settings: durweg config language en|zh, "
                                     "durweg config publish-owner <owner>|none")
    p.add_argument("key", nargs="?")
    p.add_argument("value", nargs="?")
    sub.add_parser("_coexist", help=argparse.SUPPRESS)    # install.sh: plugin copies next to this one
    p = sub.add_parser("_plugin_workflows", help=argparse.SUPPRESS)   # another plugin's hook: its workflows
    p.add_argument("plugin")
    p.add_argument("folders", nargs="+")
    p = sub.add_parser("_example", help=argparse.SUPPRESS)   # Durweg-Install.bat: the example of this version
    p.add_argument("path")
    p = sub.add_parser("doctor", help="check this computer: agents, whether they have Durweg, GitHub sign-in")
    p.add_argument("--json", action="store_true", help="print one JSON object (for programs)")
    p = sub.add_parser("ui", help="open the management page in your browser (this computer only)")
    p.add_argument("--no-browser", action="store_true", help="only print the link")
    p = sub.add_parser("uninstall", help="remove what the installer put on this computer (keeps ~/Durweg)")
    p.add_argument("--dry-run", action="store_true")
    p = sub.add_parser("status")
    p.add_argument("run", nargs="?")
    p = sub.add_parser("render")
    p.add_argument("run")
    p = sub.add_parser("check")
    p.add_argument("run")
    p = sub.add_parser("audit", help="optional plugin durweg-audit (not installed by default)")
    p.add_argument("rest", nargs=argparse.REMAINDER)
    a = ap.parse_args(argv)
    if root is not None:                    # after parsing: --version and --help change nothing
        library.ensure_plugin_example(root)
    fn = {"start": cmd_start, "begin": cmd_begin, "propose": cmd_propose, "confirm": cmd_confirm,
          "done": cmd_done, "reopen": cmd_reopen, "status": cmd_status, "render": cmd_render,
          "check": cmd_check, "audit": cmd_audit, "library": cmd_library, "catalog": cmd_catalog, "update": cmd_update, "publish": cmd_publish, "runs": cmd_runs, "uninstall": cmd_uninstall, "config": cmd_config, "_coexist": cmd_coexist, "ui": cmd_ui, "doctor": cmd_doctor, "_example": cmd_example, "_plugin_workflows": cmd_plugin_workflows}[a.cmd]
    try:
        rc = fn(a)
    except WfError as e:
        if getattr(a, "json", False):
            print(json.dumps({"schema": JSON_SCHEMA, "ok": False, "error": str(e)}, ensure_ascii=False))
        else:
            print(str(e), file=sys.stderr)
        return getattr(e, "exit_code", 1)
    except OSError as e:
        if not cannot_write_home(e):
            raise
        print(cannot_write_home(e), file=sys.stderr)
        return 1
    return rc or 0


def cannot_write_home(e):
    """The message when e is "may not write" inside ~/Durweg (a sandbox, e.g. Codex's), else None.
    Linux and WSL report EROFS (30), macOS's sandbox EPERM (1), plain permissions EACCES (13)."""
    if getattr(e, "errno", None) not in (1, 13, 30) or not e.filename:
        return None
    home = os.path.realpath(library.home())
    target = os.path.realpath(e.filename)
    if target != home and not target.startswith(home + os.sep):
        return None
    return (f"durweg cannot write to {library.home()} ({e.strerror}). If a sandbox runs this command "
            "(for example Codex's), approve the command when you are asked, or let the sandbox write to "
            "that folder; see the install page of the Durweg plugin.")


if __name__ == "__main__":
    sys.exit(main())
