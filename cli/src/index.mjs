/**
 * hummingbot-skills CLI - Core functionality
 */

import { existsSync, mkdirSync, readFileSync, writeFileSync, readdirSync, rmSync, symlinkSync, statSync } from 'fs';
import { join, dirname, basename } from 'path';
import { homedir } from 'os';
import { execSync, spawnSync } from 'child_process';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Package version
const VERSION = '1.0.0';

// Hummingbot skills registry
const SKILLS_REGISTRY = {
  setup: {
    name: 'hummingbot-setup',
    description: 'Deploy and configure Hummingbot infrastructure (Docker, API server, Gateway)',
    category: 'infrastructure',
    triggers: ['install hummingbot', 'setup trading', 'deploy api', 'docker setup'],
  },
  keys: {
    name: 'hummingbot-keys',
    description: 'Manage exchange API credentials (add, remove, verify keys)',
    category: 'configuration',
    triggers: ['add api key', 'configure exchange', 'setup binance', 'add credentials'],
  },
  executors: {
    name: 'hummingbot-executors',
    description: 'Create and manage trading executors (position, grid, DCA, TWAP)',
    category: 'trading',
    triggers: ['create executor', 'position executor', 'grid trading', 'dca order', 'start trading'],
  },
  candles: {
    name: 'hummingbot-candles',
    description: 'Market data and technical indicators (RSI, EMA, MACD, Bollinger Bands)',
    category: 'data',
    triggers: ['get candles', 'calculate rsi', 'market data', 'technical analysis'],
  },
};

// Supported AI agents and their skill directories
const AGENTS = {
  'claude-code': {
    name: 'Claude Code',
    projectPath: '.claude/skills',
    globalPath: join(homedir(), '.claude', 'skills'),
  },
  'cursor': {
    name: 'Cursor',
    projectPath: '.cursor/skills',
    globalPath: join(homedir(), '.cursor', 'skills'),
  },
  'vscode': {
    name: 'VS Code (Copilot)',
    projectPath: '.github/skills',
    globalPath: join(homedir(), '.vscode', 'skills'),
  },
  'opencode': {
    name: 'OpenCode',
    projectPath: '.opencode/skills',
    globalPath: join(homedir(), '.opencode', 'skills'),
  },
  'codex': {
    name: 'OpenAI Codex',
    projectPath: '.codex/skills',
    globalPath: join(homedir(), '.codex', 'skills'),
  },
  'goose': {
    name: 'Goose',
    projectPath: '.goose/skills',
    globalPath: join(homedir(), '.goose', 'skills'),
  },
  'gemini-cli': {
    name: 'Gemini CLI',
    projectPath: '.gemini/skills',
    globalPath: join(homedir(), '.gemini', 'skills'),
  },
};

// Colors for terminal output
const colors = {
  reset: '\x1b[0m',
  bold: '\x1b[1m',
  dim: '\x1b[2m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
  red: '\x1b[31m',
};

function c(color, text) {
  return `${colors[color]}${text}${colors.reset}`;
}

/**
 * Print version
 */
export function printVersion() {
  console.log(`hummingbot-skills v${VERSION}`);
}

/**
 * Print help message
 */
export function printHelp() {
  console.log(`
${c('bold', 'hummingbot-skills')} - Install Hummingbot trading skills for AI agents

${c('yellow', 'USAGE')}
  npx hummingbot-skills <command> [options]

${c('yellow', 'COMMANDS')}
  ${c('cyan', 'add')}              Install Hummingbot skills to your agent
  ${c('cyan', 'list')} (ls)        List installed skills
  ${c('cyan', 'find')} [query]     Search available skills
  ${c('cyan', 'remove')} (rm)      Remove installed skills
  ${c('cyan', 'check')}            Check Hummingbot API server status
  ${c('cyan', 'init')} [name]      Create a new custom skill template

${c('yellow', 'OPTIONS')}
  -g, --global        Install to user directory (default: project)
  -a, --agent <name>  Target specific agent (claude-code, cursor, vscode, etc.)
  -s, --skill <name>  Install specific skill only (setup, keys, executors, candles)
  -l, --list          List available skills without installing
  -y, --yes           Skip confirmation prompts
  -h, --help          Show this help message
  -v, --version       Show version number

${c('yellow', 'EXAMPLES')}
  ${c('dim', '# Install all Hummingbot skills to Claude Code')}
  npx hummingbot-skills add

  ${c('dim', '# Install only the executors skill globally')}
  npx hummingbot-skills add -g -s executors

  ${c('dim', '# Install to Cursor specifically')}
  npx hummingbot-skills add -a cursor

  ${c('dim', '# List available skills')}
  npx hummingbot-skills add -l

  ${c('dim', '# Search for trading-related skills')}
  npx hummingbot-skills find trading

  ${c('dim', '# Check if API server is running')}
  npx hummingbot-skills check

${c('yellow', 'AVAILABLE SKILLS')}
  ${c('green', 'setup')}       Deploy Hummingbot infrastructure
  ${c('green', 'keys')}        Manage exchange API credentials
  ${c('green', 'executors')}   Create and manage trading executors
  ${c('green', 'candles')}     Market data and technical indicators

${c('yellow', 'LEARN MORE')}
  GitHub: https://github.com/hummingbot/mcp
  Docs:   https://hummingbot.org/mcp
`);
}

/**
 * Detect installed AI agents
 */
function detectAgents() {
  const detected = [];

  for (const [id, agent] of Object.entries(AGENTS)) {
    // Check if global directory exists
    if (existsSync(dirname(agent.globalPath))) {
      detected.push({ id, ...agent, scope: 'global' });
    }
    // Check if project directory exists
    if (existsSync(agent.projectPath) || existsSync(dirname(agent.projectPath))) {
      detected.push({ id, ...agent, scope: 'project' });
    }
  }

  // Default to claude-code if nothing detected
  if (detected.length === 0) {
    detected.push({ id: 'claude-code', ...AGENTS['claude-code'], scope: 'project' });
  }

  return detected;
}

/**
 * Get the skills source directory (bundled with package or cloned repo)
 */
function getSkillsSourceDir() {
  // Check if running from the mcp repo directly
  const repoSkillsDir = join(__dirname, '..', '..', 'skills');
  if (existsSync(repoSkillsDir)) {
    return repoSkillsDir;
  }

  // Check for bundled skills in package
  const bundledDir = join(__dirname, '..', 'skills');
  if (existsSync(bundledDir)) {
    return bundledDir;
  }

  // Fall back to cloning from GitHub
  return null;
}

/**
 * Clone skills from GitHub if not available locally
 */
async function ensureSkillsAvailable() {
  let skillsDir = getSkillsSourceDir();

  if (skillsDir) {
    return skillsDir;
  }

  // Need to clone from GitHub
  const tempDir = join(homedir(), '.cache', 'hummingbot-skills');
  const cloneDir = join(tempDir, 'mcp');

  if (!existsSync(cloneDir)) {
    console.log(c('dim', 'Fetching Hummingbot skills from GitHub...'));
    mkdirSync(tempDir, { recursive: true });

    try {
      execSync(`git clone --depth 1 https://github.com/hummingbot/mcp.git "${cloneDir}"`, {
        stdio: 'pipe',
      });
    } catch (error) {
      throw new Error('Failed to clone Hummingbot skills repository. Please check your internet connection.');
    }
  }

  return join(cloneDir, 'skills');
}

/**
 * Install skills to agent directory
 */
async function installSkill(skillId, targetDir, sourceDir) {
  const skillSourcePath = join(sourceDir, skillId);

  if (!existsSync(skillSourcePath)) {
    throw new Error(`Skill "${skillId}" not found in source directory`);
  }

  const skillTargetPath = join(targetDir, `hummingbot-${skillId}`);

  // Create target directory
  mkdirSync(dirname(skillTargetPath), { recursive: true });

  // Remove existing if present
  if (existsSync(skillTargetPath)) {
    rmSync(skillTargetPath, { recursive: true });
  }

  // Copy skill directory
  copyDirectory(skillSourcePath, skillTargetPath);

  return skillTargetPath;
}

/**
 * Recursively copy directory
 */
function copyDirectory(src, dest) {
  mkdirSync(dest, { recursive: true });

  const entries = readdirSync(src, { withFileTypes: true });

  for (const entry of entries) {
    const srcPath = join(src, entry.name);
    const destPath = join(dest, entry.name);

    if (entry.isDirectory()) {
      copyDirectory(srcPath, destPath);
    } else {
      const content = readFileSync(srcPath);
      writeFileSync(destPath, content);
    }
  }
}

/**
 * Run add command - install skills
 */
export async function runAdd(flags) {
  console.log(`\n${c('bold', '🤖 Hummingbot Skills Installer')}\n`);

  // List mode
  if (flags.list) {
    console.log(c('yellow', 'Available Hummingbot Skills:\n'));
    for (const [id, skill] of Object.entries(SKILLS_REGISTRY)) {
      console.log(`  ${c('green', id.padEnd(12))} ${skill.description}`);
    }
    console.log(`\n${c('dim', 'Run "npx hummingbot-skills add" to install all skills.')}`);
    return;
  }

  // Get skills source
  const skillsSourceDir = await ensureSkillsAvailable();
  console.log(c('dim', `Skills source: ${skillsSourceDir}`));

  // Determine which skills to install
  let skillsToInstall = Object.keys(SKILLS_REGISTRY);
  if (flags.skill) {
    if (!SKILLS_REGISTRY[flags.skill]) {
      console.error(c('red', `Unknown skill: ${flags.skill}`));
      console.log(`Available skills: ${Object.keys(SKILLS_REGISTRY).join(', ')}`);
      process.exit(1);
    }
    skillsToInstall = [flags.skill];
  }

  // Determine target agents
  let agents = detectAgents();
  if (flags.agent) {
    if (!AGENTS[flags.agent]) {
      console.error(c('red', `Unknown agent: ${flags.agent}`));
      console.log(`Supported agents: ${Object.keys(AGENTS).join(', ')}`);
      process.exit(1);
    }
    agents = [{ id: flags.agent, ...AGENTS[flags.agent] }];
  }

  // Filter by scope
  const scope = flags.global ? 'global' : 'project';

  console.log(`\n${c('yellow', 'Installation Plan:')}`);
  console.log(`  Skills: ${c('cyan', skillsToInstall.join(', '))}`);
  console.log(`  Scope:  ${c('cyan', scope)}`);
  console.log(`  Agents: ${c('cyan', agents.map(a => a.name).join(', '))}`);

  // Confirm unless -y flag
  if (!flags.yes) {
    console.log(`\n${c('dim', 'Press Ctrl+C to cancel, or wait 3 seconds to continue...')}`);
    await new Promise(resolve => setTimeout(resolve, 3000));
  }

  console.log('');

  // Install to each agent
  for (const agent of agents) {
    const targetDir = flags.global ? agent.globalPath : join(process.cwd(), agent.projectPath);
    console.log(`${c('blue', '→')} Installing to ${c('bold', agent.name)} (${targetDir})`);

    for (const skillId of skillsToInstall) {
      try {
        const installedPath = await installSkill(skillId, targetDir, skillsSourceDir);
        console.log(`  ${c('green', '✓')} ${SKILLS_REGISTRY[skillId].name}`);
      } catch (error) {
        console.log(`  ${c('red', '✗')} ${skillId}: ${error.message}`);
      }
    }
  }

  console.log(`\n${c('green', '✓ Installation complete!')}`);
  console.log(`\n${c('yellow', 'Next steps:')}`);
  console.log(`  1. Start your AI agent (Claude Code, Cursor, etc.)`);
  console.log(`  2. Ask about trading, e.g., "Create a position executor for BTC"`);
  console.log(`  3. The agent will load the relevant skill automatically`);
  console.log(`\n${c('dim', 'Tip: Run "npx hummingbot-skills check" to verify API server status')}`);
}

/**
 * Run list command - show installed skills
 */
export async function runList(flags) {
  console.log(`\n${c('bold', 'Installed Hummingbot Skills')}\n`);

  const agents = detectAgents();
  let found = false;

  for (const agent of agents) {
    const dirs = [
      { path: agent.globalPath, scope: 'global' },
      { path: join(process.cwd(), agent.projectPath), scope: 'project' },
    ];

    for (const { path: skillsDir, scope } of dirs) {
      if (!existsSync(skillsDir)) continue;

      const skills = readdirSync(skillsDir, { withFileTypes: true })
        .filter(d => d.isDirectory() && d.name.startsWith('hummingbot-'))
        .map(d => d.name.replace('hummingbot-', ''));

      if (skills.length > 0) {
        found = true;
        console.log(`${c('cyan', agent.name)} (${scope}): ${skillsDir}`);
        for (const skill of skills) {
          const info = SKILLS_REGISTRY[skill];
          const desc = info ? info.description : 'Custom skill';
          console.log(`  ${c('green', '•')} ${skill.padEnd(12)} ${c('dim', desc)}`);
        }
        console.log('');
      }
    }
  }

  if (!found) {
    console.log(c('yellow', 'No Hummingbot skills installed.'));
    console.log(`\nRun ${c('cyan', 'npx hummingbot-skills add')} to install skills.`);
  }
}

/**
 * Run find command - search skills
 */
export async function runFind(query, flags) {
  console.log(`\n${c('bold', 'Search Hummingbot Skills')}\n`);

  const results = [];
  const searchQuery = (query || '').toLowerCase();

  for (const [id, skill] of Object.entries(SKILLS_REGISTRY)) {
    const searchText = `${id} ${skill.name} ${skill.description} ${skill.category} ${skill.triggers.join(' ')}`.toLowerCase();

    if (!searchQuery || searchText.includes(searchQuery)) {
      results.push({ id, ...skill });
    }
  }

  if (results.length === 0) {
    console.log(c('yellow', `No skills matching "${query}"`));
    return;
  }

  console.log(`Found ${results.length} skill(s)${query ? ` matching "${query}"` : ''}:\n`);

  for (const skill of results) {
    console.log(`${c('green', skill.id.padEnd(12))} ${skill.description}`);
    console.log(`${' '.repeat(12)} ${c('dim', `Category: ${skill.category}`)}`);
    console.log(`${' '.repeat(12)} ${c('dim', `Triggers: ${skill.triggers.slice(0, 3).join(', ')}`)}`);
    console.log('');
  }

  console.log(`${c('dim', `Install with: npx hummingbot-skills add -s <skill-name>`)}`);
}

/**
 * Run remove command - uninstall skills
 */
export async function runRemove(skillNames, flags) {
  console.log(`\n${c('bold', 'Remove Hummingbot Skills')}\n`);

  if (skillNames.length === 0) {
    console.log(c('yellow', 'Specify skills to remove:'));
    console.log(`  npx hummingbot-skills remove executors`);
    console.log(`  npx hummingbot-skills remove executors candles`);
    return;
  }

  const agents = detectAgents();
  let removed = 0;

  for (const agent of agents) {
    const dirs = flags.global
      ? [agent.globalPath]
      : [join(process.cwd(), agent.projectPath)];

    for (const skillsDir of dirs) {
      for (const skillName of skillNames) {
        const skillPath = join(skillsDir, `hummingbot-${skillName}`);
        if (existsSync(skillPath)) {
          rmSync(skillPath, { recursive: true });
          console.log(`${c('green', '✓')} Removed ${skillName} from ${agent.name}`);
          removed++;
        }
      }
    }
  }

  if (removed === 0) {
    console.log(c('yellow', 'No matching skills found to remove.'));
  } else {
    console.log(`\n${c('green', `✓ Removed ${removed} skill(s)`)}`);
  }
}

/**
 * Run check command - verify API server status
 */
export async function runCheck(flags) {
  console.log(`\n${c('bold', 'Hummingbot API Server Status')}\n`);

  const apiUrl = process.env.API_URL || 'http://localhost:8000';

  console.log(`Checking ${c('cyan', apiUrl)}...`);

  try {
    // Use curl to check API health
    const result = spawnSync('curl', [
      '-s', '-o', '/dev/null', '-w', '%{http_code}',
      '-u', 'admin:admin',
      `${apiUrl}/api/v1/executors`,
      '--connect-timeout', '5'
    ], { encoding: 'utf-8' });

    const statusCode = result.stdout.trim();

    if (statusCode === '200') {
      console.log(`\n${c('green', '✓')} API server is ${c('green', 'running')}`);
      console.log(`\n${c('yellow', 'Ready to trade!')} Your agent can now use Hummingbot skills.`);
    } else if (statusCode === '401') {
      console.log(`\n${c('yellow', '⚠')} API server is running but ${c('yellow', 'authentication failed')}`);
      console.log(`\nCheck your credentials:`);
      console.log(`  API_USER=${process.env.API_USER || 'admin'}`);
      console.log(`  API_PASS=${process.env.API_PASS || 'admin'}`);
    } else {
      throw new Error(`HTTP ${statusCode}`);
    }
  } catch (error) {
    console.log(`\n${c('red', '✗')} API server is ${c('red', 'not reachable')}`);
    console.log(`\n${c('yellow', 'To start the API server:')}`);
    console.log(`  1. Install the "setup" skill: ${c('cyan', 'npx hummingbot-skills add -s setup')}`);
    console.log(`  2. Ask your agent: "Help me set up Hummingbot"`);
    console.log(`  3. Or run manually: ${c('cyan', 'docker-compose up -d')}`);
  }
}

/**
 * Run init command - create new skill template
 */
export async function runInit(name, flags) {
  const skillName = name || 'my-skill';

  console.log(`\n${c('bold', 'Create New Skill')}\n`);

  const skillDir = join(process.cwd(), skillName);

  if (existsSync(skillDir)) {
    console.error(c('red', `Directory "${skillName}" already exists`));
    process.exit(1);
  }

  // Create skill structure
  mkdirSync(skillDir);
  mkdirSync(join(skillDir, 'scripts'));

  // Create SKILL.md
  const skillMd = `---
name: ${skillName}
description: Description of what this skill does
version: 1.0.0
author: Your Name
triggers:
  - keyword1
  - keyword2
---

# ${skillName}

Brief description of what this skill enables.

## Capabilities

### 1. First Capability

Describe what the agent can do with this skill.

## Scripts

| Script | Description |
|--------|-------------|
| \`scripts/example.sh\` | Does something useful |

## Example Usage

\`\`\`bash
./scripts/example.sh --param value
\`\`\`

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| \`API_URL\` | \`http://localhost:8000\` | Hummingbot API server URL |
`;

  writeFileSync(join(skillDir, 'SKILL.md'), skillMd);

  // Create example script
  const exampleScript = `#!/bin/bash
# Example skill script
# Usage: ./example.sh --param VALUE

set -e

API_URL="\${API_URL:-http://localhost:8000}"
API_USER="\${API_USER:-admin}"
API_PASS="\${API_PASS:-admin}"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --param) PARAM="$2"; shift 2 ;;
        *) shift ;;
    esac
done

# Make API call
curl -s -u "$API_USER:$API_PASS" "$API_URL/api/v1/resource"
`;

  writeFileSync(join(skillDir, 'scripts', 'example.sh'), exampleScript);
  execSync(`chmod +x "${join(skillDir, 'scripts', 'example.sh')}"`);

  console.log(`${c('green', '✓')} Created skill template at ${c('cyan', skillDir)}`);
  console.log(`\nFiles created:`);
  console.log(`  ${skillDir}/`);
  console.log(`  ├── SKILL.md`);
  console.log(`  └── scripts/`);
  console.log(`      └── example.sh`);
  console.log(`\n${c('yellow', 'Next steps:')}`);
  console.log(`  1. Edit ${c('cyan', 'SKILL.md')} with your skill's instructions`);
  console.log(`  2. Add scripts to ${c('cyan', 'scripts/')} directory`);
  console.log(`  3. Test with your AI agent`);
}
