"""durweg.util.rmtree: read-only files are removed, folders are never changed, failures are raised."""

import os
import shutil
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import helpers  # noqa: F401  (puts the checkout on the import path)
from durweg.util import rmtree

POSIX = os.name != "nt"
NOT_ROOT = POSIX and hasattr(os, "geteuid") and os.geteuid() != 0   # root ignores the permission bits


class RmtreeCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="rmtree-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def tree(self):
        t = self.tmp / "tree"
        t.mkdir()
        (t / "f.txt").write_text("keep me\n")
        return t

    def test_absent_path_is_no_error(self):
        rmtree(self.tmp / "nothing-here")

    def test_removes_a_plain_tree(self):
        t = self.tree()
        rmtree(t)
        self.assertFalse(t.exists())

    def test_read_only_file_is_made_writable_and_removed(self):
        # Windows git objects: the first unlink is refused, the retry after chmod must succeed
        t = self.tree()
        real_unlink = os.unlink
        calls = []

        def flaky_unlink(p, *a, **k):
            calls.append(p)
            if len(calls) == 1:
                raise PermissionError(13, "read-only file", p)
            real_unlink(p, *a, **k)
        with mock.patch("os.unlink", flaky_unlink):
            rmtree(t)
        self.assertFalse(t.exists())
        self.assertEqual(len(calls), 2)

    @unittest.skipUnless(NOT_ROOT, "needs a non-root POSIX user for folder permissions")
    def test_read_only_folder_raises_and_is_left_alone(self):
        t = self.tree()
        os.chmod(t, 0o500)                                   # listable, but the file cannot be removed
        self.addCleanup(os.chmod, t, 0o700)
        with self.assertRaises(OSError):
            rmtree(t)
        self.assertTrue(t.exists())
        self.assertEqual(stat.S_IMODE(os.stat(t).st_mode), 0o500)   # not changed to write-only
        self.assertEqual(os.listdir(t), ["f.txt"])                   # still listable

    def test_a_file_path_raises_like_shutil(self):
        f = self.tmp / "file.txt"
        f.write_text("not a folder\n")
        with self.assertRaises(OSError):
            rmtree(f)
        self.assertEqual(f.read_text(), "not a folder\n")

    @unittest.skipIf(os.name == "nt", "symlinks need a privilege on Windows")
    def test_a_symlink_to_a_folder_raises_like_shutil(self):
        target = self.tree()
        link = self.tmp / "link"
        os.symlink(target, link, target_is_directory=True)
        with self.assertRaises(OSError):
            rmtree(link)
        self.assertTrue((target / "f.txt").exists())         # the folder behind the link is untouched
        self.assertTrue(link.is_symlink())
