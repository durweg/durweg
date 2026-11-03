#!/usr/bin/env python3
"""Step 6 of write-your-method (action): give the user's workflow its final name.

  rename.py RUN <final-name>

The same final name as in the design: writes steps/6-name.json and stops. Another name: builds the
workflow again from the confirmed design under that name in RUN/named/<name>/, copies it to
~/Durweg/workflows/<name>/ ($DURWEG_HOME if set), writes steps/6-name.json and prints the two library
commands (remove the old name, add the new one). The try run keeps its own copy. Standard library only.
"""
import json
import os
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate import build  # noqa: E402
from register import tree_digest  # noqa: E402

ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def main(argv):
    if len(argv) != 2:
        sys.exit(__doc__)
    run, new = Path(argv[0]).resolve(), argv[1]
    if not ID.match(new):
        sys.exit(f"name {new!r}: use lower-case letters, digits and -")
    old = json.loads((run / "steps/3-steps.json").read_text(encoding="utf-8"))["name"]
    rec = {"name": new, "from": old}
    if new != old:
        out = build(run, name=new, root="named")
        home = Path(os.environ.get("DURWEG_HOME") or Path.home() / "Durweg")
        dest = home / "workflows" / new
        digest = tree_digest(out)
        if dest.exists() and tree_digest(dest) != digest:
            sys.exit(f"{dest} exists and holds something else; it is left alone. Choose another name.")
        if not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(out, dest)
        rec.update({"library_path": str(dest), "digest": digest})
    (run / "steps/6-name.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    if new == old:
        print(f"the name stays {old}")
    else:
        print(f"renamed copy in {rec['library_path']}\nnow run:\n  durweg library remove {old}\n"
              f"  durweg library add \"{rec['library_path']}\" --name {new}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
