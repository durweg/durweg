[← README](../README.md) · [中文](publish_cn.md)

# Publishing a workflow of yours

`durweg publish` puts one of your own workflows into a GitHub repository, public or private, so your
other computers can install it, or other people can. It needs a GitHub account and the GitHub
command `gh` (logged in once with `gh auth login` and `gh auth setup-git`); using Durweg does not.

1. Start your agent (as every day) and tell it: "Publish <name> with durweg."
2. It shows you what would be published and asks what is still open:
   - **public or private**;
   - **a license**, if the folder has none (MIT, Apache-2.0, CC-BY-4.0, or none);
   - **a catalog**: for a public workflow, whether to propose it to the public catalog; for a
     private one, whether to put it into your private catalog (the first time: whether to make one);
   - **a case page**, only if you name one from `~/Durweg/cases/`.
3. Look at the list of files and say yes. Only then does it create the repository and push.

Done looks like this: it prints `created <you>/durweg-<name>` and `pushed …`; the workflow is on
GitHub, and `durweg library list` still shows it in your own folder.

## What goes into the repository

| Goes in | Never goes in |
| :--- | :--- |
| • `workflow.json`, the skill folder and the files listed under `snapshot`<br>• your `README.md` (or one Durweg writes from the steps)<br>• your `LICENSE` (or the one you chose)<br>• the case page you named | • anything else in the folder<br>• runs, `.wf/`, your settings<br>• case pages you did not name |

Durweg copies these into `~/Durweg/publish/<name>/` and pushes from there; your folder is not
changed and stays where you edit the workflow.

## Before a public publish: English for what people type

A public workflow is read by people who may not read Chinese. Before publishing it publicly, Durweg
looks at the English pages (every `.md` except `*_cn.md` / `*_zh.md`) and stops when what a reader
types or copies is not in English: inline code, code blocks and quoted lines (such as "tell your
agent: ..."). With `--catalog yes` it also checks the title and summary that go into the public
catalog. Fix them and run publish again; if some are meant that way (an example of Chinese input),
pass `--language-ok`. When the README itself is not in English, Durweg asks first:
`--english-readme add` stops so you can write one (keep the other language as `README_cn.md`),
`--english-readme skip` publishes as it is. Private publishing is not checked.

## Where it goes: your account or an organization

New repositories go to `<your GitHub account>/durweg-<name>`. To publish to an organization by
default, run `durweg config publish-owner <organization>` (`durweg config publish-owner none` goes
back); `--repo owner/name` still chooses one repository. What `durweg publish` shows names the owner
and where it came from. A workflow published before keeps going to its first repository.

## Later

- **A new version:** edit the workflow in your folder, then "Publish <name> with durweg" again. It
  pushes to the same repository; other computers get it with `durweg update`.
- **Another computer:** `durweg library add <the repository's address>`, or by name when it is in a
  catalog: for your private catalog, first `durweg catalog add private <its address>` (once, with
  `gh` logged in).
- **Made public on GitHub:** a workflow you published as private and then made public on GitHub
  yourself is published as public from then on. The next "Publish <name> with durweg" says so
  first; with your yes it updates its record, takes the workflow out of your private catalog and
  asks whether to propose it to the public catalog. If your private catalog cannot be changed just
  then, it says so and tries again the next time you publish. The other way round (public made
  private) is not supported.

## What Durweg never does

- push to a repository it did not create from this computer, or change whether a repository is
  public or private;
- put a private workflow into the public catalog, or into a catalog that GitHub does not show as
  private and writable for you (it checks right before every write);
- publish a workflow you installed from someone else's repository.
