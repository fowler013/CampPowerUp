# 🎨 Oh My Zsh Terminal Customization Guide

## ✅ What's Installed

### Core Components
- **Oh My Zsh** - Framework for managing Zsh configuration
- **Powerlevel10k** - Modern, fast theme with icons and git info
- **zsh-autosuggestions** - Fish-like autosuggestions as you type
- **zsh-syntax-highlighting** - Syntax highlighting for commands

### Plugins Enabled
- `git` - Git aliases and functions
- `docker` - Docker completions
- `python` - Python completions
- `pip` - Pip completions
- `brew` - Homebrew completions
- `macos` - macOS-specific commands
- `vscode` - VS Code integration
- `gh` - GitHub CLI completions
- `colored-man-pages` - Colorized man pages
- `copypath` - Copy current path
- `copyfile` - Copy file contents
- `web-search` - Search from terminal
- `jsontools` - JSON tools

---

## 🎯 CampPowerUp Custom Commands

### 📂 Project Navigation
```bash
camp          # cd to CampPowerUp directory
devcamp       # Open development workspace
prodcamp      # Open production workspace
```

### 🔀 Git Shortcuts
```bash
gs            # git status
ga            # git add
gc "message"  # git commit -m "message"
gp            # git push
gpl           # git pull
gco branch    # git checkout branch
gcb branch    # git checkout -b branch
gb            # git branch
glog          # pretty git log graph
```

### 🌿 Branch Management Functions
```bash
feature my-feature    # Create feature/my-feature from develop
bugfix my-bug         # Create bugfix/my-bug from develop
qc "quick commit"     # Add all, commit, and push in one command
```

### 🎯 GitHub CLI
```bash
prs            # List all PRs
prview         # View current PR
prcreate       # Create new PR
prmerge        # Merge PR
issues         # List issues
pr-dev         # Create PR to develop branch
pr-main        # Create PR to main branch
```

### 📊 Project Management
```bash
project                    # Interactive project manager
project-overview           # Quick project overview
./scripts/project-manager.sh status 14 done    # Update PR status
```

### 🐍 Python/Flask
```bash
venv           # Activate virtual environment
dev            # Start Flask development server
runapp         # python app.py
test           # Run pytest
testall        # Run tests with coverage report
testcov        # Run tests with HTML coverage
lint           # Run pylint on src/
format         # Format code with black + isort
quality        # Run ALL quality checks (black, isort, pylint, mypy, bandit)
```

### 💾 Database
```bash
dbbackup       # Backup database
dbrestore      # Restore database
dbmaintain     # Run database maintenance
```

### 🐳 Docker (Future)
```bash
dc             # docker-compose
dcu            # docker-compose up
dcd            # docker-compose down
dcl            # docker-compose logs
```

---

## 🎨 Customizing Powerlevel10k

### First Time Setup
When you open a new terminal, Powerlevel10k will guide you through configuration:

```bash
p10k configure
```

**Configuration options:**
1. Choose prompt style (lean, classic, rainbow, etc.)
2. Enable/disable git status
3. Enable/disable command execution time
4. Choose prompt colors
5. Enable/disable icons

### Recommended Settings
- **Style**: Lean or Classic
- **Git**: Yes (show branch, status)
- **Icons**: Yes (if you have a Nerd Font installed)
- **Time**: Yes (show command execution time)
- **Transient Prompt**: Yes (clean history)

### Manual Configuration
Edit `~/.p10k.zsh` to customize:
```bash
code ~/.p10k.zsh
```

---

## 🔧 Plugin Features

### Git Plugin
```bash
gaa            # git add --all
gcam "msg"     # git commit -a -m "msg"
gd             # git diff
gf             # git fetch
gm             # git merge
grb            # git rebase
```

### Web Search Plugin
```bash
google search term       # Google search
github project name      # GitHub search
stackoverflow question   # Stack Overflow search
```

### Copypath/Copyfile
```bash
copypath       # Copy current directory path to clipboard
copyfile file  # Copy file contents to clipboard
```

---

## 📝 Customizing Your Terminal

### Add More Aliases
Edit `~/.zshrc`:
```bash
code ~/.zshrc
```

Add at the bottom:
```bash
# My custom aliases
alias mycommand="some command"
```

Then reload:
```bash
source ~/.zshrc
# OR
exec zsh
```

### Add More Plugins
Available plugins: https://github.com/ohmyzsh/ohmyzsh/wiki/Plugins

To add a plugin:
1. Edit `~/.zshrc`
2. Add plugin name to `plugins=(...)` array
3. Run `source ~/.zshrc`

Popular additions:
- `z` - Jump to frequently used directories
- `history` - History search with arrow keys
- `sudo` - Press ESC twice to add sudo
- `extract` - Universal extract command
- `npm` - NPM completions

### Change Theme
Edit `~/.zshrc` and change:
```bash
ZSH_THEME="powerlevel10k/powerlevel10k"
```

Other popular themes:
- `robbyrussell` (default)
- `agnoster`
- `spaceship`
- `pure`

---

## 💡 Pro Tips

### 1. Command History Search
Press `Ctrl+R` and start typing to search history

### 2. Auto-suggestions
As you type, you'll see gray suggestions. Press `→` to accept

### 3. Syntax Highlighting
Valid commands = green
Invalid commands = red

### 4. Tab Completion
Hit `Tab` for smart completions on almost everything

### 5. Git Status in Prompt
Your prompt shows:
- Current branch name
- Uncommitted changes (✗)
- Staged files (✚)
- Behind/ahead commits (⇣⇡)

### 6. Quick Directory Navigation
```bash
cd -           # Go to previous directory
cd ../..       # Go up two levels
..             # cd ..
...            # cd ../..
....           # cd ../../..
```

### 7. Global Aliases
```bash
alias -g G='| grep'        # ls G pattern
alias -g L='| less'        # cat file L
alias -g H='| head'        # cat file H
alias -g T='| tail'        # cat file T
```

---

## 🎨 Terminal Appearance

### Install Nerd Fonts (for icons)
```bash
brew tap homebrew/cask-fonts
brew install --cask font-meslo-lg-nerd-font
```

Then set your terminal font to "MesloLGS NF"

### Color Schemes
- VS Code: Already using JetBrains Mono
- Terminal: Configure in Terminal.app preferences
- iTerm2 (recommended): https://iterm2colorschemes.com/

---

## 🚀 Quick Start Cheat Sheet

### First Day Workflow
```bash
# Navigate to project
camp

# Activate Python environment
venv

# Start new feature
feature user-authentication

# Make changes, then quick commit
qc "feat: add user authentication"

# Create PR to develop
pr-dev

# Check project status
project-overview
```

### Code Quality Workflow
```bash
# Before committing
format         # Format code
lint           # Check for issues
testall        # Run tests with coverage
quality        # Run everything

# If all good
qc "feat: implement new feature with tests"
```

### Database Workflow
```bash
# Daily backup
dbbackup

# After changes, maintenance
dbmaintain

# If something goes wrong
dbrestore
```

---

## 📚 Learning More

### Oh My Zsh
- Wiki: https://github.com/ohmyzsh/ohmyzsh/wiki
- Cheatsheet: https://github.com/ohmyzsh/ohmyzsh/wiki/Cheatsheet

### Powerlevel10k
- Docs: https://github.com/romkatv/powerlevel10k
- Configuration: `p10k configure`

### Zsh
- User Guide: https://zsh.sourceforge.io/Guide/
- Tips: https://scriptingosx.com/zsh/

---

## 🔧 Troubleshooting

### Icons Not Showing
Install a Nerd Font and configure your terminal to use it.

### Slow Prompt
Run `p10k configure` and choose faster options.

### Plugin Not Working
```bash
# Check if plugin exists
ls ~/.oh-my-zsh/plugins/

# Reload configuration
source ~/.zshrc
```

### Reset Configuration
```bash
# Backup current config
cp ~/.zshrc ~/.zshrc.backup

# Re-run Oh My Zsh installer
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
```

---

**Last Updated:** December 3, 2025  
**Status:** ✅ Fully Configured and Ready to Use!

Type `alias` in your terminal to see all available shortcuts!
