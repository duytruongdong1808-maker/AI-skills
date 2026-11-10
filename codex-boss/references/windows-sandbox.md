# The Codex sandbox on Windows: failures and repairs

Read this when an agent's commands are refused, when `wait_agent.py` prints
`TURN_ENDED_NO_REPORT` with a sandbox line, or before choosing where agents put scratch files.

## How it works, in one paragraph

With `[windows] sandbox = "elevated"` in `~/.codex/config.toml`, Codex runs each agent command
as a restricted account. Before a command it runs `codex-windows-sandbox-setup.exe`, which
refreshes file permissions: write access on the workspace roots, and a deny rule on the folders
it protects inside them (`.git`, `.agents`, `.codex`). If any part of that refresh fails, the
command is not run at all. The agent has no network.

## Where to look

- `~/.codex/.sandbox/sandbox.<YYYY-MM-DD>.log` — the setup helper's own log. The line
  `setup refresh completed with errors: [...]` names the path and the reason. Start here.
- `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl` — one file per session; the last assistant
  message usually quotes the error the agent saw.
- The agent's terminal tab.

## Known failures

| Symptom the agent reports | Log line | Cause | Repair |
|---|---|---|---|
| Every command: `windows sandbox failed: helper_unknown_error: setup refresh had errors`. Often starts mid-run, right after the agent created files | `deny ACE failed on <worktree>\.agents: ... Access is denied. (os error 5)` (or `.codex`) | The agent created a protected folder itself. It is now owned by the sandbox account, so the setup helper cannot put its deny rule on it | Move the files to an unprotected folder (`_work/`), delete the protected folder from the worktree, point the code and brief at the new location, relaunch |
| Agent cannot download or install | none | No network in the sandbox | Do it yourself before launch; tell the brief what exists and where |
| Agent cannot write a path outside the worktree | none | Only workspace roots are writable | Add `--add-dir <path>`, or move the output into the worktree |
| `apply_patch` fails, agent falls back to PowerShell file writes | none | Follows from a broken sandbox | Fix the sandbox cause above; expect BOMs in files written that way |

## Before launching: a ten-second check

- Does the plan, the brief, or the project's own tooling tell the agent to write under `.agents/`,
  `.codex/` or `.git/` in the worktree? Redirect it.
- Does one of those folders already exist in the worktree, created by an earlier agent? Empty it
  out and remove it first.
- Does the task need the network or a tool that is not installed? Handle that yourself.

## When the log shows something not in the table

Report the exact log line to the user. Do not edit `~/.codex/config.toml`, change folder
permissions outside the worktree, or switch the sandbox off on your own: those are the user's
security settings. Offer the options (fix the cause, do the task yourself, or — only if they ask
for it — an unsandboxed run under the rules in SKILL.md step 7).
