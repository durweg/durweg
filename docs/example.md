[← README](../README.md) · [中文](example_cn.md)

# Example: write down your method

This example shows how Durweg turns one of your fixed ways of working into a workflow: taking the
weekly status report, you make your own workflow `weekly-report`, run it once, and finally write it up as a case page
to keep or share. After the installation your agent asks whether to do it now; to do it later (or make
another one), follow these steps.

1. **Open a terminal** (step 1 of ["Every day"](every-day.md)).
2. **Make a practice folder and go into it:** `mkdir -p ~/projects/first-method && cd ~/projects/first-method`.
   The record of this run goes there.
3. **Start your agent** (step 3 of ["Every day"](every-day.md)).
4. **Tell it:** "Run write-your-method with durweg." It asks what you want to have when the work is
   done and how you do the weekly report now (collect, write, approve and send), looks for something
   that already does it, suggests improvements, and you confirm the steps it shows you.
5. **Name it, and write it up as a case (optional):** after the first run it asks what to call it, then
   whether to write a case. If you want one, tell it what you would tell others; it turns your method, the steps, your own words at each
   confirmation and the first run's result into one web page in `~/Durweg/cases/`. Double-click it
   to open it in your browser, or send it to someone.

Done looks like this: the agent tells you the check result is `PASS`, and "Show me my durweg
workflows" lists `weekly-report`. From then on: "Run weekly-report with durweg."

**A real case:** with this guide the workflow `human-readme` was written, and then used to rewrite Durweg's own README. The method, the steps, the user's
own words at each step and the lessons are on this case page (English, with a switch to Chinese):
[A README for humans · Durweg case](https://claude.ai/artifact/LGnCog4wnBmgMAWJg1Xmi4).
To use the workflow yourself: [durweg-human-readme](https://github.com/durweg/durweg-human-readme).
