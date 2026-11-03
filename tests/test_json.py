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
from durweg.util import rmtree


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

    def test_same_name_from_elsewhere_is_flagged(self):
        own = self.tmp / "own-mini"
        import shutil
        shutil.copytree(self.repo, own)
        self.wf("library", "add", str(own), "--name", "mini")
        [it] = one_json(self.wf("library", "available", "--json"))["items"]
        self.assertEqual((it["installed_as"], it["name_in_library"]), (None, True))

    def test_the_built_in_example_cannot_be_removed(self):
        home = Path(os.environ["DURWEG_HOME"])
        copy = self.tmp / "share" / "current"                       # like the installer's copy
        (copy / "durweg").mkdir(parents=True)
        (copy / "durweg" / "__init__.py").write_text("")
        import shutil
        shutil.copytree(Path(__file__).resolve().parent.parent / "examples" / "write-your-method",
                        copy / "examples" / "write-your-method")
        self.wf("library", "add", str(copy / "examples" / "write-your-method"), "--name", "write-your-method")
        [it] = [i for i in one_json(self.wf("library", "list", "--json"))["items"] if i["name"] == "write-your-method"]
        self.assertTrue(it["builtin"])
        self.assertIn("comes with Durweg", self.wf("library", "remove", "write-your-method", expect=1))
        self.assertIn("write-your-method", self.lib())
        # a workflow of the user's own with that name is not built in
        data = json.loads((home / "library.json").read_text())
        data["workflows"]["write-your-method"]["path"] = str(self.repo)
        (home / "library.json").write_text(json.dumps(data))
        self.wf("library", "remove", "write-your-method")

    def test_the_installer_points_the_example_at_a_new_version(self):   # Durweg-Install.bat on update
        import shutil
        src = Path(__file__).resolve().parent.parent / "examples" / "write-your-method"
        copies = []
        for v in ("v1", "v2"):
            c = self.tmp / "Local" / v
            (c / "durweg").mkdir(parents=True)
            (c / "durweg" / "__init__.py").write_text("")
            shutil.copytree(src, c / "examples" / "write-your-method")
            copies.append(c / "examples" / "write-your-method")
        self.wf("_example", copies[0])
        self.wf("_example", copies[1])
        self.assertEqual(Path(self.lib()["write-your-method"]["path"]), copies[1])
        self.wf("_example", self.repo, expect=1)                                  # not a Durweg copy's example
        data = json.loads((Path(os.environ["DURWEG_HOME"]) / "library.json").read_text())
        data["workflows"]["write-your-method"]["path"] = str(self.repo)           # the user's own
        (Path(os.environ["DURWEG_HOME"]) / "library.json").write_text(json.dumps(data))
        self.wf("_example", copies[0])
        self.assertEqual(Path(self.lib()["write-your-method"]["path"]), self.repo)

    def test_remove_then_add_again(self):
        self.wf("library", "add", "mini")
        self.wf("library", "remove", "mini")
        j = one_json(self.wf("library", "add", "public:mini", "--json"))       # the kept clone is used again
        self.assertEqual(j["name"], "mini")
        self.assertIn("kept from before", j["note"])
        self.assertEqual(one_json(self.wf("library", "available", "--json"))["items"][0]["installed_as"], "mini")
        self.wf("library", "remove", "mini")
        folder = Path(os.environ["DURWEG_HOME"]) / "workflows" / "mini"
        rmtree(folder / ".git")                                         # not a clone any more
        out = self.wf("library", "add", "mini", expect=1)
        self.assertIn(f"durweg library add {folder}", out)

    def test_unreachable_catalog_is_a_note_not_a_failure(self):
        url = self.catalog("gone", {})
        self.wf("catalog", "add", "gone", url)
        rmtree(url)                                   # the remote disappears; the cached copy stays
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
        out = self.wf("library", "remove", "nothing-here", "--json", expect=1)
        j = one_json(out)
        self.assertEqual((j["schema"], j["ok"]), (1, False))
        self.assertTrue(j["error"])
        self.assertFalse(one_json(self.wf("catalog", "add", "x", "--json", expect=1))["ok"])

    def test_changes(self):
        j = one_json(self.wf("library", "add", "public:mini", "--json"))
        self.assertEqual((j["ok"], j["name"]), (True, "mini"))
        j = one_json(self.wf("library", "update", "--json"))
        self.assertEqual([(it["name"], it["status"]) for it in j["items"]], [("mini", "unchanged")])
        self.assertEqual(j["catalogs"][0]["id"], "public")
        self.assertTrue(j["ok"])
        j = one_json(self.wf("library", "remove", "mini", "--json"))
        self.assertTrue(j["folder_kept"])
        j = one_json(self.wf("catalog", "add", "team", self.catalog("team", {}), "--json"))
        self.assertEqual((j["id"], j["note"]), ("team", None))
        self.assertEqual(one_json(self.wf("catalog", "remove", "team", "--json"))["result"], "removed")
        self.assertEqual(one_json(self.wf("catalog", "remove", "public", "--json"))["result"], "switched off")

    def test_update_everything(self):
        self.wf("library", "add", "mini")
        j = one_json(self.wf("update", "--json"))
        self.assertEqual(j["durweg"]["status"], "skipped")      # not installed by the installer here
        self.assertFalse(j["durweg"]["restart_ui"])
        self.assertEqual([(it["name"], it["status"]) for it in j["items"]], [("mini", "unchanged")])
        self.assertTrue(j["ok"])

    def test_update_reports_failures_as_not_ok(self):
        self.wf("library", "add", "mini")
        rmtree(self.mini_url)                         # its remote is gone
        j = one_json(self.wf("library", "update", "mini", "--json"))
        self.assertEqual(j["items"][0]["status"], "failed")
        self.assertFalse(j["ok"])


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
