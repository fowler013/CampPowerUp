# 🚀 GitHub PR Strategy & Best Practices

## 📋 Overview

This document outlines the Pull Request (PR) strategy for CampPowerUp, applying GitHub best practices and organizing work into manageable, reviewable chunks.

---

## 🎯 PR Organization Strategy

### Phase 1: Foundation Infrastructure (Current)

#### PR #1: Core Configuration & Database Layer

**Title**: `feat: Add configuration management and database layer (Phase 1 - Part 1)`  
**Branch**: `feature/config-and-database`  
**Files**:

- `src/config/__init__.py` (200 lines)
- `src/shared/database.py` (300 lines)
- Updated `requirements.txt`

**Why Separate?**: These are foundational components that other code will depend on.

**Size**: ~500 lines | **Complexity**: Medium | **Risk**: Low

---

#### PR #2: Database Management Scripts

**Title**: `feat: Add professional database backup/restore/maintenance scripts (Phase 1 - Part 2)`  
**Branch**: `feature/database-scripts`  
**Depends On**: PR #1  
**Files**:

- `scripts/database/backup.py` (250 lines)
- `scripts/database/restore.py` (200 lines)
- `scripts/database/maintenance.py` (250 lines)

**Why Separate?**: Can be reviewed and tested independently of core library.

**Size**: ~700 lines | **Complexity**: Medium | **Risk**: Low

---

#### PR #3: CI/CD Pipeline & GitHub Integration

**Title**: `feat: Add CI/CD workflows and GitHub templates (Phase 1 - Part 3)`  
**Branch**: `feature/cicd-github`  
**Files**:

- `.github/workflows/ci.yml` (150 lines)
- `.github/workflows/deploy.yml` (100 lines)
- `.github/PULL_REQUEST_TEMPLATE/feature.md`
- `.github/PULL_REQUEST_TEMPLATE/bugfix.md`
- `.github/ISSUE_TEMPLATE/*.md`

**Why Separate?**: CI/CD can be set up independent of code changes.

**Size**: ~500 lines | **Complexity**: Low | **Risk**: Low

---

#### PR #4: Kit AI Bot Configuration

**Title**: `feat: Add Kit AI bot integration configuration (Phase 1 - Part 4)`  
**Branch**: `feature/kit-ai-integration`  
**Files**:

- `.kit/config.yaml` (350 lines)
- `MASTER_PROJECT_MANAGEMENT.md` (250 lines)

**Why Separate?**: Bot configuration doesn't affect running code.

**Size**: ~600 lines | **Complexity**: Low | **Risk**: None

---

#### PR #5: VS Code Workspace Configuration

**Title**: `feat: Add professional VS Code workspace configuration (JetBrains-style)`  
**Branch**: `feature/vscode-workspace`  
**Files**:

- `.vscode/settings.json`
- `.vscode/extensions.json`
- `.vscode/launch.json`
- `.vscode/tasks.json` (updated)
- `docs/VSCODE_GUIDE.md`
- `docs/MCP_SERVERS_GUIDE.md`

**Why Separate?**: IDE configuration is developer tooling, not application code.

**Size**: ~1000 lines | **Complexity**: Low | **Risk**: None

---

#### PR #6: Documentation & Project Planning

**Title**: `docs: Add comprehensive project documentation and reorganization plan`  
**Branch**: `feature/documentation`  
**Files**:

- `PROJECT_REORGANIZATION_PLAN.md`
- `PHASE1_PROGRESS_REPORT.md`
- `SESSION_SUMMARY.md`
- `QUICK_REFERENCE.md`
- `.github/README_GITHUB.md`
- `docs/architecture/ARCHITECTURE_DIAGRAM.md`

**Why Separate?**: Documentation doesn't affect functionality.

**Size**: ~2500 lines | **Complexity**: Low | **Risk**: None

---

### Phase 2: Code Migration (Future)

#### PR #7: Shared Utilities (Authentication, Email, Logging)

**Branch**: `feature/shared-utilities`  
**Files**:

- `src/shared/auth.py`
- `src/shared/email.py`
- `src/shared/logging.py`

---

#### PR #8: Testing Framework Setup

**Branch**: `feature/testing-framework`  
**Files**:

- `pytest.ini`
- `tests/conftest.py`
- `tests/unit/test_config.py`
- `tests/unit/test_database.py`

---

#### PR #9-12: Module Migration (Registration, Admin, etc.)

**Branches**: `feature/migrate-<module>`  
**Separate PRs for each major module**

---

## 📊 PR Size Guidelines

### Ideal PR Sizes

| Size   | Lines Changed | Review Time | Approval Time |
| ------ | ------------- | ----------- | ------------- |
| **XS** | < 100         | 10 min      | Same day      |
| **S**  | 100-300       | 20 min      | Same day      |
| **M**  | 300-500       | 45 min      | 1-2 days      |
| **L**  | 500-1000      | 1-2 hours   | 2-3 days      |
| **XL** | 1000+         | 3+ hours    | 3-7 days      |

**Target**: Keep PRs in S-M range (100-500 lines)

### Our PRs

| PR  | Size | Lines | Category           |
| --- | ---- | ----- | ------------------ |
| #1  | M    | ~500  | Foundation         |
| #2  | L    | ~700  | Scripts            |
| #3  | M    | ~500  | CI/CD              |
| #4  | L    | ~600  | Configuration      |
| #5  | L    | ~1000 | IDE Setup          |
| #6  | XL   | ~2500 | Docs (OK for docs) |

---

## ✅ PR Checklist (Required)

Before creating PR, ensure:

### Code Quality

- [ ] Code formatted with Black (`black src/ tests/`)
- [ ] Imports sorted with isort (`isort src/ tests/ --profile=black`)
- [ ] No linting errors (`pylint src/`)
- [ ] Type checking passes (`mypy src/ --ignore-missing-imports`)
- [ ] No security issues (`bandit -r src/`)

### Testing

- [ ] All existing tests pass (`pytest`)
- [ ] New tests added for new code
- [ ] Test coverage ≥ 80% (`pytest --cov=src --cov-fail-under=80`)

### Documentation

- [ ] README updated (if needed)
- [ ] Docstrings added for all functions/classes
- [ ] Architecture diagram updated (if needed)
- [ ] CHANGELOG updated

### CS Principles

- [ ] CYBV 301 (Security) considerations documented
- [ ] APCV 360 (Database) principles applied
- [ ] CYBV 302 (Integration) patterns followed

### Git

- [ ] Branch up to date with base branch
- [ ] Commits are logical and well-messaged
- [ ] No merge conflicts
- [ ] Signed commits (optional)

---

## 📝 PR Title Convention

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation only
- style: Code style (formatting, not functionality)
- refactor: Code refactoring
- perf: Performance improvement
- test: Adding tests
- chore: Maintenance (dependencies, etc.)
- ci: CI/CD changes
- security: Security fix

Examples:
feat(config): add environment-based configuration system
fix(database): resolve connection pool exhaustion issue
docs: add VS Code workspace setup guide
ci: add automated security scanning with Bandit
security(auth): implement password hashing with bcrypt
```

---

## 🎯 PR Description Template

### Feature PR

```markdown
## 📝 Feature Description

Brief description of what this feature adds.

## 🎯 Problem/Need

What problem does this solve?

## 💡 Solution

How does this feature work?

## 🎓 CS Principles Applied

- [ ] CYBV 301 (Security) - How?
- [ ] APCV 360 (Database) - How?
- [ ] CYBV 302 (Integration) - How?

## 🧪 Testing

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

**Test Coverage**: \_\_\_%

## 📊 Changes

- Added X
- Modified Y
- Refactored Z

## 🔗 Related Issues

Closes #X, Relates to #Y

## 📸 Screenshots

(If UI changes)

## ✅ Checklist

- [ ] Code formatted (black, isort)
- [ ] Tests passing
- [ ] Documentation updated
- [ ] No security vulnerabilities
- [ ] Ready for review
```

---

## 🔍 Review Process

### Self-Review (Before Creating PR)

1. **Read your own code** - Review every line as if you're the reviewer
2. **Check for TODOs** - Remove or track any TODO comments
3. **Verify tests** - Run full test suite locally
4. **Check documentation** - Ensure all new code is documented
5. **Security review** - Check for any security implications

### Reviewer Guidelines

**What to Look For:**

1. **Correctness** - Does the code do what it's supposed to?
2. **Security** - Any vulnerabilities? (CYBV 301)
3. **Performance** - Any obvious performance issues? (APCV 360)
4. **Testing** - Adequate test coverage?
5. **Readability** - Is the code clear and maintainable?
6. **Architecture** - Fits the overall design? (CYBV 302)

**Review Levels:**

- 🟢 **Approve** - Ready to merge
- 🟡 **Request Changes** - Issues must be fixed
- 🔵 **Comment** - Suggestions, questions, non-blocking

---

## 🚀 Merge Strategy

### Branch Protection Rules

**main (production)**:

- [ ] Require PR approval (1+ reviewers)
- [ ] Require status checks to pass
  - [ ] CI Pipeline (tests, lint, security)
  - [ ] Test coverage ≥ 80%
- [ ] Require up-to-date branch
- [ ] Require signed commits (optional)
- [ ] No direct pushes

**develop (staging)**:

- [ ] Require PR approval
- [ ] Require status checks to pass
- [ ] Allow force pushes (for rebasing)

### Merge Options

1. **Squash and Merge** (Recommended for feature branches)

   - Combines all commits into one
   - Keeps main/develop history clean
   - Use for most PRs

2. **Rebase and Merge** (For clean commit history)

   - Preserves individual commits
   - Use when commits are logical and well-messaged
   - Use for hotfixes

3. **Merge Commit** (Avoid)
   - Creates merge commit
   - Clutters history
   - Only use for special cases

---

## 🎯 GitHub Features to Use

### Labels

Create these labels in your repository:

**Type:**

- `bug` - Something isn't working
- `enhancement` - New feature or request
- `documentation` - Improvements to documentation
- `security` - Security vulnerability or improvement

**Priority:**

- `priority: critical` - Must be fixed immediately
- `priority: high` - Should be fixed soon
- `priority: medium` - Fix when possible
- `priority: low` - Nice to have

**Status:**

- `status: in-progress` - Currently being worked on
- `status: blocked` - Blocked by another issue
- `status: needs-review` - Waiting for code review
- `status: needs-testing` - Waiting for QA

**CS Courses:**

- `CYBV301` - Security-related
- `APCV360` - Database-related
- `CYBV302` - Integration-related

**Size:**

- `size: XS` - < 100 lines
- `size: S` - 100-300 lines
- `size: M` - 300-500 lines
- `size: L` - 500-1000 lines
- `size: XL` - 1000+ lines

---

### Milestones

Create milestones for tracking progress:

1. **Phase 1: Foundation** (Current)

   - Due: December 15, 2024
   - PRs: #1-6

2. **Phase 2: Code Migration**

   - Due: January 15, 2025
   - PRs: #7-12

3. **Phase 3: Testing & Security**

   - Due: February 1, 2025

4. **Phase 4: Kit AI Integration**

   - Due: February 15, 2025

5. **Phase 5: Documentation & Polish**
   - Due: March 1, 2025

---

### Projects (GitHub Projects)

Create a project board:

**Columns:**

1. **Backlog** - Future work
2. **Todo** - Ready to start
3. **In Progress** - Currently working
4. **In Review** - PR open, waiting for review
5. **Done** - Merged

**Views:**

- **By Phase** - Group by milestone
- **By Priority** - Sort by priority labels
- **By CS Course** - Group by CYBV/APCV labels

---

### Branch Protection

Enable for `main` and `develop`:

```
Settings → Branches → Add Branch Protection Rule

For main:
✅ Require pull request before merging
   ✅ Require 1 approval
   ✅ Dismiss stale reviews
   ✅ Require review from code owners
✅ Require status checks to pass
   ✅ CI Pipeline
   ✅ Test Coverage
✅ Require branches to be up to date
✅ Include administrators
✅ Restrict who can push
```

---

### Code Owners

Create `.github/CODEOWNERS`:

```
# Default owner for everything
* @fowler013

# CS Principle-specific owners
src/config/** @fowler013  # CYBV 301 & APCV 360
src/shared/database.py @fowler013  # APCV 360
src/shared/auth.py @fowler013  # CYBV 301
tests/security/** @fowler013  # CYBV 301

# Documentation
docs/** @fowler013
*.md @fowler013

# CI/CD
.github/workflows/** @fowler013
```

---

### Issue Templates

Already created:

- `.github/ISSUE_TEMPLATE/bug_report.md`
- `.github/ISSUE_TEMPLATE/feature_request.md`
- `.github/ISSUE_TEMPLATE/security_vulnerability.md`

### PR Templates

Already created:

- `.github/PULL_REQUEST_TEMPLATE/feature.md`
- `.github/PULL_REQUEST_TEMPLATE/bugfix.md`

---

## 🎓 CS Course Integration in PRs

### Tagging PRs with Course Principles

**In PR Description:**

```markdown
## 🎓 CS Principles Applied

### CYBV 301 - Cybersecurity Fundamentals

- ✅ Implemented input validation
- ✅ Added CSRF protection
- ✅ Secure session management

### APCV 360 - Database Design & Management

- ✅ Connection pooling implemented
- ✅ Transaction management with rollback
- ✅ Query optimization with indexes

### CYBV 302 - System Integration

- ✅ MVC architecture followed
- ✅ Service layer abstraction
- ✅ Error handling and logging
```

**In Commit Messages:**

```
feat(database): add connection pooling (APCV360)

Implements database connection pooling following APCV 360 principles:
- Pool size: 5 (dev), 20 (prod)
- Auto-retry on connection failure
- Proper resource cleanup with context managers

Related to APCV 360 Module 3: Database Optimization
```

---

## 📊 PR Metrics to Track

### Via GitHub Insights

Track these metrics:

1. **PR Cycle Time** - Time from open to merge
2. **Review Time** - Time to first review
3. **Number of Reviews** - How many reviews per PR
4. **Merge Rate** - % of PRs that get merged
5. **Revert Rate** - % of PRs that get reverted

**Target Goals:**

- PR Cycle Time: < 48 hours
- Review Time: < 4 hours
- Number of Reviews: 1-2
- Merge Rate: > 95%
- Revert Rate: < 2%

---

## 🚀 Automation with Kit AI Bot

Once Kit AI is integrated:

### Auto-Review

- ✅ Automatically check code style
- ✅ Verify tests pass
- ✅ Check security issues
- ✅ Verify documentation updated

### Auto-Label

- ✅ Add size label based on lines changed
- ✅ Add CS course labels based on files changed
- ✅ Add priority based on keywords

### Auto-Assign

- ✅ Assign to reviewer based on CODEOWNERS
- ✅ Assign to milestone based on branch name

---

## 💡 Best Practices Summary

1. ✅ **Keep PRs small** (300-500 lines ideal)
2. ✅ **One feature per PR** - Don't mix unrelated changes
3. ✅ **Write descriptive titles** - Use conventional commits
4. ✅ **Self-review first** - Review your own code before requesting review
5. ✅ **Add context** - Explain why, not just what
6. ✅ **Link issues** - Use "Closes #X" to auto-close issues
7. ✅ **Document CS principles** - Show which courses apply
8. ✅ **Include tests** - Don't merge code without tests
9. ✅ **Update docs** - Keep documentation in sync
10. ✅ **Be responsive** - Address review comments quickly

---

## 📚 Resources

- [GitHub PR Best Practices](https://github.com/blog/1943-how-to-write-the-perfect-pull-request)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Code Review Guidelines](https://google.github.io/eng-practices/review/)
- [GitHub Branch Protection](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)

---

**Last Updated**: December 2, 2024  
**Status**: Ready to Create PRs ✅  
**Next Step**: Create PR #1 (Config & Database Layer)
