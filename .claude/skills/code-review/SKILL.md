---
name: code-review
description: Pre-PR code review for this project. Reviews staged or branch changes for
  bugs, architecture violations, and style issues. Use whenever the user asks to review
  code, check changes before a PR, self-review, or wants feedback on what they've written.
---

# Code Review Skill

## Step 1 — Get the diff and understand what changed

```bash
git diff --staged          # if reviewing before a commit
git diff main...HEAD       # if reviewing a whole branch
git status
```

For each changed file, read it to understand its role:
```bash
cat <changed_file>
```

Also read the current graph and state to understand the system's structure:
```bash
cat src/graph/state.py       # current GraphState schema
cat src/graph/blueprint.py   # current routing logic
```

## Step 2 — Run Pylint on changed files

```bash
pylint <changed_file_1> <changed_file_2>
```

Flag all `E` (error) items as blocking. For warnings, focus on:
- `W0611` unused imports
- `W0612` unused variables
- `W1203` logging with f-string (use `%s` style)
- `R0914` too many local variables (node may be doing too much)

## Step 3 — Architecture checks

Apply these based on what actually changed — skip sections irrelevant to the diff.

**If a node changed (`src/nodes/`)**
- Does it return a `dict` with partial state updates, not a mutated state object?
- Is the signature `def node_name(state: GraphState) -> dict:`?
- Does it do one thing only?
- Are there any LLM calls or I/O at module level (outside functions)?

**If graph routing changed (`src/graph/blueprint.py`)**
- Do all conditional edges have a path to `END`?
- Is the graph compiled at module level, not inside a function or callback?
- Does any new node have a corresponding routing case?

**If state schema changed (`src/graph/state.py`)**
- Are all new fields typed?
- Are any nodes now broken by the schema change? Check each node in `src/nodes/`.

**If Streamlit components changed (`src/components/`, `src/app.py`)**
- Is any business logic or graph construction inside `app.py` or a Streamlit callback?
- Are session state keys initialised with a guard (`if "key" not in st.session_state`)?
- Are `.invoke()` / `.stream()` calls wrapped in `st.spinner()`?

**If config or secrets changed (`src/utils/config.py`)**
- Are all new secrets using `SecretStr`?
- Are there any direct `os.environ` calls in nodes or components that should go through config?

**If data pipeline changed (`scripts/`)**
- Does `ingest_sec.py` still skip already-downloaded tickers on resume?
- Does `index.py` handle a pre-existing `data/index/` correctly (or document when it doesn't)?

**If deployment files changed (`Dockerfile`, `cloudbuild.yaml`)**
- Are any secrets baked into the image? (They must come from Secret Manager at runtime.)
- Are memory/concurrency changes intentional?

## Step 4 — Security & hygiene

- [ ] No hardcoded API keys, tokens, or passwords anywhere in the diff
- [ ] No `.env` contents visible
- [ ] No `print()` statements — use `logging`
- [ ] No leftover debug code or bare `TODO` comments without a linked issue

## Step 5 — Summary report

```
## Code Review Summary

### ✅ Passed
<what looks good>

### ⚠️ Warnings
<non-blocking issues>

### ❌ Must Fix Before Merging
<blocking issues — be specific: file + line>

### 💡 Suggestions
<optional improvements>
```

Only include sections that have content. Reference file names and line numbers.
Be direct — clearly distinguish blocking from non-blocking.