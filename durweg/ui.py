"""durweg ui: a management page on this computer (plan durweg-dev plans/20261103_durweg-ui.md).

Steps 2 and 3 of the plan: the security skeleton and the read-only pages. The server binds 127.0.0.1 on a port the system picks,
serves a fixed set of built-in files, and accepts a write only as a POST that carries the start
token in the X-Durweg-Token header, the exact Host and a same-origin Origin (section 5). Reads are
GETs and never write. The changes (add, remove, update, catalogs) come in step 4; until then the
only write is "noop".

Standard library only; Python 3.9+.
"""

import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

SCHEMA = 1
MAX_BODY = 16 * 1024
IDLE_SECONDS = 30 * 60
TOKEN_HEADER = "X-Durweg-Token"

SECURITY_HEADERS = {
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": ("default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; "
                                "img-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"),
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
}

# ---------------------------------------------------------------- parameter checks (UI-R-010)
# The page's own whitelist; the durweg command still checks everything again.
NAME = re.compile(r"[a-z0-9][a-z0-9-]{0,63}")
CATALOG = re.compile(r"[a-z0-9][a-z0-9-]{1,31}")
URL_HTTPS = re.compile(r"https://[A-Za-z0-9.-]+(:[0-9]{1,5})?(/[A-Za-z0-9._~%/-]*)?")
URL_SSH = re.compile(r"git@[A-Za-z0-9.-]+:[A-Za-z0-9._~/-]+")


class BadRequest(Exception):
    """A request the page refuses (400, or 403 for a failed write check)."""

    def __init__(self, msg, status=400):
        super().__init__(msg)
        self.status = status


def _plain(value, what):
    if not isinstance(value, str):
        raise BadRequest(f"{what} must be text")
    if value.startswith("-"):
        raise BadRequest(f"{what} may not start with '-'")
    if any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in value):
        raise BadRequest(f"{what} may not contain spaces or control characters")
    return value


def check_name(value):
    if not NAME.fullmatch(_plain(value, "a workflow name")):
        raise BadRequest("a workflow name is lower-case letters, digits and -, at most 64 characters")
    return value


def check_catalog(value):
    if not CATALOG.fullmatch(_plain(value, "a catalog id")):
        raise BadRequest("a catalog id is lower-case letters, digits and -, 2 to 32 characters")
    return value


def split_ref(value):
    """'<catalog>:<name>' split at the first ':' (each side checked), or a plain name -> (catalog|None, name)."""
    _plain(value, "a workflow")
    if ":" in value:
        cat, name = value.split(":", 1)
        return check_catalog(cat), check_name(name)
    return None, check_name(value)


def check_url(value):
    _plain(value, "an address")
    if len(value) > 300:
        raise BadRequest("an address is at most 300 characters")
    if not (URL_HTTPS.fullmatch(value) or URL_SSH.fullmatch(value)):
        raise BadRequest("an address must be https://… or git@host:path")
    if "@" in value.split("//", 1)[-1].split("/", 1)[0] and value.startswith("https://"):
        raise BadRequest("an address may not carry a user name or password")
    return value


def check_fields(body, allowed):
    """The JSON body is an object with only the allowed fields."""
    if not isinstance(body, dict):
        raise BadRequest("the request body must be a JSON object")
    extra = sorted(set(body) - set(allowed))
    if extra:
        raise BadRequest(f"unknown field: {', '.join(extra)}")
    return body


# ---------------------------------------------------------------- write checks (UI-R-001)
def write_refusal(method, headers, port, token):
    """Why this request may not write (None when it may). headers: a case-insensitive mapping."""
    if method != "POST":
        return "writes are POST only"
    given = headers.get(TOKEN_HEADER) or ""
    if not token or not secrets.compare_digest(given.encode(), token.encode()):
        return "missing or wrong token: open the page again with the link printed in the terminal"
    host = headers.get("Host") or ""
    allowed = {f"127.0.0.1:{port}", f"localhost:{port}"}
    if host not in allowed:
        return "wrong Host"
    origin = headers.get("Origin") or ""
    if origin not in {f"http://{h}" for h in allowed}:
        return "missing or foreign Origin"
    if origin != f"http://{host}":
        return "Origin and Host differ"
    ctype = (headers.get("Content-Type") or "").split(";")[0].strip().lower()
    if ctype != "application/json":
        return "Content-Type must be application/json"
    return None


# ---------------------------------------------------------------- running durweg … --json
# The only commands the page runs (plan section 9, UI-R-009): argv lists, no shell, the same
# durweg as this one (python -m durweg), so the page and the command line give the same answers.
PKG_PARENT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAIL = 200


def durweg_json(args, timeout=120):
    """Run `durweg <args> --json`; its JSON object, or {"ok": False, "error": ...}. Never raises."""
    from .gitops import redact
    argv = [sys.executable, "-m", "durweg", *args, "--json"]
    path = os.environ.get("PYTHONPATH")
    env = dict(os.environ, PYTHONPATH=PKG_PARENT + (os.pathsep + path if path else ""))
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL,
                           env=env, cwd=os.path.expanduser("~"))
    except subprocess.TimeoutExpired:
        return {"schema": SCHEMA, "ok": False, "error": f"durweg {args[0]} did not finish in {timeout} s", "timeout": True}
    except OSError as e:
        return {"schema": SCHEMA, "ok": False, "error": f"durweg could not be started ({e.strerror})"}
    try:
        out = json.loads(r.stdout)
        if not isinstance(out, dict):
            raise ValueError
    except ValueError:
        tail = "\n".join(redact(r.stderr or r.stdout or "").splitlines()[-TAIL:])
        return {"schema": SCHEMA, "ok": False, "error": f"durweg {args[0]} failed (exit {r.returncode})", "output": tail}
    return out


def _version_and_language():
    from . import __version__
    from .publish import config_value
    lang = config_value("language")
    return {"version": __version__, "language": lang if lang in ("en", "zh") else "en"}


# ---------------------------------------------------------------- actions
def action_noop(body):
    check_fields(body, ())
    return {"done": "nothing"}


READS = {   # path -> function returning the JSON object to send (it carries its own "ok")
    "/api/ping": lambda: dict({"schema": SCHEMA, "ok": True}, **_version_and_language()),
    "/api/available": lambda: durweg_json(["library", "available"]),
    "/api/installed": lambda: durweg_json(["library", "list"]),
    "/api/catalogs": lambda: durweg_json(["catalog", "list"]),
    "/api/doctor": lambda: durweg_json(["doctor"]),
}
WRITES = {"/api/noop": action_noop}   # step 4 adds the changes


# ---------------------------------------------------------------- built-in files
HERE = os.path.dirname(os.path.abspath(__file__))
STATIC = {   # path -> (file in durweg/ui_static, content type); nothing else is ever served
    "/": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/app.css": ("app.css", "text/css; charset=utf-8"),
}


def _static(path):
    name, ctype = STATIC[path]
    with open(os.path.join(HERE, "ui_static", name), "rb") as f:
        return f.read(), ctype


# ---------------------------------------------------------------- server
class Handler(BaseHTTPRequestHandler):
    server_version = "durweg-ui"
    sys_version = ""
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):      # no request log: the first URL carries the token
        pass

    def _send(self, status, body, ctype="application/json; charset=utf-8"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status)
        for k, v in SECURITY_HEADERS.items():
            self.send_header(k, v)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _error(self, status, msg):
        self._send(status, {"schema": SCHEMA, "ok": False, "error": msg})

    def _host_ok(self):
        port = self.server.server_address[1]
        return (self.headers.get("Host") or "") in {f"127.0.0.1:{port}", f"localhost:{port}"}

    def do_GET(self):
        self.server.touch()
        path = urlsplit(self.path).path
        if not self._host_ok():                     # DNS rebinding: another name pointing at 127.0.0.1
            return self._error(403, "wrong Host")
        if path in STATIC:
            body, ctype = _static(path)
            return self._send(200, body, ctype)
        if path in READS:
            return self._send(200, READS[path]())
        if path in WRITES:
            return self._error(405, "writes are POST only")
        return self._error(404, "not found")

    do_HEAD = do_GET

    def do_POST(self):
        self.server.touch()
        path = urlsplit(self.path).path
        refusal = write_refusal("POST", self.headers, self.server.server_address[1], self.server.token)
        if refusal:
            return self._error(403, refusal)
        if path not in WRITES:
            return self._error(404, "not found")
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return self._error(400, "bad Content-Length")
        if n > MAX_BODY:
            return self._error(413, "request too large")
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
        except ValueError:
            return self._error(400, "the request body is not JSON")
        if not self.server.write_lock.acquire(blocking=False):
            return self._error(409, "another change is running; wait until it ends")
        try:
            return self._send(200, dict({"schema": SCHEMA, "ok": True}, **WRITES[path](body)))
        except BadRequest as e:
            return self._error(e.status, str(e))
        finally:
            self.server.write_lock.release()

    def _refuse_method(self):
        self._error(405, "method not allowed")

    do_PUT = do_DELETE = do_PATCH = do_OPTIONS = _refuse_method


class UIServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, idle=IDLE_SECONDS):
        super().__init__(("127.0.0.1", 0), Handler)      # bind 0: the system picks a free port
        self.token = secrets.token_urlsafe(32)
        self.write_lock = threading.Lock()
        self.idle = idle
        self.last = time.monotonic()

    def touch(self):
        self.last = time.monotonic()

    @property
    def port(self):
        return self.server_address[1]

    def start_url(self):
        return f"http://127.0.0.1:{self.port}/?t={self.token}"

    def serve_until_idle(self):
        def watch():
            while True:
                time.sleep(min(30, max(1, self.idle / 4)))
                if time.monotonic() - self.last > self.idle:
                    self.shutdown()
                    return
        threading.Thread(target=watch, daemon=True).start()
        self.serve_forever()


# ---------------------------------------------------------------- opening a browser
def is_wsl():
    try:
        with open("/proc/version", encoding="utf-8", errors="replace") as f:
            return "microsoft" in f.read().lower()
    except OSError:
        return False


def open_browser(url):
    """Try to open url in a browser; True when a launcher accepted it. Never raises.
    WSL: wslview, else explorer.exe (Windows opens WSL's localhost). Elsewhere: the webbrowser module."""
    try:
        if is_wsl():
            for cmd in (["wslview", url], ["explorer.exe", url]):
                if shutil.which(cmd[0]):
                    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return True
            return False
        if sys.platform.startswith("linux") and not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
            return False                                  # no graphical session (SSH, a server)
        import webbrowser
        return bool(webbrowser.open(url))
    except Exception:
        return False


def run(no_browser=False, idle=IDLE_SECONDS, out=None):
    out = out or sys.stdout
    srv = UIServer(idle=idle)
    url = srv.start_url()
    print("Durweg management page (this computer only):", file=out)
    print(f"  {url}", file=out)
    print("Open that link; after a refresh, open it again from here. Ctrl-C stops it "
          f"(it also stops after {idle // 60} minutes without use).", file=out)
    out.flush()
    if not no_browser and not open_browser(url):
        print("No browser could be opened: copy the link above into your browser.", file=out)
    try:
        srv.serve_until_idle()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
    return 0
