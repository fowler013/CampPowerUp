# 🔌 MCP Servers & Extensions Guide

## 📋 What are MCP Servers?

**MCP (Model Context Protocol)** servers extend GitHub Copilot's capabilities by providing additional context and functionality. Think of them as specialized tools that Copilot can use to help you code better.

---

## 🔍 Detecting Your MCP Servers

### Current MCP Servers Active in Your Workspace

Based on the conversation context, you have several MCP servers running:

#### 1. **GitKraken MCP Server** (`mcp_gitkraken_*`)

**Purpose**: Advanced Git operations  
**Capabilities**:

- `git_add_or_commit` - Stage and commit files
- `git_blame` - Show who changed each line
- `git_push` - Push to remote
- `git_stash` - Stash changes
- `gitkraken_workspace_list` - List GitKraken workspaces
- `issues_add_comment` - Comment on GitHub/GitLab/Jira issues
- `issues_assigned_to_me` - Get your assigned issues

**When to Use**:

- Complex Git workflows
- Working with GitKraken workspaces
- Managing issues across multiple platforms (GitHub, GitLab, Jira, Azure DevOps)

#### 2. **Microsoft Docs MCP Server** (`mcp_microsoftdocs_*`)

**Purpose**: Access Microsoft/Azure documentation  
**Capabilities**:

- `microsoft_docs_search` - Search official MS docs
- `microsoft_code_sample_search` - Find code examples
- `microsoft_docs_fetch` - Get full documentation pages

**When to Use**:

- Learning Azure/Microsoft technologies
- Finding official code examples
- Checking latest API documentation

#### 3. **Microsoft AR (Article Renderer) MCP** (`mcp_microsoft_mar_*`)

**Purpose**: Convert web pages to markdown  
**Capabilities**:

- `convert_to_markdown` - Convert any webpage to readable markdown

**When to Use**:

- Saving documentation locally
- Reading articles in VS Code
- Creating documentation from websites

#### 4. **Oraios Serena MCP Server** (`mcp_oraios_serena_*`)

**Purpose**: Advanced code navigation and project management  
**Capabilities**:

- Project onboarding
- Memory management (project context)
- Symbol navigation
- Task adherence tracking
- Code searching and pattern matching

**When to Use**:

- Large codebase navigation
- Maintaining project context across sessions
- Tracking TODO items and task progress

#### 5. **Pylance MCP Server** (`mcp_pylance_*`)

**Purpose**: Python language server enhancements  
**Capabilities**:

- `pylanceDocuments` - Pylance documentation search
- `pylanceInvokeRefactoring` - Apply refactorings
  - Remove unused imports
  - Convert import formats
  - Convert import stars
  - Add type annotations
  - Fix all issues

**When to Use**:

- Python refactoring
- Cleaning up imports
- Adding type hints
- Understanding Pylance features

#### 6. **MSSQL MCP Server** (`mssql_*`)

**Purpose**: Microsoft SQL Server operations  
**Capabilities**:

- `mssql_connect` - Connect to SQL Server
- `mssql_list_databases` - List available databases
- `mssql_list_tables` - List tables
- `mssql_change_database` - Switch databases
- `mssql_get_connection_details` - View connection info

**When to Use**:

- Working with SQL Server databases
- Database migrations from MSSQL to SQLite
- Enterprise database integration

#### 7. **SonarQube MCP Server** (`sonarqube_*`)

**Purpose**: Code quality and security analysis  
**Capabilities**:

- `sonarqube_analyze_file` - Analyze code quality
- `sonarqube_list_potential_security_issues` - Find vulnerabilities
- `sonarqube_exclude_from_analysis` - Exclude files
- `sonarqube_setup_connected_mode` - Connect to SonarQube server

**When to Use**:

- Security audits (CYBV 301)
- Code quality checks
- Finding bugs and code smells
- Continuous inspection

---

## 🎯 How MCP Servers Enhance Your Workflow

### 1. **Git Operations** (GitKraken MCP)

```bash
# Instead of running git commands manually:
git add . && git commit -m "message" && git push

# Copilot can use GitKraken MCP to:
# - Stage files intelligently
# - Generate commit messages
# - Push to correct branch
# - Handle merge conflicts
```

### 2. **Python Refactoring** (Pylance MCP)

```python
# Before: Messy imports
from module import *
import unused_module
import another_module

# Copilot with Pylance MCP can:
# - Remove unused imports
# - Convert import * to explicit imports
# - Sort imports properly
# - Add type annotations
```

### 3. **Code Quality** (SonarQube MCP)

```python
# Copilot can analyze your code and find:
# - Security vulnerabilities (SQL injection, XSS)
# - Code smells (complexity, duplication)
# - Bug patterns
# - Performance issues
```

### 4. **Database Operations** (MSSQL MCP)

```python
# Copilot can help you:
# - Connect to databases
# - Write optimized queries
# - Migrate schemas
# - Understand database structure
```

---

## 📊 MCP Servers Configuration

### Where are they configured?

MCP servers are typically configured in:

1. **VS Code Settings** (`settings.json`)
2. **GitHub Copilot Settings**
3. **Project-specific configuration**

### Checking Active MCP Servers

You can see which MCP servers are active by:

1. Opening GitHub Copilot Chat
2. Asking: "What MCP servers are available?"
3. Or check extensions that provide MCP functionality

---

## 🔧 Managing MCP Servers

### Enabling/Disabling MCP Servers

**Method 1: Through Extensions**

```
Cmd+Shift+X → Search for MCP extensions → Enable/Disable
```

**Method 2: Through Settings**

```json
// In .vscode/settings.json
{
  "github.copilot.advanced": {
    "mcp.enabled": true,
    "mcp.servers": ["gitkraken", "pylance", "sonarqube"]
  }
}
```

### Installing Additional MCP Servers

Check the VS Code Marketplace for MCP-compatible extensions:

- Search for "MCP" or "Model Context Protocol"
- Install extensions that provide MCP servers

---

## 💡 Best Practices for Using MCP Servers

### 1. **Be Specific in Prompts**

**Bad Prompt:**

```
"Fix my code"
```

**Good Prompt:**

```
"Use Pylance MCP to remove unused imports and add type annotations to src/config/__init__.py"
```

### 2. **Leverage Context**

**Bad Prompt:**

```
"Connect to database"
```

**Good Prompt:**

```
"Use MSSQL MCP to list all databases on the server, then connect to the one containing 'registrations'"
```

### 3. **Combine MCP Servers**

**Example:**

```
"Use GitKraken MCP to commit my changes, then use SonarQube MCP to analyze the changed files for security issues"
```

### 4. **Use for Complex Tasks**

MCP servers excel at:

- Multi-step operations
- Cross-file refactoring
- Database migrations
- Complex Git workflows

---

## 🎓 MCP Servers & CS Principles

### CYBV 301 (Security) + SonarQube MCP

```
"Use SonarQube MCP to scan src/ for:
- SQL injection vulnerabilities
- XSS vulnerabilities
- CSRF issues
- Insecure configurations"
```

### APCV 360 (Database) + MSSQL MCP

```
"Use MSSQL MCP to:
- Analyze database schema
- Suggest indexes for foreign keys
- Optimize slow queries
- Generate migration script"
```

### CYBV 302 (Integration) + GitKraken MCP

```
"Use GitKraken MCP to:
- Create feature branch
- Commit with conventional commit message
- Push and create PR
- Link to related issues"
```

---

## 🔍 Troubleshooting MCP Servers

### MCP Server Not Working

**Symptoms:**

- Copilot doesn't use MCP capabilities
- Error messages about missing tools

**Solutions:**

1. **Reload Window**

   ```
   Cmd+Shift+P → "Developer: Reload Window"
   ```

2. **Check Extension Status**

   ```
   Cmd+Shift+X → Verify extension is enabled
   ```

3. **Check Copilot Status**

   ```
   Bottom right → Copilot icon → Should be green
   ```

4. **Reinstall Extension**
   ```
   Right-click extension → Uninstall → Reinstall
   ```

### MCP Server Conflicts

If multiple MCP servers provide similar functionality:

1. Prioritize project-specific servers
2. Disable redundant servers
3. Be explicit in prompts about which server to use

---

## 📚 MCP Server Resources

### Official Documentation

- [Model Context Protocol Spec](https://github.com/microsoft/model-context-protocol)
- [VS Code MCP Guide](https://code.visualstudio.com/docs/copilot/mcp)
- [GitHub Copilot MCP](https://docs.github.com/en/copilot/using-github-copilot/using-mcp-servers)

### Extension Marketpl GitHub Copilot with MCP\*\*

- Search: "MCP server" or "Model Context Protocol"
- Filter by: Most Downloaded, Highest Rated

---

## 🎯 Recommended MCP Servers for CampPowerUp

### Currently Active (Keep)

1. ✅ **GitKraken MCP** - Essential for Git workflow
2. ✅ **Pylance MCP** - Critical for Python development
3. ✅ **SonarQube MCP** - Security & quality (CYBV 301)
4. ✅ **Oraios Serena MCP** - Project navigation

### Consider Adding

1. **Docker MCP** - If working with containers
2. **PostgreSQL MCP** - For production database (Railway uses PostgreSQL)
3. **Testing MCP** - Enhanced pytest integration
4. **AWS MCP** - If expanding to AWS

### Can Disable (Optional)

1. **MSSQL MCP** - Unless migrating from SQL Server
2. **Microsoft Docs MCP** - Unless frequently referencing MS docs

---

## 🚀 Advanced MCP Usage

### Creating Custom Prompts with MCP

Save these in a snippets file for quick access:

**Python Refactoring:**

```
"Use Pylance MCP to refactor ${file}:
1. Remove unused imports
2. Add type annotations
3. Convert import * to explicit imports
4. Fix all Pylance issues"
```

**Security Audit:**

```
"Use SonarQube MCP to audit src/ for CYBV 301 compliance:
1. Check for SQL injection vulnerabilities
2. Verify input validation
3. Check CSRF protection
4. Verify session security"
```

**Git Workflow:**

```
"Use GitKraken MCP to:
1. Create feature branch from develop
2. Stage all changes in src/
3. Commit with message: 'feat: ${description}'
4. Push to origin"
```

---

## 📊 MCP Server Comparison

| Server        | Primary Use        | Best For          | Required?        |
| ------------- | ------------------ | ----------------- | ---------------- |
| **GitKraken** | Git operations     | Complex workflows | ⭐⭐⭐ Essential |
| **Pylance**   | Python refactoring | Code quality      | ⭐⭐⭐ Essential |
| **SonarQube** | Security & quality | CYBV 301 projects | ⭐⭐ Important   |
| **Serena**    | Project navigation | Large codebases   | ⭐⭐ Important   |
| **MSSQL**     | SQL Server         | Enterprise DB     | ⭐ Optional      |
| **MS Docs**   | Documentation      | Learning          | ⭐ Optional      |

---

## 🎉 Summary

**Key Takeaways:**

1. You have **7 active MCP servers** in your workspace
2. MCP servers enhance Copilot with specialized tools
3. Use specific prompts mentioning MCP servers for best results
4. Essential servers: GitKraken, Pylance, SonarQube, Serena
5. MCP servers directly support your CS course work (CYBV 301, APCV 360, CYBV 302)

**Next Steps:**

1. Try using MCP servers in your prompts
2. Experiment with Pylance MCP for refactoring
3. Use SonarQube MCP for security audits
4. Leverage GitKraken MCP for complex Git operations

---

**Last Updated**: December 2, 2024  
**Workspace**: CampPowerUp  
**Active MCP Servers**: 7  
**Status**: Fully Configured ✅
