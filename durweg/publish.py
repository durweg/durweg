"""durweg publish: put one of your own workflows on GitHub (plan v1.1 D5, C7, C8, U3, revision 3).

Two steps, so that every confirmation goes through the agent's question to the user:
  durweg publish <name> [choices]        prepares and shows what would happen; publishes nothing
  durweg publish <name> [choices] --yes  does it

What is published is only what the workflow needs (workflow.json, the skill folder, the files under
"snapshot"), a README and a LICENSE (the folder's own, or chosen now), and a case page only when
named. It is copied into ~/Durweg/publish/<name>/, a git repository of its own; nothing else from
the folder, no runs, no settings. The folder stays yours: edit it there and publish again.

Repositories: a repository that this staging folder did not create is never pushed to, and the
visibility of an existing one is never changed. One change made on GitHub is followed: a workflow
published as private whose repository you made public there is published as public from then on
(shown first; the record changes at --yes), and its entry in your private catalog is removed - kept
in the record as "unlist" until that worked, so a later publish tries again. Catalogs: a public workflow may be proposed to the
public catalog (a pull request); a private one only ever goes into your own private catalog, and
only after GitHub confirms that catalog is private and that you may write to it.

gh (the GitHub CLI, logged in) is needed for publishing only, never for using Durweg.
"""

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from . import catalog, gitops, library, workflow
from .util import WfError, now, read_json, rmtree, write_json

LICENSES = {"mit": "MIT", "apache-2.0": "Apache-2.0", "cc-by-4.0": "CC-BY-4.0", "none": None}
REPO = re.compile(r"^[A-Za-z0-9-]+/[A-Za-z0-9._-]+$")
PRIVATE_NAME = "durweg-workflows-private"
RECORD = ".durweg-publish.json"


class _tmpdir:
    """A temporary folder removed with durweg's rmtree (git's read-only files on Windows)."""

    def __enter__(self):
        self.path = tempfile.mkdtemp(prefix="durweg-catalog-")
        return self.path

    def __exit__(self, *exc):
        rmtree(self.path)
        return False


# -- gh ----------------------------------------------------------------------------------------
def gh(*args, check=True):
    exe = shutil.which("gh")
    if not exe:
        raise WfError("publishing needs the GitHub command gh (https://cli.github.com); install it, "
                      "then run `gh auth login` once")
    env = dict(gitops.env(), GH_PROMPT_DISABLED="1", GH_NO_UPDATE_NOTIFIER="1", NO_COLOR="1")
    try:
        r = subprocess.run([exe, *args], env=env, capture_output=True, text=True, timeout=120,
                           stdin=subprocess.DEVNULL, encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        raise WfError(f"gh {args[0]} gave no answer within 120 s")
    if check and r.returncode != 0:
        msg = gitops.redact((r.stderr or r.stdout).strip().splitlines()[-1] if (r.stderr or r.stdout).strip() else "")
        raise WfError(f"gh {' '.join(args[:2])} failed: {msg or 'exit ' + str(r.returncode)}")
    return r


def login():
    r = gh("api", "user", "--jq", ".login", check=False)
    if r.returncode != 0 or not r.stdout.strip():
        raise WfError("gh is not logged in to GitHub: run `gh auth login` and `gh auth setup-git` once")
    return r.stdout.strip()


def repo_info(repo):
    """{visibility, viewerPermission, url} or None when the repository does not exist (for us)."""
    r = gh("repo", "view", repo, "--json", "visibility,viewerPermission,url", check=False)
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except ValueError:
        return None


def github_repo(url):
    """owner/repo of a GitHub URL, or None."""
    m = re.match(r"^(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/)([^/]+/[^/]+?)(?:\.git)?/?$",
                 gitops.redact(url or ""))
    return m.group(1) if m else None


def catalog_ok(repo, info):
    """None when the repository holds a valid catalog.json (format 1), else the reason. Read only:
    a shallow clone into a temporary folder (U3: an existing repository is only read)."""
    url = (info or {}).get("url")
    if not url:
        return "GitHub does not show it to you"
    with _tmpdir() as tmp:
        try:
            gitops.run(["clone", "-q", "--depth", "1", "--", url, str(Path(tmp) / "c")], url=url)
            catalog._parse(repo, Path(tmp) / "c")
        except WfError as e:
            return f"it holds no valid catalog.json ({e})"
    return None


def private_ok(info):
    """None when a catalog repository may hold private workflows, else the reason (revision 3)."""
    if not info:
        return "GitHub does not show it to you (removed, or no access)"
    if str(info.get("visibility", "")).upper() != "PRIVATE":
        return "it is not private on GitHub (now: " + str(info.get("visibility", "?")).lower() + ")"
    if str(info.get("viewerPermission", "")).upper() not in ("WRITE", "MAINTAIN", "ADMIN"):
        return "you may not write to it"
    return None


# -- what is published --------------------------------------------------------------------------
def _source(name):
    e = library.entries().get(name)
    if not e:
        raise WfError(f"no workflow named {name} in the library")
    if e.get("source") == "plugin-example":
        raise WfError(f"{name} comes with Durweg; publish only workflows in your own folders")
    if e.get("source") == "plugin":
        raise WfError(f"{name} comes with the plugin {e.get('plugin', '?')}; publish only workflows in your own folders")
    if e.get("source") != "folder":
        raise WfError(f"{name} was installed from git ({gitops.redact(e.get('url', ''))}); "
                      "publish only workflows in your own folders")
    return e, workflow.load(Path(e["path"]))


def _readme(wf):
    lines = [f"# {wf.data.get('title') or wf.id}", "",
             f"A [Durweg](https://github.com/durweg/durweg) workflow: the steps below are done in order, "
             "each one checked before the next starts.", "", "## Steps", ""]
    for i, s in enumerate(wf.steps, 1):
        lines.append(f"{i}. **{s.get('title') or s['id']}**")
    lines += ["", "## Use it", "", "With Durweg installed:", "",
              f"1. `durweg library add <the address of this repository>`",
              f"2. Tell your agent: \"Run {wf.id} with durweg.\"", ""]
    return "\n".join(lines)


def _license_text(choice, owner):
    key = choice.lower()
    r = gh("api", f"licenses/{key}")
    try:
        body = json.loads(r.stdout)["body"]
    except (ValueError, KeyError):
        raise WfError(f"GitHub did not give the text of the {LICENSES[key]} license")
    year = now()[:4]
    return (body.replace("[year]", year).replace("[yyyy]", year)
                .replace("[fullname]", owner).replace("[name of copyright owner]", owner))


def files_of(wf, src, license_choice, case):
    """[(relative path, source path or None, text or None)] - exactly what goes into the repository."""
    out = [(rel, src / rel, None) for rel in workflow.snapshot_sources(wf)]
    # a README.md always (the public catalog needs one); a README_cn.md of the folder goes along
    out += [(p, src / p, None) for p in ("README.md", "README_cn.md") if (src / p).is_file()]
    if not (src / "README.md").is_file():
        out.append(("README.md", None, _readme(wf)))
    own_license = next((p for p in ("LICENSE", "LICENSE.md", "LICENSE.txt") if (src / p).is_file()), None)
    if own_license:
        out.append((own_license, src / own_license, None))
    elif license_choice and license_choice.lower() != "none":
        out.append(("LICENSE", None, ""))           # text filled in at --yes (needs gh)
    if case:
        out.append((f"case/{Path(case).name}", Path(case), None))
    seen, uniq = set(), []
    for item in out:
        if item[0] not in seen:
            seen.add(item[0])
            uniq.append(item)
    return uniq


# -- the plan ----------------------------------------------------------------------------------
# -- public publishing: what users type must be in English (v1.6.0, user 2026-11-03) -------------
CJK = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af\uff01-\uff60]")
TRANSLATED = re.compile(r"_(?:cn|zh)\.md$")


def _file_text(srcp, text):
    if text is not None:
        return text
    try:
        return Path(srcp).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def typed_text_findings(files):
    """CJK in what a reader of an English page types or copies: inline code, code blocks, quoted lines."""
    out = []
    for rel, srcp, text in files:
        if not rel.endswith(".md") or TRANSLATED.search(rel):
            continue
        fence = False
        for n, line in enumerate(_file_text(srcp, text).splitlines(), 1):
            if line.lstrip().startswith("```"):
                fence = not fence
                continue
            spans = [line] if fence or line.lstrip().startswith(">") else re.findall(r"`([^`]+)`", line)
            for s in spans:
                if CJK.search(s):
                    out.append(f"{rel}:{n}: {s.strip()[:80]}")
                    break
    return out


def english_readme(files):
    """True when README.md reads as English (most letters are not CJK)."""
    for rel, srcp, text in files:
        if rel == "README.md":
            body = _file_text(srcp, text)
            cjk = len(CJK.findall(body))
            latin = len(re.findall(r"[A-Za-z]", body))
            return cjk * 3 <= latin          # a CJK character carries about three letters' worth of text
    return False


def config_value(key):
    p = library.home() / "config.json"
    try:
        return json.loads(p.read_text(encoding="utf-8")).get(key) if p.is_file() else None
    except ValueError:
        return None


def prepare(name, visibility=None, repo=None, license_choice=None, case=None, catalog_answer=None,
            language_ok=False, english_readme_answer=None):
    """Everything that would happen, and the questions still open. Touches nothing."""
    entry, wf = _source(name)
    src = Path(entry["path"])
    stage = library.home() / "publish" / name
    record = _record(stage)
    owner = login()
    questions, notes = [], []

    if record:
        repo = repo or record["repo"]
        if repo != record["repo"]:
            raise WfError(f"{name} was published to {record['repo']} before; Durweg pushes only there "
                          f"(to start again elsewhere, remove {stage})")
    if repo:
        repo_from = "--repo" if not record else "the earlier publishing"
    else:
        default_owner = config_value("publish_owner")
        repo_from = "durweg config publish-owner" if default_owner else "your GitHub account"
        repo = f"{default_owner or owner}/durweg-{name}"
    if not REPO.match(repo):
        raise WfError(f"--repo is owner/name, not {repo!r}")
    info = repo_info(repo)
    went_public, unlist = False, None
    if record:
        if not info:
            raise WfError(f"{repo} is not on GitHub any more (or you lost access); nothing was pushed")
        on_github = str(info.get("visibility", "")).lower()
        if record["visibility"] == "private" and on_github == "public":
            # made public on GitHub by the user: followed, never the other way round
            if visibility == "private":
                raise WfError(f"{repo} is public on GitHub now; run it without --private to publish it as public")
            went_public, visibility = True, "public"
            notes.append(f"{repo} is public on GitHub now: the record changes from private to public")
            unlist = _unlist_target(record)
        else:
            visibility = visibility or record["visibility"]
            if visibility != record["visibility"]:
                raise WfError(f"{record['repo']} is {record['visibility']}; Durweg does not change that "
                              "(change it on GitHub yourself if you want to)")
            if on_github != record["visibility"]:
                raise WfError(f"{repo} is {on_github} on GitHub now, "
                              f"not {record['visibility']}; Durweg does not push to it")
            unlist = record.get("unlist")
        if unlist:
            note = _unlist_preview(unlist, name)
            if note:
                notes.append(note)
        action = f"push a new version to {repo}"
    elif info:
        raise WfError(f"{repo} exists on GitHub already and was not made by `durweg publish` here; "
                      "Durweg does not push to it: choose another name with --repo")
    else:
        action = f"create the {visibility or '?'} repository {repo} and push"
    if visibility not in ("public", "private"):
        questions.append("public or private? (--public or --private)")

    if case:
        c = Path(case).expanduser()
        cases = (library.home() / "cases").resolve()
        if not c.is_file() or c.suffix != ".html" or cases not in c.resolve().parents:
            raise WfError(f"--case is a page in {cases}, not {case}")
        case = c
    has_license = any((src / p).is_file() for p in ("LICENSE", "LICENSE.md", "LICENSE.txt"))
    if not has_license and license_choice is None:
        questions.append("which license? (--license MIT, Apache-2.0, CC-BY-4.0 or none)")
    if license_choice and license_choice.lower() not in LICENSES:
        raise WfError("--license is one of MIT, Apache-2.0, CC-BY-4.0, none")
    files = files_of(wf, src, license_choice, case)

    if visibility == "public":
        found = typed_text_findings(files)
        if catalog_answer == "yes" and p_entry_cjk(wf, name):   # the entry goes to the public catalog
            found.append(f"catalog entry: title or summary in workflow.json is not English ({p_entry_cjk(wf, name)})")
        if found and not language_ok:
            raise WfError("not published: a public workflow's English pages and catalog entry use English for what "
                          "people type (examples, trigger words, labels). Fix these, or pass --language-ok if they "
                          "are meant that way:\n  " + "\n  ".join(found))
        if found:
            notes.append(f"--language-ok: {len(found)} place(s) with CJK text in what people type are kept")
        if not english_readme(files):
            if english_readme_answer is None:
                questions.append("the README is not in English: add an English README.md first? "
                                 "(--english-readme add, or --english-readme skip to publish as it is)")
            elif english_readme_answer == "add":
                raise WfError("not published: write an English README.md (keep the other language as README_cn.md), "
                              "then run publish again")
            else:
                notes.append("published without an English README (--english-readme skip)")
    cat = _catalog_plan(name, visibility, owner, catalog_answer, has_license or
                        (license_choice and license_choice.lower() != "none"))
    if cat.get("question"):
        questions.append(cat["question"])
    notes += cat.get("notes", [])
    return {"name": name, "wf": wf, "src": src, "stage": stage, "repo": repo, "visibility": visibility,
            "owner": owner, "license": license_choice, "case": case, "files": files, "action": action,
            "catalog": cat, "questions": questions, "notes": notes, "record": record,
            "went_public": went_public, "unlist": unlist, "repo_from": repo_from}


def _record(stage):
    p = stage / RECORD
    try:
        return read_json(p) if p.is_file() else None
    except (OSError, ValueError):
        raise WfError(f"{p} cannot be read; fix or delete it")


def _unlist_target(record):
    """Where the entry of a workflow that went public is to be removed: your private catalog."""
    pid = catalog._load().get("private_default")
    entry = catalog.configured().get(pid) or {} if pid else {}
    target = entry.get("repo") or github_repo(entry.get("url", ""))
    if not (pid and target and record.get("url")):
        return None
    return {"id": pid, "target": target, "url": record["url"]}


def _unlist_preview(u, name):
    """The line for the plan. Only the newest copy of the catalog counts; a stale or missing cache
    never means "not listed" (PP-R-002). The removal itself checks again (_edit_catalog)."""
    url = (catalog.configured().get(u["id"]) or {}).get("url")
    try:
        reason = catalog.refresh(u["id"], url) if url else "it is not set up on this computer"
        if not reason:
            items, _ = catalog._parse(u["id"], catalog.cache_dir(u["id"]))
            e = items.get(name)
            if e and catalog.same_url(e["url"], u["url"]):
                return f"removed from your private catalog {u['id']} ({u['target']}), as it is public now"
            return None
    except (WfError, OSError) as e:
        reason = str(e)
    return (f"your private catalog {u['id']} could not be checked ({reason}); "
            "Durweg checks it again when publishing")


def _catalog_plan(name, visibility, owner, answer, licensed):
    """What happens with a catalog: {"do": ..., "question"?, "notes"?}."""
    if visibility == "public":
        if answer is None:
            return {"do": None, "question": "propose it to the public catalog, so others find it by name? "
                                             "(--catalog yes or --catalog no)"}
        if answer == "no":
            return {"do": "nothing"}
        if not licensed:
            raise WfError("the public catalog takes only workflows with a LICENSE; choose one with --license")
        pub = github_repo(catalog.public_url())
        if not pub:
            raise WfError(f"the public catalog {catalog.public_url()} is not on GitHub; no pull request possible")
        return {"do": "pr", "target": pub, "notes": [f"a pull request to {pub} that adds {name}; "
                                                       "it is listed once its owner merges it"]}
    if visibility != "private":
        return {"do": None}
    data = catalog._load()
    pid = data.get("private_default")
    if pid:
        entry = catalog.configured().get(pid) or {}
        target = entry.get("repo") or github_repo(entry.get("url", ""))
        reason = None if target else f"catalog {pid} is not a GitHub repository"
        if target:
            reason = private_ok(repo_info(target))
        if reason:
            return {"do": "nothing", "notes": [f"not added to your private catalog {pid}: {reason}; "
                                               "the workflow is published all the same"]}
        return {"do": "private", "id": pid, "target": target,
                "notes": [f"added to your private catalog {pid} ({target})"]}
    if data.get("private_declined") and answer is None:
        return {"do": "nothing", "notes": ["not added to a catalog (you chose no private catalog; "
                                           "`durweg catalog create-private` makes one)"]}
    target = f"{owner}/{PRIVATE_NAME}"
    info = repo_info(target)
    if info:
        reason = private_ok(info) or catalog_ok(target, info)
        if reason:
            return {"do": "nothing", "notes": [f"{target} exists but cannot be your private catalog: {reason}"]}
        q = f"use your existing private repository {target} as your private catalog? (--catalog yes or --catalog no)"
        adopt = True
    else:
        q = (f"make a private catalog {target}, so your other computers can install your private workflows "
             "by name? (--catalog yes or --catalog no)")
        adopt = False
    if answer is None:
        return {"do": None, "question": q}
    if answer == "no":
        return {"do": "decline", "notes": ["no private catalog: on another computer install it with "
                                           "`durweg library add <address>`"]}
    return {"do": "create-private", "target": target, "adopt": adopt,
            "notes": [f"{'use' if adopt else 'make'} the private catalog {target} and add this workflow"]}


def show(p):
    lines = [f"publish {p['name']} from {p['src']}",
             f"  to: {p['repo']} ({p['visibility'] or '?'}; owner from {p.get('repo_from', 'your GitHub account')})"
             f" - {p['action']}",
             "  files:"]
    lines += [f"    {rel}" + ("  (written by Durweg)" if srcp is None else "") for rel, srcp, _ in p["files"]]
    lines += [f"  {n}" for n in p["notes"]]
    if p["questions"]:
        lines.append("still to answer:")
        lines += [f"  - {q}" for q in p["questions"]]
    lines.append("nothing was published yet; with the user's yes, run the same command with --yes")
    return "\n".join(lines)


# -- doing it ----------------------------------------------------------------------------------
def _sync(p):
    """Make the staging repository hold exactly the files to publish; returns True if it changed."""
    stage = p["stage"]
    stage.mkdir(parents=True, exist_ok=True)
    if not (stage / ".git").is_dir():
        gitops.run(["init", "-q", "-b", "main"], cwd=stage)
        (stage / ".git" / "info").mkdir(exist_ok=True)
        (stage / ".git" / "info" / "exclude").write_text(RECORD + "\n", encoding="utf-8")
    want = {rel for rel, _, _ in p["files"]}
    for f in sorted(stage.rglob("*"), reverse=True):
        rel = f.relative_to(stage).as_posix()
        if rel.split("/")[0] == ".git" or rel == RECORD:
            continue
        if f.is_file() and rel not in want:
            f.unlink()
        elif f.is_dir() and not any(f.iterdir()):
            f.rmdir()
    for rel, srcp, text in p["files"]:
        dst = stage / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if srcp is not None:
            shutil.copy2(srcp, dst)                 # keeps the executable bit of scripts (V11-C-013)
        elif rel == "LICENSE":
            dst.write_text(_license_text(p["license"], p["owner"]), encoding="utf-8")
        else:
            dst.write_text(text, encoding="utf-8")
    gitops.run(["add", "-A"], cwd=stage)
    if not gitops.run(["status", "--porcelain"], cwd=stage).strip():
        return False
    ident = ["-c", f"user.name={p['owner']}", "-c", f"user.email={p['owner']}@users.noreply.github.com"]
    gitops.run([*ident, "commit", "-q", "-m", f"Publish {p['name']} from Durweg"], cwd=stage)
    return True


def publish(p):
    """Returns the lines to print. The workflow repository first; the catalog after, and a catalog
    problem never undoes a published workflow."""
    if p["questions"]:
        raise WfError("not published: answer first: " + "; ".join(p["questions"]))
    out = []
    if p.get("went_public"):
        now_vis = str((repo_info(p["repo"]) or {}).get("visibility", "")).upper()
        if now_vis != "PUBLIC":
            raise WfError(f"{p['repo']} is not public on GitHub any more ({now_vis.lower() or 'not shown'}); "
                          "nothing was pushed")
    changed = _sync(p)
    stage, rec = p["stage"], p["record"]
    if not rec:
        r = gh("repo", "create", p["repo"], f"--{p['visibility']}",
               "--description", f"Durweg workflow: {p['wf'].data.get('title') or p['name']}")
        info = repo_info(p["repo"]) or {}
        rec = {"repo": p["repo"], "visibility": p["visibility"], "url": info.get("url") or r.stdout.strip(),
               "created": now()}
        write_json(stage / RECORD, rec)            # written at once: a failed push is pushed by a rerun
        out.append(f"created {p['repo']} ({p['visibility']})")
    url = rec["url"]
    gitops.run(["push", "-q", url, "HEAD:main"], cwd=stage, url=url)
    rec["pushed"] = now()
    if p.get("went_public"):                       # only once the push worked (PP-R-003)
        rec["visibility"], rec["made_public"] = "public", now()
        if p.get("unlist"):
            rec["unlist"] = p["unlist"]
        out.append(f"the record of {p['name']} says public now, as {p['repo']} is public on GitHub")
    write_json(stage / RECORD, rec)
    out.append(f"pushed {'a new version' if changed else 'the same version'} to {url}")
    with library._IndexLock("library"):
        data = library._load("library.json", "workflows")
        if p["name"] in data["workflows"]:
            data["workflows"][p["name"]]["published"] = url
            write_json(library.home() / "library.json", data)
    if rec.get("unlist"):
        u = rec["unlist"]
        try:
            out += _unlist(p["name"], rec, stage)
        except (WfError, OSError, ValueError) as e:
            out.append(f"not removed from your private catalog {u['id']} yet: {e}; "
                       "Durweg tries again on the next publish")
    try:
        out += _do_catalog(p, url)
    except (WfError, OSError, ValueError) as e:
        out.append(f"the workflow is published, but the catalog step did not work: {e}")
    return out


def p_entry_cjk(wf, name):
    """The catalog entry's title or summary when it is not English, else None."""
    entry = {"title": wf.data.get("title") or name, "summary": wf.data.get("summary") or wf.data.get("title") or name}
    bad = [v for v in entry.values() if CJK.search(v)]
    return bad[0][:60] if bad else None


def _entry(p, url):
    return {"title": p["wf"].data.get("title") or p["name"],
            "summary": p["wf"].data.get("summary") or p["wf"].data.get("title") or p["name"], "url": url}


def _unlist(name, rec, stage):
    """Remove the entry of a workflow that is public now from the private catalog in the record.
    The record keeps "unlist" until it is removed, gone, or another workflow by that name."""
    u = rec["unlist"]
    reason = private_ok(repo_info(u["target"]))   # asked again right before writing
    if reason:
        return [f"still in your private catalog {u['id']}: {reason}; Durweg tries again on the next publish"]
    result = _edit_catalog(u["target"], name, None, remove_url=u["url"])
    del rec["unlist"]
    write_json(stage / RECORD, rec)
    if result == "gone":
        return []
    if result == "other":
        return [f"your private catalog {u['id']} lists another workflow named {name}; it was left alone"]
    out = [f"removed {name} from your private catalog {u['id']} ({u['target']})"]
    url = (catalog.configured().get(u["id"]) or {}).get("url")
    why = catalog.refresh(u["id"], url) if url else None
    if why:
        out.append(f"the copy of {u['id']} on this computer was not updated ({why}); "
                   "`durweg update` refreshes it")
    return out


def _do_catalog(p, url):
    c = p["catalog"]
    do = c.get("do")
    if do in (None, "nothing"):
        return list(c.get("notes", []))
    if do == "decline":
        with catalog._lock():
            data = catalog._load()
            data["private_declined"] = True
            catalog._save(data)
        return ["no private catalog (you will not be asked again; `durweg catalog create-private` makes one)"]
    if do == "pr":
        return [_pull_request(p, c["target"], url)]
    if do == "create-private":
        cid = create_private(p["owner"], adopt=c["adopt"])
        c = {"do": "private", "id": cid, "target": c["target"]}
    # write into the private catalog: GitHub is asked again right before (revision 3)
    reason = private_ok(repo_info(c["target"]))
    if reason:
        return [f"not added to your private catalog {c['id']}: {reason}; the workflow is published all the same"]
    _edit_catalog(c["target"], p["name"], _entry(p, url))
    catalog.refresh(c["id"], catalog.configured()[c["id"]]["url"])
    return [f"added {p['name']} to your private catalog {c['id']} ({c['target']})"]


def _edit_catalog(source, name, entry, dest=None, branch=None, remove_url=None):
    """Clone the newest catalog.json of `source`, add or replace one entry, and push: to `source`'s
    default branch, or (a pull request) to `branch` of `dest`, replacing an earlier version of that
    branch. A repository without a valid catalog.json is never written to (V11-C-011).
    entry=None removes `name`, only when its url is `remove_url` in that newest copy (PP-R-001), with
    a plain push that never overwrites newer commits. Returns "removed", "gone" or "other"."""
    src = repo_info(source) or {}
    if not src.get("url"):
        raise WfError(f"{source} cannot be read")
    to = repo_info(dest) if dest else src
    if not (to or {}).get("url"):
        raise WfError(f"{dest} cannot be read")
    with _tmpdir() as tmp:
        work = Path(tmp) / "c"
        gitops.clone(src["url"], work)
        catalog._parse(source, work)                               # refuses a missing or broken one
        f = work / "catalog.json"
        try:
            data = read_json(f)
        except (OSError, ValueError) as e:
            raise WfError(f"{source}: catalog.json cannot be read ({e})")
        result = None
        if entry is None:
            old = data["workflows"].get(name)
            if old is None:
                return "gone"
            if not (isinstance(old, dict) and catalog.same_url(str(old.get("url", "")), remove_url or "")):
                return "other"
            del data["workflows"][name]
            result = "removed"
        else:
            data["workflows"][name] = entry
        f.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        gitops.run(["add", "catalog.json"], cwd=work)
        owner = (dest or source).split("/")[0]
        ident = ["-c", f"user.name={owner}", "-c", f"user.email={owner}@users.noreply.github.com"]
        if gitops.run(["status", "--porcelain"], cwd=work).strip():
            msg = f"Remove {name} (public now)" if entry is None else f"Add {name}"
            gitops.run([*ident, "commit", "-q", "-m", msg], cwd=work)
        if branch:
            gitops.run(["push", "-q", "--", to["url"], f"+HEAD:refs/heads/{branch}"], cwd=work, url=to["url"])
        else:
            gitops.run(["push", "-q", "origin", "HEAD"], cwd=work, url=src["url"])
    return result


def _pull_request(p, upstream, url):
    me = p["owner"]
    branch = f"add-{p['name']}"
    if upstream.split("/")[0].lower() == me.lower():
        target = upstream                                       # your own catalog: a branch in it
        head = branch
    else:
        gh("repo", "fork", upstream, "--clone=false")
        target = f"{me}/{upstream.split('/')[1]}"
        head = f"{me}:{branch}"
    # from the catalog's newest version, not from an older fork (V11-C-012)
    _edit_catalog(upstream, p["name"], _entry(p, url), dest=target, branch=branch)
    r = gh("pr", "create", "--repo", upstream, "--head", head, "--title", f"Add {p['name']}",
           "--body", f"Adds the workflow {p['name']} ({url}), published with `durweg publish`.", check=False)
    if r.returncode == 0:
        return f"pull request to the public catalog: {r.stdout.strip() or 'opened'}"
    found = gh("pr", "list", "--repo", upstream, "--head", branch, "--state", "open", "--json", "url",
               "--jq", ".[0].url", check=False).stdout.strip()
    if found:
        return f"updated the open pull request to the public catalog: {found}"
    raise WfError(f"the pull request could not be opened: {gitops.redact((r.stderr or '').strip()[-200:])}")


def private_plan(owner):
    """For `durweg catalog create-private` without --yes: (what would happen, None) or (None, why not)."""
    target = f"{owner}/{PRIVATE_NAME}"
    info = repo_info(target)
    if not info:
        return f"make the private repository {target} with an empty catalog and use it as your private catalog", None
    reason = private_ok(info) or catalog_ok(target, info)
    if reason:
        return None, f"{target} exists and cannot be your private catalog: {reason}"
    return f"use your existing private repository {target} as your private catalog", None


def create_private(owner, adopt=None):
    """Make owner/durweg-workflows-private, or - only with adopt=True, after the user said yes -
    use an existing one, and record it as private_default. An existing repository must be private,
    writable for you and hold a valid catalog.json; it is only read. Nothing is written to
    catalogs.json before the catalog was downloaded and checked (V11-C-011). Returns the id."""
    target = f"{owner}/{PRIVATE_NAME}"
    cid = "private"
    existing = catalog._load()["catalogs"].get(cid)
    info = repo_info(target)
    if existing and not (info and catalog.same_url(existing.get("url", ""), info.get("url", ""))):
        raise WfError(f"a catalog named {cid} exists already ({gitops.redact(existing.get('url', ''))})")
    if info:
        if adopt is not True:
            raise WfError(f"{target} exists already; using it as your private catalog needs the user's yes")
        reason = private_ok(info) or catalog_ok(target, info)
        if reason:
            raise WfError(f"{target} cannot be your private catalog: {reason}")
    else:
        if adopt is True:
            raise WfError(f"{target} is not on GitHub (any more)")
        gh("repo", "create", target, "--private", "--description", "My private Durweg catalog")
        info = repo_info(target) or {}
        reason = private_ok(info)
        if reason:
            raise WfError(f"{target} was created but {reason}")
        with _tmpdir() as tmp:
            work = Path(tmp) / "c"
            work.mkdir()
            gitops.run(["init", "-q", "-b", "main"], cwd=work)
            (work / "catalog.json").write_text(json.dumps({"format": 1, "workflows": {}}, indent=2) + "\n",
                                               encoding="utf-8")
            (work / "README.md").write_text("My private Durweg catalog: `durweg catalog add private <this address>`.\n",
                                            encoding="utf-8")
            gitops.run(["add", "-A"], cwd=work)
            ident = ["-c", f"user.name={owner}", "-c", f"user.email={owner}@users.noreply.github.com"]
            gitops.run([*ident, "commit", "-q", "-m", "Private Durweg catalog"], cwd=work)
            gitops.run(["push", "-q", info["url"], "HEAD:main"], cwd=work, url=info["url"])
    url = info["url"]
    reason = catalog.refresh(cid, url)                       # downloads and checks it first
    if reason:
        raise WfError(f"{target} cannot be read as a catalog ({reason}); nothing was recorded")
    with catalog._lock():
        data = catalog._load()
        data["catalogs"][cid] = dict(data["catalogs"].get(cid, {}), url=url, repo=target)
        data["catalogs"][cid].setdefault("added", now())
        data["private_default"] = cid
        data.pop("private_declined", None)
        catalog._save(data)
    return cid
