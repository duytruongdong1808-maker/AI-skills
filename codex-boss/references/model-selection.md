# Choosing a Codex model and reasoning effort

The goal is **balanced**: the cheapest configuration that will very likely get the task right on
the first try. A wrong cheap run is not cheap — it costs a review cycle and a rerun — so do not
under-pick on tasks where failure is likely. But spending a frontier model on a rename burns the
user's quota for nothing.

Always confirm the live list first (`python <skill-dir>/scripts/codex_env.py`). The table below
describes the lineup as of 2026-10; if the cache shows new slugs, map them onto the same four
tiers by their descriptions (fast/affordable → Luna tier, balanced → Terra tier, workhorse → Sol
tier, frontier → Astra tier) and prefer the newest generation within a tier.

## The tiers

| Tier | Current slug | Context | What it is good at |
|---|---|---|---|
| Fast | `gpt-6-luna` | 272k | Mechanical, well-specified edits: renames, formatting, boilerplate, docs, adding a test that mirrors existing ones, simple config changes. |
| Balanced | `gpt-6.1-terra` | 500k | Codex-tuned coder. Straightforward implementation with a clear spec: a function/endpoint/component, a bug with a known repro and location, test suites for existing code. **Default for ordinary coding.** |
| Workhorse | `gpt-6.1-sol` | 500k | Multi-file features, refactors across modules, bugs whose cause is unknown, tasks needing judgement or reading a lot of code, mixed code+docs+research work. |
| Frontier | `gpt-6-astra` | 272k | The genuinely hard: concurrency/timing/firmware races, security-sensitive code, subtle algorithmic work, architecture-level changes, or a task that already failed on Sol. |

Skip the older generations (`gpt-6-sol`, `gpt-5.6-*`) unless a newer model is unavailable or the
user asks for one.

## Reasoning effort

Effort is the cheaper knob — turn it before switching model.

| Effort | Use for |
|---|---|
| `low` | Mechanical work where thinking adds nothing (Luna/Terra on trivial edits). |
| `medium` | Default for normal implementation. |
| `high` | Debugging, multi-file changes, anything where the agent must investigate before editing. |
| `xhigh` / `max` | Rare. Hard single problems after `high` fell short, or Astra on the hardest work. |
| `ultra` | Do not use. It makes Codex delegate to its own sub-agents, which fights your role as the one coordinating the work and makes runs hard to track. |

## Decision procedure

Score the task on these questions, then pick:

1. **Is the change fully specified?** (You could write the diff yourself in a few minutes; the brief
   names the files and the exact behaviour.) → Luna `low`/`medium`, or Terra `low` if it touches
   real logic.
2. **Is it ordinary implementation with a clear spec and known location?** → Terra `medium`.
3. **Does the agent need to explore, diagnose, or coordinate changes across several modules?** →
   Sol `high` (Terra `high` if it's mostly in one area).
4. **Is it the kind of thing a strong senior engineer would get wrong on the first try** —
   concurrency, hardware timing, security, numerical subtlety, design decisions with lasting
   consequences? → Astra `high` (`xhigh` if very hard).
5. **Huge context** (needs to hold >200k tokens of code/logs at once)? → prefer Sol or Terra
   (500k window) over Astra (272k).

## Escalation ladder (when a run fails review)

1. Was the brief the problem (missing context, ambiguous acceptance criteria)? Fix the brief and
   rerun on the **same** config. This is the most common cause — check it first.
2. Otherwise raise effort one step (medium → high).
3. Then move up one tier (Luna → Terra → Sol → Astra).
4. After two failed attempts at Astra `high`, stop delegating that piece: do it yourself or bring
   the problem to the user.

## Speed tier

`-c service_tier="priority"` ("Fast", ~2x speed, more usage). Only for small tasks the user is
actively waiting on. Never for long or parallel runs.

## Examples

| Task | Pick | Why |
|---|---|---|
| Rename `temp_c` → `temperature_c` across the gateway and update tests | Luna `low` | Fully mechanical, grep-verifiable. |
| Add a `GET /api/rooms/{id}/history` endpoint mirroring the existing `/latest` one | Terra `medium` | Clear spec, existing pattern to copy. |
| Write pytest coverage for `storage.py` | Terra `medium` | Straightforward, code exists to read. |
| "MQTT bridge sometimes drops messages after reconnect" | Sol `high` | Unknown cause, needs investigation. |
| Refactor packet format shared by two firmware boards and the gateway | Sol `high` | Cross-module, must stay consistent. |
| ESP-NOW receive callback corrupts data under load (ISR/race) | Astra `high` | Concurrency + hardware timing. |
| Update README setup section after a config change | Luna `medium` | Docs, low risk. |
