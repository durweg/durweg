[← README](../README.md) · [中文](ui_cn.md)

# The management page (`durweg ui`)

A page in your browser for the things you do around Durweg without typing commands: see which
workflows you can install, add and remove them, keep them up to date, manage catalogs and check
what this computer has. Running a workflow stays in the terminal with your agent; the page gives
you the sentence to say.

1. Open a terminal (on Windows: PowerShell, then `wsl`).
2. Run `durweg ui`. It prints a link and opens your browser on it.
   - No browser opened (for example over SSH): copy the link into a browser on the same computer.
3. Use the three tabs:

| Tab | What you do there |
| :--- | :--- |
| Browse | • the workflows in the catalogs that are switched on<br>• **Add** installs one; a workflow with the same name already in your library is marked instead |
| Installed | • your library<br>• **Run** shows the sentence for your agent; **Update**; **Remove** (the folder stays on this computer) |
| This computer | • Claude Code, Codex, Antigravity: installed, and whether they have Durweg<br>• GitHub sign-in (to sign in: `gh auth login --web` in a terminal)<br>• catalogs: add, remove, switch the public one off and on, make your private catalog (you see what would happen first) |

**Update everything** (top right) does the same as `durweg update`. Changes run one at a time and
are listed under **Changes**, with what happened to each workflow.

## 🔒 Good to know

- The page is only reachable from this computer (`127.0.0.1`), and only the link printed at the
  start can make changes. After a refresh or in a new tab the page still shows everything but its
  buttons are grey: open the printed link again.
- `Ctrl-C` in the terminal stops it; it also stops after 30 minutes without use.
- When it opens your browser, the link (with the key of this start) is passed to the program that opens
  the browser. On a computer shared with other people, use `durweg ui --no-browser` and paste the
  link yourself.
- After **Update everything** updated Durweg itself, close the page and run `durweg ui` again.
