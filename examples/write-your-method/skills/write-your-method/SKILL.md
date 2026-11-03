---
name: write-your-method
description: Durweg's first-run example - help the user say what they want from one kind of work and how they do it, check whether something already does it, turn the method into steps, build a Durweg workflow from it, run it once, give it its name and, if they like, write it up as a case page. Use when the user starts Durweg for the first time or asks to turn their own method into a workflow.
---

# write-your-method: from "how I do it" to a workflow you can run

Run it with durweg (skill run-workflow): `durweg start write-your-method my-first-method`, then step
by step. Talk to the user in the language set in `~/Durweg/config.json` (`"language": "zh"` is
Chinese, `"en"` English); file names, step ids and commands stay in English. The method is the
user's: write down what they say, do not invent their method for them. Ask little: where you can
write a first version yourself, write it and let the user correct it.

`RUN` below is this run's folder.

## 1. Describe
Ask one question: **"When this workflow is done, what do you want to have?"** From the answer
write one sentence, the core: "It solves ___; when it is done you have ___." Show it; the user
says yes or changes a word.

Then ask them to tell you how they do it now, in their own words. From that, write the steps in
their order, where it usually goes wrong and where they always decide themselves; show it and ask
only about what is missing.

**File:** `steps/1-method.md` with these headings (keep the English headings, write the content in
the user's language):
- `## Core`: the one sentence;
- `## How I do it`: a list, at least two items, in their order;
- `## Where it goes wrong`: a list (may be empty);
- `## Where I decide`: a list (may be empty).

`durweg propose`, show it, and `durweg confirm` with the user's words when it is right.

## 2. Check
Before building anything, look for something that already does what the core says: agent plugins
and skills (Claude Code, Codex), workflows in the Durweg public catalog (`durweg library available`),
and existing software or libraries. At most 5 searches; show at most 3 results, one line each: what
it is, whether it does the core, what it lacks.

**File:** `steps/2-check.md`:

```markdown
## Existing tools
- <name and link>: <what it is>; <does it do the core?>; <what it lacks>
(or one line: "- searched <where>; nothing that does this")

## Choice
- Choice: use existing | build on <tool> | build my own
```

The user chooses. **use existing**: tell them how to start with it; this run stops here (do not
run the later steps; the record says why). **build on <tool>**: the next steps only add what the
tool lacks. **build my own**: go on as usual. `durweg propose`, confirm with their words.

## 3. Design
First give the user their method back as a numbered list (from step 1), then your suggestions, one
per line: steps that can be merged or dropped, a better order, a check that can be automatic, and
places where they do not really need to decide. The user picks which to take. Then turn the method
into steps. Each step does one thing and delivers something the user can look at. A step where the
user decides gets `"user": true`. Do not add check scripts: the user's own look is the check
(Durweg's rule: write a script only when a mistake cannot be seen in the result, costs a lot, and
the work repeats often).

**Files:**
- `steps/3-review.md`: `## Your method` (the numbered list) and `## Suggestions` (one line each,
  with what the user chose: taken / not taken);
- `steps/3-steps.json`: `{"name": "<lower-case-name>", "title": "<the method's title>", "steps":
  [{"id": "<lower-case-id>", "title": "...", "do": "...", "deliver": "...", "user": true|false}]}`
  with 2 to 12 steps. The name is a working name for now (lower-case letters, digits and -); the
  final name comes in step 6.

Show the user the steps as a numbered list (title, what it delivers, whether they decide there),
`durweg propose`, and confirm with their words.

## 4. Build
1. `python3 RUN/.wf/workflow/tools/generate.py RUN` builds `generated/<name>/` from the confirmed
   design: `workflow.json` and the skill. Do not edit the generated files by hand; to change
   something, `durweg reopen RUN design`.
2. `python3 RUN/.wf/workflow/tools/register.py RUN` copies it into `~/Durweg/workflows/<name>/` and
   writes `steps/4-register.json`; then run the command it prints:
   `durweg library add "<that folder>" --name <name>`. If the name is taken, choose another
   (`durweg reopen RUN design`).

Tell the user it is built and in their library (step number, id, title, whether they decide there).

## 5. Try
Ask the user whether to run their new workflow once now. When they agree:
`durweg start <name> try-1` (in the same project folder), go through it with them step by step as
its skill says, and finish with `durweg check <that run>`.

**File:** `steps/5-try.json`: `{"run": "<the new run's folder>", "check": "PASS"}` (only after
check printed PASS). `durweg propose`, show the user both results, and confirm with their words.

## 6. Name
Now that they have seen it work, ask what to call it. If they have no good name yet, suggest
running the workflow name-project (in its own run; it is in the public catalog): give it the core
from step 1 and the tools from step 2, so the name says what this one does that they do not. If
they cannot say what it does better than those, go back to step 2 (`durweg reopen RUN check`).

`python3 RUN/.wf/workflow/tools/rename.py RUN <final-name>` writes `steps/6-name.json`. With a new
name it builds the workflow again under that name in `named/<final-name>/`, copies it into
`~/Durweg/workflows/<final-name>/` and prints two commands; run them: `durweg library remove <old>`
and `durweg library add "<that folder>" --name <final-name>`. The try run keeps its record.

Then ask whether they want this run written up as a case: one web page they can keep, or send to
others to share what they learned. It holds their method, the steps, their own words at each
confirmation and the first run's result, all taken from this run's record.

- **No:** write `steps/6-case.json` as `{"made": false}`.
- **Yes:** ask what they would tell someone who wants to do the same (what worked, what to watch
  for) and write it, in their words, to `steps/6-lessons.md` under `## Lessons`. Then
  `python3 RUN/.wf/workflow/tools/make_case.py RUN` builds `case/<name>.html`, keeps a copy in
  `~/Durweg/cases/` and writes `steps/6-case.json`. Do not edit the page by hand; to change the
  lessons, edit `steps/6-lessons.md` and run make_case.py again. Tell the user where the copy is
  (they open it by double-clicking).

`durweg propose`, and confirm with their words.

At the end: `durweg check RUN` for this run too, and tell the user how to use their workflow from
now on: "Run <name> with durweg."

Then ask once whether they want to publish it on GitHub, so their other computers or other people
can install it (it needs a GitHub account and `gh`). If not, stop here. If yes, follow "Publishing"
in the skill run-workflow.
