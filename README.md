# AI-skills

A collection of reusable AI skills. Each skill is a self-contained folder with a `SKILL.md`
(a name, a description of when to use it, and the instructions), plus any scripts, references
and templates it needs.

## Skills

| Skill | What it does |
|---|---|
| [`codex-boss`](codex-boss/) | Claude acts as lead engineer and delegates work to OpenAI Codex agents through the Codex CLI: decomposes the task, picks the model and reasoning effort per piece, writes the briefs, runs each agent in its own git worktree and Terminal tab, then reviews, verifies and integrates the result. |

## Using a skill

Copy the skill's folder into your skills directory. For Claude Code that is
`~/.claude/skills/` (user-wide) or `.claude/skills/` inside a project:

```bash
cp -r codex-boss ~/.claude/skills/
```

The agent then loads the skill automatically when a request matches its description.

## Layout

```
<skill-name>/
├── SKILL.md        # frontmatter (name, description) + instructions
├── references/     # longer notes the skill reads on demand
├── scripts/        # helper scripts
├── assets/         # templates
└── evals/          # test prompts and graders
```

Only `SKILL.md` is required; the other folders appear when a skill needs them.
