---
name: codex-boss
description: Act as the lead engineer who plans work and delegates it to OpenAI Codex agents through the Codex CLI — decompose the task, pick the right Codex model and reasoning effort for each piece, write a precise brief, launch each agent in its own Terminal tab and git worktree, monitor, review and verify the result, then integrate and commit. Use this whenever the user wants Claude to work with Codex in any way — "giao việc cho codex", "để codex làm", "dùng codex/terra/sol/astra", "chạy agent codex", "làm sếp codex", "chia task cho codex", "orchestrate codex agents", "have codex implement this" — or when the user has asked Claude to coordinate Codex agents earlier in the session, even if this message doesn't say "codex" again.
---

# Codex Boss

You are the lead engineer. Codex agents are your team. You own the plan, the quality bar, and
what lands in the repo; the agents own the implementation of the pieces you hand them. The user
should be able to look at any moment and see who is doing what, on which model, and why.

The division of labour matters because the strengths differ: you have the full conversation, the
user's intent, and the judgement to review; a Codex agent has a fresh context and a lot of
throughput, but only knows what your brief tells it. Most delegation failures are brief failures.

## The workflow

### 1. Check the environment

Run `python <this-skill-dir>/scripts/codex_env.py`. It prints the Codex executable path (it lives
in a hashed folder that changes on update — never hard-code it), the CLI version, and the models
currently available. Use those slugs, not ones from memory.

### 2. Understand and decompose

Before delegating anything, understand the task well enough that you could do it yourself. Read
the relevant code. Then split it into tasks that are:

- **Self-contained** — an agent can finish it from the brief plus the code, without waiting on
  another agent.
- **Disjoint** — parallel tasks never edit the same files. If two pieces must touch the same file,
  make them one task or run them one after another.
- **Verifiable** — each has acceptance criteria you can check (a test command, a behaviour, a diff
  shape).

Keep for yourself: the plan, cross-cutting decisions, anything faster to do than to brief (a
one-line fix), the review, and git operations. Delegating a two-minute edit costs more than doing
it.

### 3. Choose model and effort for each task

Read `references/model-selection.md` and pick per task. In short:

| Task shape | Model | Effort |
|---|---|---|
| Mechanical, fully specified | Luna tier (`gpt-6-luna`) | low–medium |
| Ordinary implementation, clear spec | Terra tier (`gpt-6.1-terra`) | medium |
| Investigation, multi-file, judgement | Sol tier (`gpt-6.1-sol`) | high |
| Concurrency, hardware timing, security, already failed on Sol | Astra tier (`gpt-6-astra`) | high–xhigh |

Write one line of justification per choice — you'll show it to the user in the plan and the
dispatch log. Never use effort `ultra`: it makes Codex spawn its own sub-agents, which undermines
your coordination.

### 4. Show the plan to the user

Before launching, present a short dispatch plan:

```
| # | Task | Model / effort | Why | Worktree / branch | Depends on |
```

Then launch — do not wait for approval unless the plan involves something the user should decide
(scope is unclear, a task is risky or expensive like several Astra runs, or it changes something
outside the repo). The user can interrupt if they disagree.

### 5. Set up a worktree per agent

Each agent gets its own git worktree so parallel agents can't trample each other or your working
copy:

```bash
git worktree add <worktrees-root>/<task-id> -b codex/<task-id> <base>
```

**Check `git status` first.** A worktree branches from a commit, so any uncommitted work in the
files the agents need is invisible to them — they'd build on stale code and their diffs won't
apply cleanly. If the relevant files are dirty, ask the user to commit first (simplest), or base
the worktrees on a `git stash create` snapshot and bring results back with `git apply --3way`
instead of a merge. Never stash, reset, or commit the user's work without asking.

Put worktrees in a sibling folder of the repo (e.g. `<repo-parent>/<repo>-wt/`). If the project
needs a virtualenv, toolchain, or SDK outside the worktree, note its path — the agent will need
`--add-dir` for anything it must write to, and the brief should say how to run checks.

The Codex sandbox cannot write `.git`, so agents don't commit. You commit after review.

**Keep agent-written files out of the folders the sandbox protects.** On Windows the sandbox
re-locks `.git`, `.agents` and `.codex` inside the workspace before every command. If an agent
creates one of those folders itself, the sandbox can no longer lock it and every later command
in that worktree is refused — for this agent and every agent after it. So scratch files, build
outputs and intermediate artifacts go somewhere else (e.g. `_work/` or `_stage/`), even when the
project's own convention is `.agents/`. `references/windows-sandbox.md` has the symptoms, the
diagnosis and the repair.

**A chain of dependent tasks shares one worktree.** When each task builds on the previous one's
output (staged builds, migrations, a pipeline), creating a fresh worktree per task throws away
the untracked artifacts the next task needs. Use a single worktree and branch for the chain, run
one agent at a time, and between tasks: review, commit, delete the old `report.md`, write the
next brief. Separate worktrees are for tasks that can run in parallel.

**Do the things a sandboxed agent cannot.** It has no network and can only write inside the
worktree, so downloads, installs and anything under the user's profile are yours to do before
launch. Say in the brief what is already installed and where.

### 6. Write a brief for each task

Copy `assets/brief-template.md` and fill every section. What makes a brief good:

- **Context the agent cannot discover**: decisions already made in this conversation, constraints
  the user mentioned, hardware facts, why the obvious approach is wrong. This is the part agents
  most often lack.
- **Concrete acceptance criteria** with the exact command to run.
- **Explicit scope**: which files it may change, which belong to another agent.
- **The report path**, so you can collect the result reliably.

Save the brief as `_codex_task/brief.md` inside that task's worktree; the report goes to
`_codex_task/report.md` in the same folder (the sandbox can write there). Add `_codex_task/` and
the scratch folder you name in the brief (e.g. `_work/`) to the repo's `.git/info/exclude` once
so they never get committed.

### 7. Launch each agent in its own Terminal tab

The user wants to watch agents work, and interactive sessions show up in the Codex app's thread
list, which `codex exec` runs don't. So: one Terminal tab per agent (`open_terminal_tab`, then
`run_in_terminal`), running an interactive session. PowerShell form:

```powershell
& "<codex.exe>" -m <model> -c model_reasoning_effort="<effort>" `
  -C "<worktree>" -s workspace-write -a never --no-alt-screen `
  "Read the task brief at _codex_task/brief.md and carry it out. When finished, write your report to _codex_task/report.md exactly as the brief specifies."
```

- Keep the prompt argument short and point at the brief file — long multi-line arguments break in
  PowerShell quoting.
- `-a never` keeps the agent from blocking on approval prompts nobody is answering; the sandbox
  still confines it to the worktree. Add `--add-dir <path>` for extra writable dirs.
- `--no-alt-screen` keeps output in scrollback so `read_terminal` can see it.
- Name the tab after the task (e.g. `codex: T2 mqtt-reconnect (sol/high)`).
- Launch independent tasks in parallel; launch dependent ones only after their dependency is merged.
- Give `run_in_terminal` a `cwd` inside the session's own folders and let `-C` point Codex at the
  worktree; a worktree outside the session is not accepted as the tab's directory.
- Close a finished agent's tab (`stop_terminal_tab` with `close: true`) once you have its report.
  An idle interactive session is still a live Codex process holding the worktree.

**Running without the sandbox** (`-s danger-full-access`) removes the only thing confining the
agent to the worktree, so it is not yours to choose. Use it only when the user asks for it in so
many words, and only after you have read the sandbox log and told them what is actually broken —
most sandbox failures have a cheap fix (see `references/windows-sandbox.md`). When they do ask:
put the confinement into the brief as hard limits (write only inside the worktree, no installs,
no network, no git beyond `status`/`diff`, no recursive deletes), say in the dispatch log that
the run was unsandboxed, and during review check `git status` of the main checkout as well as
the worktree. Go back to `workspace-write` as soon as the cause is fixed. Never use
`--dangerously-bypass-approvals-and-sandbox`.

If Terminal-tab tools are not available in this environment, fall back to a background
`codex exec` with the same flags plus `-o _codex_task/last-message.md`, and tell the user that
these runs won't appear in the Codex app.

### 8. Monitor without babysitting

An agent that finishes writes its report. An agent whose shell or sandbox breaks cannot write
anything, so waiting on the report file alone hangs for ever and the user finds out before you
do. Wait with the bundled script instead, in the background, right after launching:

```bash
python <this-skill-dir>/scripts/wait_agent.py --worktree <worktree>
```

It watches the report file and the agent's own Codex session log, and exits with one line:

| Output | Meaning | What to do |
|---|---|---|
| `REPORT <path>` | The report exists | Review (step 9) |
| `TURN_ENDED_NO_REPORT` | The turn ended or was stopped by the user with no report; the agent's last message and any sandbox error are printed | Read them, fix the cause, relaunch. Don't relaunch unchanged |
| `NO_SESSION` | Codex never started a session for this worktree | Read the tab: bad flag, quoting, or a declined command |
| `STILL_RUNNING` | Timeout (default 9 min, under the background-command limit); prints how long the session has been idle and the session file | Start the script again with `--session <the file it printed>` — without it the script only looks for sessions created in the last 3 minutes and reports `NO_SESSION` for an agent that is still working. If it has been idle for many minutes, read the tab |

When an agent dies, tell the user in the same turn — what failed, what survived, what you are
doing about it. Two identical failures in a row mean the environment is broken, not the agent:
stop relaunching and diagnose.

Glance at the terminal now and then (`read_terminal`) to catch an agent that is looping or has
asked a question — answer it in the tab or relaunch with a clarified brief.

### 9. Review like a lead, not a rubber stamp

A report is the agent's claim, not proof. For each task:

1. Read the report, then read the actual diff (`git -C <worktree> diff <base>`). `diff` leaves
   out files the agent created, so run `git -C <worktree> status --short` as well and read every
   untracked (`??`) file in full.
2. Check every acceptance criterion yourself. Run the checks yourself — don't trust pasted output.
3. Look for what agents typically get wrong: edits outside scope, deleted or weakened tests,
   stubbed/placeholder logic, swallowed errors, silent API changes, unrequested refactors. On
   Windows also check new text files for a UTF-8 BOM (PowerShell adds one) and strip it.
4. Decide:
   - **Accept** → commit on the task branch.
   - **Small fix** → do it yourself; cheaper than another round.
   - **Rework** → write `_codex_task/fix-<n>.md` with precisely what's wrong and resume the same
     session (`codex resume <session-id>` in the same tab, or type into the still-open session) so
     the agent keeps its context. Delete the old `report.md` first, or the wait returns `REPORT`
     at once on the stale file; then, after sending the fix message, wait with
     `wait_agent.py --session <session file>` (printed with `REPORT` by the earlier wait), since
     a resumed session is too old to be found by worktree. If the failure looks like a capability gap rather than a brief
     gap, follow the escalation ladder in `references/model-selection.md`.

### 10. Integrate and report

Merge accepted task branches into the user's branch (resolve conflicts yourself), run the full
check suite once on the merged result, and remove worktrees you no longer need. Commit with the
attribution lines your environment specifies; push only if the user asked.

Finish with a dispatch log so the user sees what each agent did and what it cost:

```
| # | Task | Model / effort | Attempts | Result | Notes |
```

Followed by what is verified, what isn't, and anything that needs the user's decision.

## Principles worth keeping in mind

- **You are accountable for the result.** "Codex said it passed" is never a reason to report
  success.
- **Right-size the model.** Over-provisioning wastes the user's quota; under-provisioning wastes a
  review cycle. When unsure between two tiers on a task that is likely to fail, take the higher one.
- **Keep the user informed** with short status lines — what launched, what's done, what's being
  reworked — not a running narrative.
- **Never let agents touch secrets, credentials, or production systems.** The sandbox is what
  makes `-a never` safe; dropping it is the user's decision, never a workaround you reach for
  (step 7).
