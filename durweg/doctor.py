"""durweg doctor: what this computer has for Durweg, in three layers (plan durweg-ui, section 3 and UI-R-009).

1. agent installed: claude / codex / agy found on PATH (or in their usual folders);
2. Durweg reachable from that agent: as its plugin, or through the skills the installer linked;
3. GitHub: gh installed and signed in (only the account name is read, never a token).
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

from . import __version__
from .util import plugin_copies, plugin_host, plugin_root

AGENTS = (  # (id, name shown, command, the folder it reads skills from)
    ("claude", "Claude Code", "claude", lambda: Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude") / "skills"),
    ("codex", "Codex", "codex", lambda: Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex") / "skills"),
    ("agy", "Antigravity", "agy", lambda: Path.home() / ".gemini" / "config" / "skills"),
)
SKILL = "run-workflow"


def _which(cmd):
    found = shutil.which(cmd)
    if found:
        return found
    for d in (Path.home() / ".local" / "bin", Path.home() / ".codex" / "bin"):    # installer's usual places
        if (d / cmd).is_file() and os.access(d / cmd, os.X_OK):
            return str(d / cmd)
    return None


def agents():
    plugins = {agent for agent, _ in plugin_copies()}
    out = []
    for aid, name, cmd, skills in AGENTS:
        plugin = name in plugins
        linked = (skills() / SKILL).exists()
        out.append({"id": aid, "name": name, "installed": _which(cmd) is not None,
                    "durweg": "plugin" if plugin else "skills" if linked else None})
    return out


def github(timeout=20):
    """{"gh": bool, "signed_in": bool|None, "account": str|None, "note": str|None}. None = could not tell."""
    gh = shutil.which("gh")
    if not gh:
        return {"gh": False, "signed_in": False, "account": None, "note": "gh is not installed"}
    try:
        r = subprocess.run([gh, "auth", "status", "--json", "hosts"], capture_output=True, text=True,
                           timeout=timeout, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired) as e:
        return {"gh": True, "signed_in": None, "account": None, "note": f"gh auth status did not answer ({type(e).__name__})"}
    try:
        hosts = json.loads(r.stdout).get("hosts")      # signed out: {"hosts": {}}
    except (ValueError, AttributeError):
        hosts = None
    if not isinstance(hosts, dict):
        return {"gh": True, "signed_in": None, "account": None, "note": "gh is too old to report its sign-in"}
    for acct in hosts.get("github.com") or []:        # only these three fields are read
        if acct.get("active") and acct.get("state") == "success":
            return {"gh": True, "signed_in": True, "account": str(acct.get("login") or "") or None, "note": None}
    return {"gh": True, "signed_in": False, "account": None, "note": None}


def report():
    root = plugin_root()
    return {"durweg": {"version": __version__, "plugin": (plugin_host(root) or "unknown") if root else None},
            "agents": agents(), "github": github()}


def show(rep):
    lines = [f"durweg {rep['durweg']['version']}" + (f" (plugin: {rep['durweg']['plugin']})" if rep["durweg"]["plugin"] else "")]
    for a in rep["agents"]:
        if not a["installed"] and not a["durweg"]:
            lines.append(f"{a['name']:12} not installed")
            continue
        how = {"plugin": "has the Durweg plugin", "skills": "has Durweg's skills", None: "does not have Durweg yet"}[a["durweg"]]
        lines.append(f"{a['name']:12} {'installed' if a['installed'] else 'not on PATH'}; {how}")
    g = rep["github"]
    if not g["gh"]:
        lines.append("GitHub       gh is not installed (needed only for private catalogs and publishing)")
    elif g["signed_in"]:
        lines.append(f"GitHub       signed in as {g['account']}")
    elif g["signed_in"] is None:
        lines.append(f"GitHub       unknown: {g['note']}")
    else:
        lines.append("GitHub       not signed in; in a terminal: gh auth login --web")
    return "\n".join(lines)
