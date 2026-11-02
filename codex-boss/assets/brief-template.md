# Task <ID>: <short title>

You are a Codex agent working on one task assigned by the lead engineer (Claude). Work only on
this task. When you finish — or if you get stuck — write the report described at the end. The
lead will review your diff, run the checks, and commit; you do not commit.

## Goal
<1–3 sentences: what should be true when you are done, and why it matters.>

## Context
- Repository: <path> (you are in a git worktree on branch `<branch>`)
- Relevant files: <list, with one line on each>
- Background the agent cannot discover from the code: <decisions already made, constraints,
  hardware facts, links to docs/spec sections>

## Scope
- In scope: <files/modules you may change>
- Out of scope: <what not to touch — shared files owned by another agent, public APIs, etc.>

## Acceptance criteria
- [ ] <observable, checkable criterion>
- [ ] <…>
- [ ] Checks pass: `<exact test/build/lint command>`

## How to work
- Read the relevant code before editing; follow the existing style and patterns.
- Keep the change minimal and focused on the goal; no drive-by refactors.
- Run the checks above yourself before reporting. If a check cannot run in your sandbox, say so.
- If something in this brief is wrong or ambiguous, choose the most reasonable reading, continue,
  and flag it in the report rather than stopping.

## Report
When done, write `<report path>` with:

```
STATUS: done | partial | blocked
SUMMARY: <2–4 sentences>
FILES CHANGED: <list>
CHECKS: <command → result, pasted tail of output>
DEVIATIONS / ASSUMPTIONS: <anything you did differently from the brief, and why>
OPEN ISSUES: <what's left, risks, questions for the lead>
```
