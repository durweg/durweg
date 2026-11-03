"""v1.6.0: the installer's copy says when a Durweg plugin is installed next to it (user 2026-11-03)."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from durweg.util import coexist_lines, plugin_copies  # noqa: E402


class Coexist(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.claude, self.codex = self.tmp / "claude", self.tmp / "codex"
        self.old = {k: os.environ.get(k) for k in ("CLAUDE_CONFIG_DIR", "CODEX_HOME")}
        os.environ["CLAUDE_CONFIG_DIR"], os.environ["CODEX_HOME"] = str(self.claude), str(self.codex)

    def tearDown(self):
        for k, v in self.old.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)

    def installed(self, names):
        (self.claude / "plugins").mkdir(parents=True, exist_ok=True)
        (self.claude / "plugins/installed_plugins.json").write_text(
            json.dumps({"version": 2, "plugins": {n: [{"scope": "user"}] for n in names}}))

    def test_nothing_installed(self):
        self.assertEqual(plugin_copies(), [])

    def test_leftover_cache_is_not_an_installation(self):
        (self.claude / "plugins/cache/durweg/durweg/1.5.0/bin").mkdir(parents=True)
        (self.codex / "plugins/cache/durweg").mkdir(parents=True)          # empty, as after `codex plugin remove`
        self.installed(["ai-queue@ai-queue"])
        self.assertEqual(plugin_copies(), [])

    def test_claude_and_codex_plugins(self):
        self.installed(["durweg@durweg", "ai-queue@ai-queue"])
        b = self.codex / "plugins/cache/durweg/durweg/1.8.0/bin"
        b.mkdir(parents=True)
        (b / "durweg").write_text("#!/bin/sh\n")
        lines = coexist_lines()
        self.assertEqual(len(lines), 2)
        self.assertIn("/plugin uninstall durweg", lines[0])
        self.assertIn("codex plugin remove durweg@durweg", lines[1])

    def test_hidden_command_for_the_installer(self):
        self.installed(["durweg@durweg"])
        r = subprocess.run([sys.executable, "-c", "import sys; from durweg.cli import main; sys.exit(main(['_coexist']))"],
                           cwd=ROOT, capture_output=True, text=True, env=dict(os.environ, PYTHONPATH=str(ROOT)))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Durweg plugin in Claude Code", r.stdout)


if __name__ == "__main__":
    unittest.main()
