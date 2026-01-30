#!/usr/bin/env node

/**
 * hummingbot-skills CLI
 *
 * Discover and install Hummingbot trading skills for AI agents.
 *
 * Usage:
 *   npx hummingbot-skills add              # Install all Hummingbot skills
 *   npx hummingbot-skills add --skill executors  # Install specific skill
 *   npx hummingbot-skills list             # List installed skills
 *   npx hummingbot-skills find             # Search available skills
 *   npx hummingbot-skills remove           # Remove installed skills
 *   npx hummingbot-skills check            # Check API server status
 */

import {
  runAdd,
  runList,
  runFind,
  runRemove,
  runCheck,
  runInit,
  printHelp,
  printVersion
} from '../src/index.mjs';

const args = process.argv.slice(2);
const command = args[0];

// Parse flags
const flags = {
  global: args.includes('-g') || args.includes('--global'),
  agent: getFlag(args, '-a', '--agent'),
  skill: getFlag(args, '-s', '--skill'),
  list: args.includes('-l') || args.includes('--list'),
  yes: args.includes('-y') || args.includes('--yes'),
  all: args.includes('--all'),
  help: args.includes('-h') || args.includes('--help'),
  version: args.includes('-v') || args.includes('--version'),
};

function getFlag(args, short, long) {
  const shortIdx = args.indexOf(short);
  const longIdx = args.indexOf(long);
  const idx = shortIdx !== -1 ? shortIdx : longIdx;
  if (idx !== -1 && args[idx + 1] && !args[idx + 1].startsWith('-')) {
    return args[idx + 1];
  }
  return null;
}

async function main() {
  try {
    if (flags.help || command === 'help') {
      printHelp();
      return;
    }

    if (flags.version || command === 'version') {
      printVersion();
      return;
    }

    switch (command) {
      case 'add':
      case 'install':
      case 'i':
        await runAdd(flags);
        break;

      case 'list':
      case 'ls':
        await runList(flags);
        break;

      case 'find':
      case 'search':
        await runFind(args[1], flags);
        break;

      case 'remove':
      case 'rm':
      case 'uninstall':
        await runRemove(args.slice(1).filter(a => !a.startsWith('-')), flags);
        break;

      case 'check':
      case 'status':
        await runCheck(flags);
        break;

      case 'init':
        await runInit(args[1], flags);
        break;

      default:
        if (!command) {
          // No command - show interactive menu or help
          printHelp();
        } else {
          console.error(`Unknown command: ${command}`);
          console.log('\nRun "npx hummingbot-skills --help" for usage information.');
          process.exit(1);
        }
    }
  } catch (error) {
    console.error(`\n❌ Error: ${error.message}`);
    if (process.env.DEBUG) {
      console.error(error.stack);
    }
    process.exit(1);
  }
}

main();
