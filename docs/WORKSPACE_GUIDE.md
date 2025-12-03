# 🎯 Using Git Branches + VS Code Workspaces Together

## Overview

You now have **TWO powerful tools** working together:
1. **Git Branches** - Control your code versions (staging/production)
2. **VS Code Workspaces** - Control your editor environment

## 📁 Available Workspaces

### 1. **CampPowerUp-Development.code-workspace**
**Use when:** Working on new features on `develop` or `feature/*` branches

**Features:**
- 🧪 Shows test files prominently
- 🐛 Debug mode enabled by default
- 🔧 Development environment variables
- 📝 All development tools visible

**Open with:**
```bash
code CampPowerUp-Development.code-workspace
```

---

### 2. **CampPowerUp-Production.code-workspace**
**Use when:** Reviewing code on `main` branch or preparing for deployment

**Features:**
- 🚀 Production environment variables
- 🔒 Read-only mode for critical files (safety)
- 📦 Hides test files for cleaner view
- ✅ Production-focused tools

**Open with:**
```bash
code CampPowerUp-Production.code-workspace
```

---

### 3. **Nivet.code-workspace**
**Use when:** Personal workspace (your custom setup)

**Features:**
- 🎨 Your personal preferences
- 📌 Your favorite open tabs
- 🪟 Your preferred window layout

---

## 🔄 Typical Workflow

### Scenario 1: Developing a New Feature

```bash
# 1. Switch to development context
git checkout develop
git checkout -b feature/my-awesome-feature

# 2. Open development workspace
code CampPowerUp-Development.code-workspace

# 3. Develop with all dev tools visible
# ... make changes ...

# 4. Commit and push
git add .
git commit -m "feat: add awesome feature"
git push -u origin feature/my-awesome-feature

# 5. Create PR to develop (staging)
gh pr create --base develop --head feature/my-awesome-feature
```

---

### Scenario 2: Testing in Staging (Develop Branch)

```bash
# 1. Switch to develop branch
git checkout develop
git pull

# 2. Still use development workspace (for testing)
code CampPowerUp-Development.code-workspace

# 3. Test the integrated features
# Run tests, check integration

# 4. If all good, prepare for production
```

---

### Scenario 3: Deploying to Production

```bash
# 1. Switch to main branch
git checkout main

# 2. Open PRODUCTION workspace
code CampPowerUp-Production.code-workspace

# 3. Review with production lens
# - Test files hidden
# - Production settings active
# - Read-only mode protects critical files

# 4. Merge from develop
git merge develop
git push

# 5. Deploy to Railway (automatic from main)
```

---

## 🎨 Visual Workflow

```
┌─────────────────────────────────────────────────┐
│  Your Work: feature/my-feature                  │
│  📂 Workspace: CampPowerUp-Development          │
│  🎯 Focus: Build new features                   │
└────────────────┬────────────────────────────────┘
                 │ git push + PR
                 ↓
┌─────────────────────────────────────────────────┐
│  Staging: develop branch                        │
│  📂 Workspace: CampPowerUp-Development          │
│  🎯 Focus: Integration testing                  │
└────────────────┬────────────────────────────────┘
                 │ git merge + PR
                 ↓
┌─────────────────────────────────────────────────┐
│  Production: main branch                        │
│  📂 Workspace: CampPowerUp-Production           │
│  🎯 Focus: Production review & deploy           │
└─────────────────────────────────────────────────┘
```

---

## 💡 Pro Tips

### Tip 1: Quick Workspace Switching
Add aliases to your `~/.zshrc`:

```bash
# Open development workspace
alias devcamp="cd ~/Documents/CampPowerUp && code CampPowerUp-Development.code-workspace"

# Open production workspace
alias prodcamp="cd ~/Documents/CampPowerUp && code CampPowerUp-Production.code-workspace"
```

### Tip 2: Workspace-Specific Tasks
Each workspace inherits tasks from `.vscode/tasks.json`, but you can add workspace-specific tasks in the workspace file itself.

### Tip 3: Multiple Windows
You can have BOTH workspaces open simultaneously:
- **Window 1**: Development workspace on `feature/branch`
- **Window 2**: Production workspace on `main` (for reference)

### Tip 4: Workspace Extensions
Some extensions can be enabled/disabled per workspace:
- Enable `GitHub Copilot` in Development workspace
- Disable heavy extensions in Production workspace for performance

---

## 🔐 Security Note

**Production Workspace Safety Features:**
- Read-only mode on critical files (`app.py`, `requirements.txt`)
- Prevents accidental edits to production code
- Use only for review and deployment

If you need to edit on `main`, temporarily disable read-only or work on a hotfix branch.

---

## 🎯 When to Use Which Workspace

| Situation | Workspace | Git Branch |
|-----------|-----------|------------|
| Building new feature | Development | `feature/*` |
| Fixing bug | Development | `bugfix/*` |
| Testing integration | Development | `develop` |
| Code review | Development | `feature/*` |
| Pre-deployment review | Production | `develop` or `main` |
| Deploying | Production | `main` |
| Hotfix (emergency) | Development | `hotfix/*` |
| Personal experiments | Nivet | Any branch |

---

## 📚 Further Reading

- VS Code Workspaces Docs: https://code.visualstudio.com/docs/editor/workspaces
- Git Branching Strategy: See `docs/GITHUB_PR_STRATEGY.md`
- VS Code Guide: See `docs/VSCODE_GUIDE.md`

---

**Last Updated:** December 3, 2025  
**Status:** ✅ Ready to Use
