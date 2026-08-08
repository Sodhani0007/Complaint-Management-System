# Git Workflow

## Setting up from scratch

```bash
git init
```
Initializes a new, empty git repository in the current directory (creates a hidden `.git/`
folder that tracks all history). Run once, at the project root.

```bash
git add <file>       # stage a specific file
git add .             # stage everything in the current directory (respecting .gitignore)
```
Moves changes into the "staging area" — the draft of what your next commit will contain. Nothing
is actually recorded in history until you commit.

```bash
git commit -m "Your message here"
```
Records everything currently staged as a permanent snapshot in history, with your message
explaining what changed and why. Each commit gets a unique hash you can reference later.

```bash
git branch -M main
```
Renames the current branch to `main` (git's default branch name used to be `master`; `-M` forces
the rename even if `main` doesn't exist yet). Run once, early.

```bash
git remote add origin <your-repo-url>
```
Registers a remote named `origin` pointing at your GitHub repository URL — this is what `git push`
and `git pull` talk to. Run once, after creating the empty repo on GitHub.

```bash
git push -u origin main
```
Uploads your local commits to the `origin` remote's `main` branch. `-u` sets `main` to track
`origin/main`, so future pushes can just be `git push`.

## This project's actual commit history

Rather than fabricating a fictional multi-week commit history to imply the project was built
gradually over time, this repo's git history genuinely reflects the order modules were actually
built and verified during development — see `git log` in this repo for the real sequence. That's
a better interview artifact than a staged one anyway: you can talk through any commit because it's
the actual order you (with AI assistance) built and tested things in.

If you continue developing this project, keep following the same pattern:

```bash
git checkout -b feature/duplicate-detection   # new branch per feature
# ... make changes ...
git add app/ai/nodes/duplicate_check.py
git commit -m "Add duplicate complaint detection node"
git push -u origin feature/duplicate-detection
# then open a PR into main on GitHub
```

## Everyday commands worth knowing

| Command | What it does |
|---|---|
| `git status` | Shows staged/unstaged/untracked changes |
| `git diff` | Shows unstaged changes line-by-line |
| `git log --oneline` | Compact commit history |
| `git log --oneline --graph --all` | Visualize branch history |
| `git checkout -b <branch>` | Create and switch to a new branch |
| `git stash` | Temporarily shelve uncommitted changes |
| `git pull` | Fetch + merge the latest remote changes |
