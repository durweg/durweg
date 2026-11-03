"""--json for programs (plan durweg-ui UI-R-009): library list / available, catalog list, doctor; and
the read pages of durweg ui, which run exactly these commands."""

import http.client
import json
import os
import stat
import threading
import unittest
from pathlib import Path

from test_catalog import CatalogCase
from durweg import doctor, ui


def one_json(text):
    """The output is exactly one JSON object (nothing else on stdout)."""
    obj = json.loads(text)
    assert isinstance(obj, dict)
    return obj


class Json(CatalogCase):
    def test_library_list(self):
        self.assertEqual(one_json(self.wf("library", "list", "--json")), {"schema": 1, "ok": True, "items": []})
        self.wf("library", "add", "mini")
        j = one_json(self.wf("library", "list", "--json"))
        [it] = j["items"]
        self.assertEqual((it["name"], it["valid"]), ("mini", True))
        self.assertIsInstance(it["platforms"], list)
        self.assertTrue(it["url"])

    def test_available_marks_installed_and_gives_platforms_only_then(self):
        j = one_json(self.wf("library", "available", "--json"))
        self.assertEqual(j["catalogs_on"], ["public"])
        [it] = j["items"]
        self.assertEqual((it["ref"], it["title"], it["summary"], it["installed_as"], it["platforms"]),
                         ("public:mini", "Mini", "a tiny example", None, None))
        self.wf("library", "add", "mini")
        [it] = one_json(self.wf("library", "available", "--json"))["items"]
        self.assertEqual(it["installed_as"], "mini")
        self.assertIsInstance(it["platforms"], list)

    def test_unreachable_catalog_is_a_note_not_a_failure(self):
        url = self.catalog("gone", {})
        self.wf("catalog", "add", "gone", url)
        import shutil
        shutil.rmtree(url)                                   # the remote disappears; the cached copy stays
        j = one_json(self.wf("library", "available", "--json"))
        self.assertTrue(j["ok"])
        self.assertTrue(any("gone" in n for n in j["notes"]))

    def test_catalog_list_hides_credentials(self):
        self.wf("catalog", "add", "mine", self.catalog("mine", {}))
        cfg = Path(os.environ["DURWEG_HOME"]) / "catalogs.json"
        data = json.loads(cfg.read_text())
        data["catalogs"]["mine"]["url"] = "https://someone:secret@example.invalid/cat.git"
        cfg.write_text(json.dumps(data))
        j = one_json(self.wf("catalog", "list", "--json"))
        urls = {it["id"]: it["url"] for it in j["items"]}
        self.assertNotIn("secret", json.dumps(j))
        self.assertIn("mine", urls)

    def test_errors_are_json_too(self):
        out = self.wf("library", "add", "mini", "--json", expect=1)
        self.assertEqual(one_json(out), {"schema": 1, "ok": False, "error": "--json is not available for library add yet"})
        out = self.wf("catalog", "remove", "public", "--json", expect=1)
        self.assertFalse(one_json(out)["ok"])


@unittest.skipIf(os.name == "nt", "fake tools are shell scripts")
class Doctor(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = Path(tempfile.mkdtemp())
        self.old = {k: os.environ.get(k) for k in ("HOME", "PATH", "CLAUDE_CONFIG_DIR", "CODEX_HOME")}
        home = self.tmp / "home"
        (home / "bin").mkdir(parents=True)
        os.environ.update(HOME=str(home), PATH=str(home / "bin"), CLAUDE_CONFIG_DIR=str(home / ".claude"),
                          CODEX_HOME=str(home / ".codex"))
        self.home = home

    def tearDown(self):
        import shutil
        for k, v in self.old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(self.tmp, ignore_errors=True)

    def tool(self, name, script="exit 0"):
        p = self.home / "bin" / name
        p.write_text(f"#!/bin/sh\n{script}\n")
        p.chmod(p.stat().st_mode | stat.S_IEXEC)

    def test_nothing_installed(self):
        rep = doctor.report()
        self.assertEqual([(a["id"], a["installed"], a["durweg"]) for a in rep["agents"]],
                         [("claude", False, None), ("codex", False, None), ("agy", False, None)])
        self.assertEqual(rep["github"], {"gh": False, "signed_in": False, "account": None, "note": "gh is not installed"})
        self.assertIn("not installed", doctor.show(rep))

    def test_agents_skills_plugin_and_github(self):
        self.tool("claude")
        self.tool("codex")
        (self.home / ".claude" / "skills" / "run-workflow").mkdir(parents=True)
        (self.home / ".claude" / "plugins").mkdir(parents=True)
        (self.home / ".claude" / "plugins" / "installed_plugins.json").write_text(
            json.dumps({"plugins": {"durweg@durweg": []}}))
        self.tool("gh", "echo '{\"hosts\":{\"github.com\":[{\"state\":\"success\",\"active\":true,"
                        "\"login\":\"someone\",\"token\":\"gho_SECRET\"}]}}'")
        rep = doctor.report()
        got = {a["id"]: (a["installed"], a["durweg"]) for a in rep["agents"]}
        self.assertEqual(got, {"claude": (True, "plugin"), "codex": (True, None), "agy": (False, None)})
        self.assertEqual(rep["github"]["account"], "someone")
        self.assertNotIn("SECRET", json.dumps(rep))                       # only login/state/active are read
        self.assertIn("signed in as someone", doctor.show(rep))

    def test_signed_out_and_old_gh(self):
        self.tool("gh", "echo '{\"hosts\":{}}'")
        self.assertEqual(doctor.github()["signed_in"], False)
        self.tool("gh", "echo 'unknown flag: --json' >&2; exit 1")
        self.assertIsNone(doctor.github()["signed_in"])


class ReadPages(CatalogCase):
    def setUp(self):
        super().setUp()
        self.wf("catalog", "add", "evil", self.catalog("evil", {
            "x-ss": {"title": "<img src=x onerror=alert(1)>", "summary": "<script>alert(2)</script>", "url": self.mini_url}}))
        self.srv = ui.UIServer(idle=600)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        super().tearDown()

    def get(self, path):
        c = http.client.HTTPConnection("127.0.0.1", self.srv.port, timeout=120)
        c.request("GET", path, headers={"Host": f"127.0.0.1:{self.srv.port}"})
        r = c.getresponse()
        body = r.read()
        c.close()
        return r.status, r.getheader("Content-Type"), json.loads(body)

    def test_pages_run_the_same_commands(self):
        st, ctype, j = self.get("/api/available")
        self.assertEqual((st, ctype), (200, "application/json; charset=utf-8"))
        refs = {it["ref"]: it for it in j["items"]}
        self.assertEqual(set(refs), {"public:mini", "evil:x-ss"})
        self.assertEqual(refs["evil:x-ss"]["summary"], "<script>alert(2)</script>")   # data; the page shows it as text
        self.assertEqual(self.get("/api/installed")[2]["items"], [])
        self.assertEqual({it["id"] for it in self.get("/api/catalogs")[2]["items"]}, {"public", "evil"})
        d = self.get("/api/doctor")[2]
        self.assertTrue(d["ok"])
        self.assertEqual(len(d["agents"]), 3)
        p = self.get("/api/ping")[2]
        self.assertIn(p["language"], ("en", "zh"))

    def test_a_broken_command_is_reported_not_raised(self):
        out = ui.durweg_json(["no-such-command"])
        self.assertFalse(out["ok"])
        self.assertIn("failed (exit 2)", out["error"])
        out = ui.durweg_json(["doctor"], timeout=0.001)
        self.assertTrue(out.get("timeout"))


if __name__ == "__main__":
    unittest.main()
