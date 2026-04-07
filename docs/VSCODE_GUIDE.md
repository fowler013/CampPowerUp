# 🎯 VS Code Workspace Guide - JetBrains Style Configuration

## 📋 Overview

This workspace is configured to mimic **JetBrains GoLand/PyCharm** functionality in VS Code, providing a professional Python development environment with integrated testing, debugging, and database management.

---

## 🎨 JetBrains Features Replicated

| JetBrains Feature      | VS Code Equivalent         | How to Use                          |
| ---------------------- | -------------------------- | ----------------------------------- |
| **Run Configurations** | Tasks + Launch Configs     | `Cmd+Shift+P` → "Tasks: Run Task"   |
| **Project View**       | Explorer with file nesting | Left sidebar, organized by type     |
| **Structure View**     | Outline view               | `Cmd+Shift+O` for symbols           |
| **Database Tools**     | SQLTools extension         | See Database section                |
| **TODO View**          | Todo Tree extension        | Left sidebar "TODO TREE"            |
| **Git Integration**    | GitLens + Git Graph        | Source Control panel                |
| **Terminal**           | Integrated Terminal        | `` Ctrl+` ``                        |
| **Run Tests**          | Test Explorer              | Left sidebar "Testing"              |
| **Refactoring**        | Pylance + Python extension | Right-click → "Refactor"            |
| **Code Actions**       | Quick Fix (lightbulb)      | `Cmd+.`                             |
| **Find Usages**        | References                 | Right-click → "Find All References" |
| **Go to Definition**   | Built-in                   | `F12` or `Cmd+Click`                |
| **Recent Files**       | Quick Open                 | `Cmd+P`                             |
| **Bookmarks**          | Bookmarks extension        | See Extensions                      |

---

## 🚀 Quick Start

### 1. Install Recommended Extensions

When you open this workspace, VS Code will prompt you to install recommended extensions. **Accept** to install all 40+ extensions.

**Critical Extensions** (install first):

- **ms-python.python** - Python support
- **ms-python.vscode-pylance** - IntelliSense
- **ms-python.black-formatter** - Code formatting
- **github.copilot** - AI assistance
- **eamodio.gitlens** - Git supercharged
- **mtxr.sqltools** - Database tools
- **gruntfuggly.todo-tree** - TODO tracking

### 2. Configure Python Interpreter

1. Press `Cmd+Shift+P`
2. Type "Python: Select Interpreter"
3. Choose `.venv/bin/python` (should auto-detect)

### 3. Verify Setup

Run this task to verify everything works:

- `Cmd+Shift+P` → "Tasks: Run Task" → "📊 Git Status"

---

## 🎯 Common Tasks (JetBrains "Run Configurations")

### Running the Application

**Method 1: Using Tasks** (Recommended)

```
Cmd+Shift+P → "Tasks: Run Task" → "🚀 Start Registration Server"
```

**Method 2: Using Debugger** (Best for debugging)

```
F5 (or Debug panel) → "🚀 Flask: Registration App (Development)"
```

**Method 3: Keyboard Shortcut**

```
Cmd+Shift+B (Default build task)
```

### Running Tests

**All Tests:**

```
Cmd+Shift+P → "Tasks: Run Task" → "🧪 Run All Tests"
```

**Test Explorer:**

```
Click Testing icon in left sidebar → Click play button
```

**With Debugger:**

```
F5 → "🧪 Pytest: All Tests"
```

### Code Quality Checks

**Format + Lint + Type Check + Security:**

```
Cmd+Shift+P → "Tasks: Run Task" → "✅ Run All Quality Checks"
```

**Individual Checks:**

- **Format**: "✨ Format Code (Black)"
- **Sort Imports**: "📦 Sort Imports (isort)"
- **Lint**: "🔍 Lint Code (Pylint)"
- **Type Check**: "🔎 Type Check (mypy)"
- **Security**: "🛡️ Security Scan (Bandit)"

---

## 💾 Database Management (APCV 360)

### Using SQLTools Extension

1. **Open Database View**

   - Click SQLite icon in left sidebar
   - Or `Cmd+Shift+P` → "SQLTools: Add New Connection"

2. **Connect to Database**

   ```
   Name: CampPowerUp Registration
   Database File: /Users/tevinfowler/Documents/CampPowerUp/registration_submissions.db
   ```

3. **Features:**
   - View tables and data
   - Run SQL queries
   - Export data
   - Generate ER diagrams

### Using Database Scripts

**Backup:**

```
Cmd+Shift+P → "Tasks: Run Task" → "💾 Backup Database"
```

**Restore:**

```
Cmd+Shift+P → "Tasks: Run Task" → "💾 Restore Database (Latest)"
```

**Maintenance:**

```
Cmd+Shift+P → "Tasks: Run Task" → "🔧 Run Database Maintenance"
```

---

## 🐛 Debugging (Like JetBrains)

### Breakpoints

1. Click left margin of code (red dot appears)
2. Press `F5` to start debugging
3. Use debug toolbar:
   - **Continue** (`F5`)
   - **Step Over** (`F10`)
   - **Step Into** (`F11`)
   - **Step Out** (`Shift+F11`)
   - **Restart** (`Cmd+Shift+F5`)
   - **Stop** (`Shift+F5`)

### Debug Configurations Available

- `🚀 Flask: Registration App (Development)` - Debug web server
- `🧪 Pytest: All Tests` - Debug all tests
- `🧪 Pytest: Unit Tests Only` - Debug unit tests
- `🔧 Python: Current File` - Debug currently open file
- `💾 Database: Backup Script` - Debug backup script

### Debug Console

Access variables, evaluate expressions:

```python
# In debug console while paused:
print(variable_name)
dir(object)
help(function)
```

---

## 🔍 Code Navigation (JetBrains-style)

### Go To...

| Action                   | Shortcut       | Description                |
| ------------------------ | -------------- | -------------------------- |
| **Go to File**           | `Cmd+P`        | Quick open any file        |
| **Go to Symbol**         | `Cmd+Shift+O`  | Jump to function/class     |
| **Go to Definition**     | `F12`          | Jump to where it's defined |
| **Go to Implementation** | `Cmd+F12`      | Jump to implementation     |
| **Find References**      | `Shift+F12`    | Show all usages            |
| **Go Back**              | `Ctrl+-`       | Navigate back              |
| **Go Forward**           | `Ctrl+Shift+-` | Navigate forward           |

### Search

| Action               | Shortcut      | Description               |
| -------------------- | ------------- | ------------------------- |
| **Find**             | `Cmd+F`       | Find in current file      |
| **Replace**          | `Cmd+H`       | Replace in current file   |
| **Find in Files**    | `Cmd+Shift+F` | Search entire project     |
| **Replace in Files** | `Cmd+Shift+H` | Replace in entire project |

### Refactoring

| Action               | Shortcut         | Description              |
| -------------------- | ---------------- | ------------------------ |
| **Rename Symbol**    | `F2`             | Rename variable/function |
| **Extract Variable** | Select → `Cmd+.` | Extract to variable      |
| **Extract Method**   | Select → `Cmd+.` | Extract to method        |
| **Organize Imports** | `Shift+Alt+O`    | Sort and remove unused   |

---

## 📊 Project Structure View

### Explorer (Project View)

The left sidebar shows your project with **file nesting** enabled:

```
CampPowerUp/
├── 📁 src/
│   ├── 📁 config/           # Configuration
│   ├── 📁 shared/           # Utilities
│   └── ...
├── 📁 tests/                # Tests
├── 📁 docs/                 # Documentation
├── 📁 scripts/              # Scripts
├── 📁 .github/              # CI/CD
├── 📄 requirements.txt      # Dependencies
└── 📄 README.md             # Documentation
```

**Features:**

- Folders sorted before files
- Related files nested (e.g., `.pyc` under `.py`)
- Right-click → "Reveal in Finder" to open in macOS

### Outline View

Shows structure of current file (like JetBrains Structure):

1. Bottom of Explorer → "OUTLINE"
2. Shows functions, classes, methods
3. Click to jump to that section

---

## ✅ TODO View (Like JetBrains TODO Tool Window)

### Using Todo Tree Extension

**View TODOs:**

- Click "TODO TREE" in left sidebar
- Shows all TODOs, FIXMEs, NOTEs, etc.

**Custom Tags:**

```python
# TODO: Regular task
# FIXME: Bug to fix
# NOTE: Important note
# SECURITY: Security concern (CYBV301)
# CYBV301: Security principle
# APCV360: Database principle
# CYBV302: Integration principle
```

**Search TODOs:**

```
Cmd+Shift+F → Search for "TODO:"
```

---

## 🔧 Git Integration (Like JetBrains VCS)

### GitLens Features

1. **Inline Blame**: See who changed each line (toggle: `Cmd+Shift+P` → "GitLens: Toggle Line Blame")
2. **File History**: Right-click file → "Open File History"
3. **Compare**: Right-click → "GitLens: Compare File with..."
4. **Commit Graph**: Click GitLens icon in left sidebar

### Git Graph

1. Click Source Control icon
2. Click "View Git Graph" (top right)
3. Visual branch history (like JetBrains)

### Common Git Operations

| Action            | Shortcut          | Command                 |
| ----------------- | ----------------- | ----------------------- |
| **Stage Changes** | Click +           | Stage selected files    |
| **Commit**        | `Cmd+Enter`       | Type message and commit |
| **Push**          | Click ↑           | Push to remote          |
| **Pull**          | Click ↓           | Pull from remote        |
| **Branch**        | Click branch name | Switch/create branches  |

---

## 🧪 Testing (Like JetBrains Test Runner)

### Test Explorer

1. Click Testing icon in left sidebar (beaker)
2. Shows all discovered tests
3. Click ▶ to run individual tests
4. Click bug icon to debug test
5. Green ✓ = passing, Red ✗ = failing

### Run Tests via Tasks

```
Cmd+Shift+P → "Tasks: Run Task" →
  - 🧪 Run All Tests
  - 🧪 Run Unit Tests
  - 🧪 Run Integration Tests
  - 🔒 Run Security Tests
```

### View Coverage

After running tests with coverage:

```bash
open htmlcov/index.html
```

Or use Coverage Gutters extension (shows coverage in editor).

---

## ⌨️ Keyboard Shortcuts Cheat Sheet

### Essential (Matching JetBrains)

| Action               | Shortcut                  |
| -------------------- | ------------------------- |
| **Command Palette**  | `Cmd+Shift+P`             |
| **Quick Open**       | `Cmd+P`                   |
| **Go to Symbol**     | `Cmd+Shift+O`             |
| **Go to Definition** | `F12`                     |
| **Find References**  | `Shift+F12`               |
| **Rename**           | `F2`                      |
| **Format Document**  | `Shift+Alt+F`             |
| **Toggle Terminal**  | `` Ctrl+` ``              |
| **Toggle Sidebar**   | `Cmd+B`                   |
| **Toggle Problems**  | `Cmd+Shift+M`             |
| **Run Task**         | `Cmd+Shift+P` then "Task" |
| **Start Debugging**  | `F5`                      |
| **Run Build Task**   | `Cmd+Shift+B`             |

### Navigation

| Action                 | Shortcut       |
| ---------------------- | -------------- |
| **Next Error**         | `F8`           |
| **Previous Error**     | `Shift+F8`     |
| **Toggle Breadcrumbs** | `Cmd+Shift+.`  |
| **Focus Explorer**     | `Cmd+Shift+E`  |
| **Focus Search**       | `Cmd+Shift+F`  |
| **Focus Git**          | `Ctrl+Shift+G` |
| **Focus Debug**        | `Cmd+Shift+D`  |
| **Focus Extensions**   | `Cmd+Shift+X`  |

---

## 🎨 Customization

### Theme (JetBrains-like)

**Dark Theme** (Current):

```
File → Preferences → Theme → Color Theme → "Default Dark Modern"
```

**JetBrains Darcula** (Optional):

1. Install "JetBrains IDE Darcula Theme" extension
2. Select it in Color Theme

### Font (JetBrains Mono)

Already configured in settings.json:

```json
"editor.fontFamily": "JetBrains Mono, Menlo, Monaco"
```

If JetBrains Mono not installed:

```bash
brew tap homebrew/cask-fonts
brew install font-jetbrains-mono
```

Then restart VS Code.

### File Icons

Switch to Material Icon Theme:

```
File → Preferences → File Icon Theme → "Material Icon Theme"
```

---

## 🔌 Extensions Management

### Viewing Installed Extensions

```
Cmd+Shift+X → Shows all extensions
```

### Recommended Extensions Status

Check `.vscode/extensions.json` for full list.

**Categories:**

- **Python Development** (7 extensions)
- **Git & GitHub** (7 extensions)
- **Database** (3 extensions)
- **Code Quality** (4 extensions)
- **Productivity** (10+ extensions)

### Disable Unwanted Extensions

```
Right-click extension → "Disable (Workspace)"
```

---

## 📊 Panels & Views Layout

### Recommended Layout (JetBrains-style)

```
┌─────────────────────────────────────────────────────────┐
│  File  Edit  Selection  View  ...         [Breadcrumbs] │
├────────┬────────────────────────────────────────────────┤
│        │                                                 │
│ Exp    │          Editor Area                           │
│ lor    │          (Code)                                │
│ er     │                                                 │
│        │                                                 │
│────────┤                                                 │
│ TODO   │                                                 │
│ Tree   │                                                 │
│        │                                                 │
│────────┤                                                 │
│ Git    │                                                 │
│ Lens   ├─────────────────────────────────────────────────┤
│        │  Terminal / Problems / Output / Debug Console  │
└────────┴─────────────────────────────────────────────────┘
```

**Toggle Panels:**

- `Cmd+B` - Toggle sidebar
- `` Ctrl+` `` - Toggle terminal
- `Cmd+Shift+M` - Toggle problems
- `Cmd+J` - Toggle panel

---

## 🔄 Synchronization

### Settings Sync (Like JetBrains Settings Sync)

Enable to sync settings, extensions, keybindings across devices:

```
File → Preferences → Settings Sync
→ Sign in with GitHub
→ Enable Settings Sync
```

**Syncs:**

- Settings
- Extensions
- Keybindings
- Snippets
- UI State

---

## 📝 Snippets (Like JetBrains Live Templates)

### Using Snippets

Type prefix and press `Tab`:

```python
# Type: def
def function_name():
    """Docstring"""
    pass

# Type: class
class ClassName:
    """Docstring"""
    def __init__(self):
        pass

# Type: if
if condition:
    pass

# Type: for
for item in iterable:
    pass
```

### Creating Custom Snippets

```
File → Preferences → Configure User Snippets → python.json
```

---

## 🐛 Troubleshooting

### Python Extension Not Working

1. Reload window: `Cmd+Shift+P` → "Developer: Reload Window"
2. Check interpreter: `Cmd+Shift+P` → "Python: Select Interpreter"
3. Reinstall Python extension

### Tests Not Discovered

1. Ensure pytest installed: `pip install pytest`
2. Reload tests: Click refresh in Test Explorer
3. Check `python.testing.pytestEnabled` in settings

### Git Graph Not Showing

1. Ensure repository has commits
2. Click "View Git Graph" in Source Control
3. Install Git Graph extension if missing

### Database Connection Failed

1. Check database path in `.vscode/settings.json`
2. Ensure database file exists
3. Reconnect in SQLTools

---

## 📚 Learning Resources

### VS Code Docs

- [Python in VS Code](https://code.visualstudio.com/docs/languages/python)
- [Debugging](https://code.visualstudio.com/docs/editor/debugging)
- [Tasks](https://code.visualstudio.com/docs/editor/tasks)

### JetBrains to VS Code Migration

- [IntelliJ IDEA Keymap](https://marketplace.visualstudio.com/items?itemName=k--kato.intellij-idea-keybindings)
- [PyCharm Keymap](https://marketplace.visualstudio.com/items?itemName=alois.vscode-pycharm-keybindings)

---

## 💡 Pro Tips

1. **Multi-cursor editing**: `Alt+Click` to add cursors
2. **Column selection**: `Shift+Alt+Drag`
3. **Duplicate line**: `Shift+Alt+Down`
4. **Move line**: `Alt+Up/Down`
5. **Comment**: `Cmd+/`
6. **Block comment**: `Shift+Alt+A`
7. **Format selection**: `Cmd+K, Cmd+F`
8. **Zen mode**: `Cmd+K, Z` (distraction-free)
9. **Split editor**: `Cmd+\`
10. **Sticky scroll**: Shows current function at top

---

**Last Updated**: December 2, 2024  
**Maintained by**: Tevin Fowler  
**Questions?**: Check QUICK_REFERENCE.md or ask GitHub Copilot Chat
