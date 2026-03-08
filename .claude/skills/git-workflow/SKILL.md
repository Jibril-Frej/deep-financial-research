---
name: git-workflow
description: Full git workflow — stage, commit, push, and open a PR. Use whenever the
  user wants to commit changes, push a branch, create a pull request, ship a feature,
  or any combination. Triggers on "commit this", "push my changes", "open a PR",
  "ship this", "create a pull request".
---

# Git Workflow Skill

## Step 1 — Assess current state

```bash
git status
git diff --staged
git branch --show-current
```

Report: current branch, what's staged vs unstaged. If on `main`, warn and offer to
create a feature branch before continuing.

## Step 2 — Branch check

If on `main`, suggest a branch name based on what the changes do:
```bash
git checkout -b <type>/<short-description>
```
Types: `feat`, `fix`, `refactor`, `chore`, `docs` — kebab-case, under 40 chars.

## Step 3 — Stage changes

If nothing is staged, ask whether to stage everything or specific paths:
```bash
git add .
git add src/nodes/some_node.py   # example of specific path
```
Never stage: `.env`, `data/raw/`, `data/index/`

## Step 4 — Analyse the diff

```bash
git diff --staged
```

Read the diff. Identify what changed and which part of the system it affects. Use that
to pick the right commit type and scope (see CLAUDE.md for the scope list).

Decide if this is one logical commit or should be split.

## Step 5 — Propose a commit message

Format:
```
<type>(<scope>): <description under 72 chars>

<optional body — WHY not WHAT, wrap at 100 chars>

<optional footer — e.g. Closes #123>
```

Show the proposed message to the user and ask for approval before committing.

## Step 6 — Commit

```bash
git commit -m "<message>"
```

Do not add `Co-Authored-By` or AI attribution unless the user explicitly asks.

## Step 7 — Push

```bash
git push -u origin <branch-name>   # first push (sets upstream)
git push origin <branch-name>      # subsequent pushes
```

## Step 8 — Open a PR

Use GitHub CLI if available:
```bash
gh pr create \
  --base main \
  --title "<same as commit title>" \
  --body "..."
```

PR body template:
```markdown
## Summary
<1-2 sentences — what and why>

## Changes
- <one bullet per logical change>

## Testing
- [ ] Tested via `python src/main.py`
- [ ] Tested via `streamlit run src/app.py`
- [ ] Pylint passes on changed files
- [ ] No `.env` or `data/` files staged

## Notes
<edge cases, follow-up work, deployment impact>
```

If `gh` is not installed, print the PR body for manual pasting.

## Rules
- Never stage `.env`, `data/raw/`, `data/index/`
- Never push to `main` directly
- Always confirm commit message before running `git commit`
- If nodes or graph changed, suggest a quick test with `python src/main.py` before pushing