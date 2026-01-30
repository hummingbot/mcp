# @hummingbot/skills

CLI tool to discover and install Hummingbot trading skills for AI agents.

```bash
npx @hummingbot/skills add
```

## What are Hummingbot Skills?

Skills are reusable instruction sets that extend AI agent capabilities for algorithmic trading. Instead of loading thousands of tokens of MCP tool definitions, skills load on-demand when relevant to the user's task.

**Context efficiency:**
- Skill metadata at startup: ~100 tokens per skill
- Full skill on activation: <5,000 tokens
- Compare to MCP tools: ~20,000+ tokens always loaded

## Installation

No installation required! Use directly with npx:

```bash
npx @hummingbot/skills add
```

Or install globally:

```bash
npm install -g @hummingbot/skills
hb-skills add
```

## Commands

### Add Skills

Install Hummingbot skills to your AI agent:

```bash
# Install all skills
npx @hummingbot/skills add

# Install specific skill
npx @hummingbot/skills add -s executors

# Install globally (user directory)
npx @hummingbot/skills add -g

# Install to specific agent
npx @hummingbot/skills add -a cursor

# List available skills without installing
npx @hummingbot/skills add -l
```

### List Installed Skills

```bash
npx @hummingbot/skills list
# or
npx @hummingbot/skills ls
```

### Search Skills

```bash
# Search all skills
npx @hummingbot/skills find

# Search by keyword
npx @hummingbot/skills find trading
npx @hummingbot/skills find "api key"
```

### Remove Skills

```bash
npx @hummingbot/skills remove executors
npx @hummingbot/skills rm executors candles
```

### Check API Server

Verify your Hummingbot API server is running:

```bash
npx @hummingbot/skills check
```

### Create Custom Skill

Generate a skill template:

```bash
npx @hummingbot/skills init my-custom-skill
```

## Available Skills

| Skill | Description |
|-------|-------------|
| `setup` | Deploy Hummingbot infrastructure (Docker, API server, Gateway) |
| `keys` | Manage exchange API credentials |
| `executors` | Create and manage trading executors (position, grid, DCA, TWAP) |
| `candles` | Market data and technical indicators (RSI, EMA, MACD) |

## Supported Agents

- Claude Code
- Cursor
- VS Code (GitHub Copilot)
- OpenCode
- OpenAI Codex
- Goose
- Gemini CLI
- And 25+ more...

## Options

| Flag | Description |
|------|-------------|
| `-g, --global` | Install to user directory (default: project) |
| `-a, --agent <name>` | Target specific agent |
| `-s, --skill <name>` | Install specific skill only |
| `-l, --list` | List available skills |
| `-y, --yes` | Skip confirmation prompts |
| `-h, --help` | Show help |
| `-v, --version` | Show version |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_URL` | `http://localhost:8000` | Hummingbot API server URL |
| `API_USER` | `admin` | API authentication username |
| `API_PASS` | `admin` | API authentication password |

## How It Works

1. **Discovery**: CLI detects installed AI agents (Claude Code, Cursor, etc.)
2. **Installation**: Skills are copied to agent-specific directories
3. **Activation**: When you ask about trading, your agent reads the relevant SKILL.md
4. **Execution**: Agent runs skill scripts that call the Hummingbot API directly

```
User: "Create a BTC position with 2% stop loss"
     ↓
Agent matches "position" → loads executors skill
     ↓
Agent reads: ~/.claude/skills/hummingbot-executors/SKILL.md
     ↓
Agent runs: ./scripts/create_executor.sh --type position_executor ...
     ↓
Script calls: curl -X POST $API_URL/api/v1/executors
     ↓
Executor created!
```

## Publishing to npm

The package is published under the `@hummingbot` npm organization.

### First-Time Setup (Maintainers)

```bash
# Login to the hummingbot npm account
npm login

# Verify you're logged in as hummingbot
npm whoami
# Should output: hummingbot
```

### Publishing

```bash
cd cli

# Verify package name and version
npm pkg get name version
# Should show: "@hummingbot/skills" "1.0.0"

# Run a dry-run to preview what will be published
npm publish --dry-run

# Publish (scoped packages need --access public for first publish)
npm publish --access public
```

### Versioning

```bash
# Patch release (1.0.0 → 1.0.1) - bug fixes
npm version patch

# Minor release (1.0.0 → 1.1.0) - new features
npm version minor

# Major release (1.0.0 → 2.0.0) - breaking changes
npm version major

# Then publish
npm publish
```

### Automated Publishing with GitHub Actions

Add this workflow to `.github/workflows/npm-publish.yml`:

```yaml
name: Publish @hummingbot/skills to npm

on:
  release:
    types: [created]
  workflow_dispatch:
    inputs:
      version:
        description: 'Version bump type'
        required: true
        default: 'patch'
        type: choice
        options:
          - patch
          - minor
          - major

jobs:
  publish:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: cli
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          registry-url: 'https://registry.npmjs.org'

      - name: Bump version (manual trigger only)
        if: github.event_name == 'workflow_dispatch'
        run: npm version ${{ inputs.version }} --no-git-tag-version

      - name: Publish to npm
        run: npm publish --access public
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

**Setup:**
1. Generate npm token: https://www.npmjs.com/settings/hummingbot/tokens
2. Add `NPM_TOKEN` to repo secrets: Settings → Secrets → Actions
3. Trigger via GitHub Releases or manual workflow dispatch

## Development

```bash
# Clone repository
git clone https://github.com/hummingbot/mcp.git
cd mcp/cli

# Run locally
node bin/cli.mjs --help

# Test commands
node bin/cli.mjs add -l
node bin/cli.mjs check
```

## License

Apache-2.0

## Links

- [Hummingbot](https://hummingbot.org)
- [GitHub Repository](https://github.com/hummingbot/mcp)
- [Agent Skills Specification](https://agentskills.io)
