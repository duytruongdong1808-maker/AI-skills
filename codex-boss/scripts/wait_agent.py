"""Wait for a Codex agent, and notice when it dies without writing its report.

Usage:  python wait_agent.py --worktree <path> [--report _codex_task/report.md]
                             [--timeout 540] [--launched-within 180]
                             [--session <rollout file>]

Start it right after launching the agent (run it in the background). It exits
as soon as one of these is true and prints one status line first:

  REPORT <path>             exit 0  the report file exists
  TURN_ENDED_NO_REPORT      exit 3  the agent's turn finished but no report was
                                    written: it gave up, crashed or was blocked
  NO_SESSION                exit 4  no Codex session for this worktree appeared
  STILL_RUNNING             exit 2  timeout reached; the agent is still working,
                                    so start the script again with the
                                    --session it prints (without it the session
                                    is too old to be found and you get NO_SESSION)

Why not just wait for the report file: an agent whose shell or sandbox breaks
cannot write the report either, so a file-only wait hangs for ever. Codex logs
every session to ~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl and writes a
`task_complete` event when a turn ends, or `turn_aborted` when the user stops it.
Either one is the signal.
"""
import argparse
import datetime
import glob
import json
import os
import sys
import time


def codex_home():
    return os.environ.get("CODEX_HOME", os.path.expanduser("~/.codex"))


def same_path(a, b):
    norm = lambda p: os.path.normcase(os.path.normpath(os.path.abspath(p)))
    return norm(a) == norm(b)


def read_session(path):
    """Return (cwd, turn_ended, last_agent_text) for one rollout file."""
    cwd, last_event, last_text = None, None, ""
    try:
        with open(path, encoding="utf-8", errors="replace") as stream:
            for line in stream:
                try:
                    record = json.loads(line)
                except ValueError:
                    continue  # a line still being written
                payload = record.get("payload") or {}
                kind = record.get("type")
                if kind == "session_meta":
                    cwd = payload.get("cwd")
                elif kind == "event_msg":
                    last_event = payload.get("type")
                elif kind == "response_item" and payload.get("role") == "assistant":
                    parts = payload.get("content") or []
                    text = " ".join(p.get("text", "") for p in parts if isinstance(p, dict))
                    last_text = text.strip() or last_text
    except OSError:
        pass
    return cwd, last_event in ("task_complete", "turn_aborted"), last_text


def find_session(worktree, not_before):
    """Newest rollout for this worktree created after the agent was launched."""
    root = os.path.join(codex_home(), "sessions")
    days = {datetime.date.today(), datetime.date.today() - datetime.timedelta(days=1)}
    files = []
    for day in days:
        files += glob.glob(os.path.join(root, day.strftime("%Y/%m/%d"), "rollout-*.jsonl"))
    files = [f for f in files if os.path.getctime(f) >= not_before]
    for path in sorted(files, key=os.path.getctime, reverse=True):
        cwd, _, _ = read_session(path)
        if cwd and same_path(cwd, worktree):
            return path
    return None


def sandbox_error(not_before):
    """Last Windows-sandbox setup error logged since launch, if any."""
    log = os.path.join(codex_home(), ".sandbox",
                       "sandbox.%s.log" % datetime.date.today().isoformat())
    try:
        if os.path.getmtime(log) < not_before:
            return None
        with open(log, encoding="utf-8", errors="replace") as stream:
            hits = [line.strip() for line in stream if "completed with errors" in line]
        return hits[-1][-400:] if hits else None
    except OSError:
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--worktree", required=True)
    parser.add_argument("--report", default="_codex_task/report.md")
    parser.add_argument("--timeout", type=int, default=540)
    parser.add_argument("--launched-within", type=int, default=180,
                        help="seconds before now that the agent may have been launched")
    parser.add_argument("--session",
                        help="rollout file to watch, as printed by an earlier run; use it when "
                             "waiting again on a session that is older than --launched-within")
    args = parser.parse_args()

    report = os.path.join(args.worktree, args.report)
    started = time.time()
    not_before = started - args.launched_within
    ended_at = None
    while True:
        session = args.session or find_session(args.worktree, not_before)
        if os.path.isfile(report):
            print("REPORT", report)
            if session:
                print("session:", session)
            return 0
        if session:
            _, ended, text = read_session(session)
            if ended:
                # Give a just-finished agent a moment to flush the report.
                ended_at = ended_at or time.time()
                if time.time() - ended_at >= 10:
                    print("TURN_ENDED_NO_REPORT", session)
                    if text:
                        print("last agent message:", text[-800:])
                    error = sandbox_error(not_before)
                    if error:
                        print("sandbox log:", error)
                    return 3
            else:
                ended_at = None
        elif time.time() - started >= 90:
            print("NO_SESSION no Codex session for", args.worktree)
            return 4
        if time.time() - started >= args.timeout:
            idle = int(time.time() - os.path.getmtime(session)) if session else -1
            print("STILL_RUNNING last session activity %ss ago" % idle)
            if session:
                print("wait again with: --session", session)
            return 2
        time.sleep(5)


if __name__ == "__main__":
    sys.exit(main())
