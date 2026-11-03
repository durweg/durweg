"""durweg ui, step 2: the security contract (plan durweg-dev plans/20261103_durweg-ui.md, section 5).

A real server on 127.0.0.1 with raw HTTP requests, the way a hostile web page or a DNS-rebinding
name would send them.
"""

import http.client
import json
import os
import sys
import threading
import unittest

import helpers  # noqa: F401  (puts the checkout on sys.path)
from durweg import ui


class Server(unittest.TestCase):
    def setUp(self):
        self.srv = ui.UIServer(idle=3600)
        self.port = self.srv.port
        self.th = threading.Thread(target=self.srv.serve_forever, daemon=True)
        self.th.start()
        self.origin = f"http://127.0.0.1:{self.port}"
        self.good = {"Host": f"127.0.0.1:{self.port}", "Origin": self.origin,
                     "X-Durweg-Token": self.srv.token, "Content-Type": "application/json"}

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()

    def req(self, method, path, headers=None, body=None):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        c.putrequest(method, path, skip_host=True, skip_accept_encoding=True)
        for k, v in (headers or {}).items():
            c.putheader(k, v)
        data = body.encode() if isinstance(body, str) else (body or b"")
        c.putheader("Content-Length", str(len(data)))
        c.endheaders(data)
        r = c.getresponse()
        raw = r.read()
        c.close()
        try:
            j = json.loads(raw)
        except ValueError:
            j = None
        return r.status, dict(r.getheaders()), raw, j

    def post(self, path="/api/noop", drop=(), body="{}", **override):
        h = {k: v for k, v in self.good.items() if k not in drop}
        h.update({k.replace("_", "-"): v for k, v in override.items()})
        return self.req("POST", path, h, body)

    # -- binding and pages
    def test_binds_loopback_on_a_system_port(self):
        self.assertEqual(self.srv.server_address[0], "127.0.0.1")
        self.assertNotEqual(self.port, 0)
        self.assertGreaterEqual(len(self.srv.token), 40)
        other = ui.UIServer(idle=10)
        self.assertNotEqual(other.token, self.srv.token)       # a new token every start
        other.server_close()

    def test_only_the_built_in_files(self):
        h = {"Host": f"127.0.0.1:{self.port}"}
        for path in ("/", "/app.js", "/app.css", "/api/ping"):
            self.assertEqual(self.req("GET", path, h)[0], 200, path)
        for path in ("/ui.py", "/../cli.py", "/ui_static/index.html", "/etc/passwd", "/%2e%2e/ui.py", "/index.html"):
            self.assertEqual(self.req("GET", path, h)[0], 404, path)

    def test_security_headers_on_every_answer(self):
        for path in ("/", "/nothing"):
            _, headers, _, _ = self.req("GET", path, {"Host": f"127.0.0.1:{self.port}"})
            for k, v in ui.SECURITY_HEADERS.items():
                self.assertEqual(headers.get(k), v, (path, k))
            self.assertNotIn("Access-Control-Allow-Origin", headers)
        _, headers, _, _ = self.post(Origin="http://evil.example")
        self.assertEqual(headers.get("Referrer-Policy"), "no-referrer")
        self.assertNotIn("Access-Control-Allow-Origin", headers)

    def test_wrong_host_is_refused_even_for_reads(self):        # DNS rebinding
        st, _, _, j = self.req("GET", "/api/ping", {"Host": f"evil.example:{self.port}"})
        self.assertEqual((st, j["error"]), (403, "wrong Host"))
        self.assertEqual(self.req("GET", "/", {})[0], 403)

    def test_page_takes_the_token_out_of_the_address_and_never_stores_it(self):
        js = self.req("GET", "/app.js", {"Host": f"127.0.0.1:{self.port}"})[2].decode()
        self.assertIn("history.replaceState", js)
        for store in ("localStorage", "sessionStorage", "document.cookie", "innerHTML"):
            self.assertNotIn(store, js)
        html = self.req("GET", "/", {"Host": f"127.0.0.1:{self.port}"})[2].decode()
        self.assertNotIn("<script>", html)                         # no inline script (CSP)
        self.assertNotIn(self.srv.token, html)

    # -- writes
    def test_a_good_write(self):
        st, _, _, j = self.post()
        self.assertEqual((st, j), (200, {"schema": 1, "ok": True, "done": "nothing"}))
        st, _, _, j = self.post(Host=f"localhost:{self.port}", Origin=f"http://localhost:{self.port}")
        self.assertEqual(st, 200)

    def test_writes_are_post_only(self):
        h = dict(self.good)
        for m in ("GET", "PUT", "DELETE", "PATCH", "OPTIONS"):
            st, _, _, j = self.req(m, "/api/noop", h)
            self.assertEqual(st, 405, m)
        st, _, _, _ = self.req("GET", f"/api/noop?t={self.srv.token}", {"Host": f"127.0.0.1:{self.port}"})
        self.assertEqual(st, 405)                                   # a token in a GET writes nothing

    def test_token(self):
        self.assertIn("token", self.post(drop=("X-Durweg-Token",))[3]["error"])
        self.assertEqual(self.post(X_Durweg_Token="x" * 43)[0], 403)
        self.assertEqual(self.post(X_Durweg_Token=self.srv.token[:-1])[0], 403)

    def test_hostile_page_form_and_fetch(self):
        # an HTML form from another site: no token header, foreign Origin, form content type
        st, _, _, j = self.req("POST", "/api/noop", {"Host": f"127.0.0.1:{self.port}", "Origin": "http://evil.example",
                                                     "Content-Type": "application/x-www-form-urlencoded"}, "a=1")
        self.assertEqual(st, 403)
        # fetch from another site that somehow knows the token: Origin still gives it away
        self.assertEqual(self.post(Origin="http://evil.example")[0], 403)
        self.assertEqual(self.post(Origin="null")[0], 403)
        self.assertEqual(self.post(drop=("Origin",))[0], 403)
        self.assertEqual(self.post(Origin=f"http://127.0.0.1:{self.port + 1}")[0], 403)
        self.assertEqual(self.post(Origin=f"https://127.0.0.1:{self.port}")[0], 403)
        self.assertEqual(self.post(Origin=f"http://localhost:{self.port}")[3]["error"], "Origin and Host differ")
        self.assertEqual(self.post(Host=f"evil.example:{self.port}")[0], 403)
        self.assertEqual(self.post(Content_Type="text/plain")[0], 403)

    def test_body(self):
        self.assertEqual(self.post(body="not json")[0], 400)
        self.assertEqual(self.post(body='{"x": 1}')[3]["error"], "unknown field: x")
        self.assertEqual(self.post(body="[]")[0], 400)
        self.assertEqual(self.post(body="{" + " " * (ui.MAX_BODY + 1) + "}")[0], 413)
        self.assertEqual(self.post(path="/api/other")[0], 404)

    def task(self, **body):
        return self.post(path="/api/task", body=json.dumps(body))

    def wait(self, tid, states=("success", "partial", "failed", "timeout")):
        for _ in range(200):
            for tk in self.req("GET", "/api/tasks", {"Host": f"127.0.0.1:{self.port}"})[3]["tasks"]:
                if tk["id"] == tid and tk["state"] in states:
                    return tk
            threading.Event().wait(0.05)
        self.fail(f"task {tid} never reached {states}")

    def test_tasks_run_one_at_a_time_and_a_double_click_is_one_task(self):
        gate, calls = threading.Event(), []

        def fake(args, timeout=0):
            calls.append(args)
            gate.wait(5)
            return {"schema": 1, "ok": True, "name": "x"}
        old, ui.durweg_json = ui.durweg_json, fake
        try:
            a = self.task(action="library-add", ref="public:todo-daily")[3]["task"]
            b = self.task(action="library-add", ref="public:todo-daily")[3]["task"]
            c = self.task(action="library-remove", name="old-one")[3]["task"]
            self.assertEqual(a["id"], b["id"])                       # the same change: one task
            self.wait(a["id"], ("running",))
            self.assertEqual(self.wait(c["id"], ("queued",))["state"], "queued")
            gate.set()
            self.assertEqual(self.wait(c["id"])["state"], "success")
        finally:
            ui.durweg_json = old
        self.assertEqual(calls, [["library", "add", "public:todo-daily"], ["library", "remove", "old-one"]])

    def test_tasks_check_their_fields(self):
        for body, msg in (({"action": "rm -rf"}, "unknown action"), ({"action": "library-add", "ref": "--dev"}, "may not start"),
                          ({"action": "library-add", "ref": "x", "path": "/"}, "unknown field: path"),
                          ({"action": "catalog-add", "id": "team", "url": "file:///etc"}, "https://"),
                          ({"action": "library-remove"}, "must be text"),
                          ({"action": "private-create", "would": "anything"}, "preview first")):
            st, _, _, j = self.task(**body)
            self.assertEqual(st, 400, body)
            self.assertIn(msg, j["error"], body)

    def test_private_catalog_needs_the_shown_preview(self):
        seen = []

        def fake(args, timeout=0):
            seen.append(args)
            if args[-1] == "--yes":
                return {"schema": 1, "ok": True, "preview": False, "id": "private"}
            return {"schema": 1, "ok": True, "preview": True, "account": "someone",
                    "would": "create someone/durweg-workflows-private"}
        old, ui.durweg_json = ui.durweg_json, fake
        try:
            tid = self.task(action="private-preview")[3]["task"]["id"]
            self.wait(tid)
            self.assertEqual(self.task(action="private-create", would="create other/thing")[0], 400)
            tid = self.task(action="private-create", would="create someone/durweg-workflows-private")[3]["task"]["id"]
            self.assertEqual(self.wait(tid)["state"], "success")
            self.assertEqual(self.task(action="private-create", would="create someone/durweg-workflows-private")[0], 400)
        finally:
            ui.durweg_json = old
        self.assertEqual(seen, [["catalog", "create-private"], ["catalog", "create-private", "--yes"]])

    def test_task_states_and_restart(self):
        self.assertEqual(ui.task_state({"ok": True}), "success")
        self.assertEqual(ui.task_state({"ok": False, "timeout": True}), "timeout")
        self.assertEqual(ui.task_state({"ok": False, "items": [{"status": "updated"}, {"status": "failed"}]}), "partial")
        self.assertEqual(ui.task_state({"ok": False, "error": "x"}), "failed")
        old, ui.durweg_json = ui.durweg_json, lambda a, timeout=0: {"ok": True, "durweg": {"restart_ui": True}, "items": []}
        try:
            self.wait(self.task(action="update")[3]["task"]["id"])
        finally:
            ui.durweg_json = old
        self.assertTrue(self.req("GET", "/api/tasks", {"Host": f"127.0.0.1:{self.port}"})[3]["restart_ui"])

    def test_idle_stop(self):
        srv = ui.UIServer(idle=1)
        th = threading.Thread(target=srv.serve_until_idle, daemon=True)
        th.start()
        th.join(5)
        self.assertFalse(th.is_alive())
        srv.server_close()


class Checks(unittest.TestCase):
    def test_names_and_refs(self):
        self.assertEqual(ui.split_ref("public:todo-daily"), ("public", "todo-daily"))
        self.assertEqual(ui.split_ref("todo-daily"), (None, "todo-daily"))
        for bad in ("-x", "--dev", "Todo", "a b", "a\nb", "x" * 65, "", "a:b:c", "p:-x", "../x", "a/b"):
            with self.assertRaises(ui.BadRequest, msg=bad):
                ui.split_ref(bad)
        with self.assertRaises(ui.BadRequest):
            ui.check_catalog("x")
        with self.assertRaises(ui.BadRequest):
            ui.check_name(5)

    def test_urls(self):
        for good in ("https://github.com/durweg/durweg-workflows", "git@github.com:me/private-catalog.git"):
            self.assertEqual(ui.check_url(good), good)
        for bad in ("http://github.com/x", "file:///etc", "https://user:pw@github.com/x", "ext::sh -c x",
                    "-uhttps://x", "https://github.com/x y", "https://github.com/" + "a" * 300,
                    "git@github.com:x;rm", "https://github.com/x?y=1"):
            with self.assertRaises(ui.BadRequest, msg=bad):
                ui.check_url(bad)

    def test_write_refusal_is_pure(self):
        h = {"X-Durweg-Token": "t", "Host": "127.0.0.1:5", "Origin": "http://127.0.0.1:5",
             "Content-Type": "application/json; charset=utf-8"}
        self.assertIsNone(ui.write_refusal("POST", h, 5, "t"))
        self.assertEqual(ui.write_refusal("GET", h, 5, "t"), "writes are POST only")
        self.assertIsNotNone(ui.write_refusal("POST", h, 5, ""))     # no token configured: never


class Launch(unittest.TestCase):
    def test_start_link_and_no_request_log(self):
        srv = ui.UIServer(idle=10)
        try:
            self.assertEqual(srv.start_url(), f"http://127.0.0.1:{srv.port}/?t={srv.token}")
        finally:
            srv.server_close()
        self.assertIsNone(ui.Handler.log_message(None, "%s", "x"))

    def test_no_graphical_session_only_prints(self):
        if ui.is_wsl() or not sys.platform.startswith("linux"):
            self.skipTest("Linux without WSL only")
        env = {k: os.environ.pop(k) for k in ("DISPLAY", "WAYLAND_DISPLAY") if k in os.environ}
        try:
            self.assertFalse(ui.open_browser("http://127.0.0.1:1/"))
        finally:
            os.environ.update(env)


if __name__ == "__main__":
    unittest.main()
