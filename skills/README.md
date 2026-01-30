# Hummingbot Skills

This directory contains skills for AI agents to manage Hummingbot trading infrastructure. Skills follow the [Agent Skills Specification](https://agentskills.io/specification).

## Available Skills

| Skill | Description | Triggers |
|-------|-------------|----------|
| [setup](./setup/SKILL.md) | Deploy Hummingbot infrastructure | "install hummingbot", "setup trading" |
| [keys](./keys/SKILL.md) | Manage exchange API credentials | "add api key", "configure exchange" |
| [executors](./executors/SKILL.md) | Create and manage trading executors | "create executor", "position executor" |
| [candles](./candles/SKILL.md) | Market data and technical indicators | "get candles", "calculate rsi" |

## Integration Guide

### For Filesystem-Based Agents

Filesystem agents (Claude Code, Cursor, terminal-based tools) activate skills by reading the SKILL.md file:

```bash
# Discover available skills
ls -la /path/to/skills/*/SKILL.md

# Activate a skill by reading it
cat /path/to/skills/executors/SKILL.md
```

### For Tool-Based Agents

Tool-based agents implement skill discovery and activation as tools:

```python
def discover_skills(skills_dir: str) -> list:
    """Scan directory for valid skills (folders with SKILL.md)."""
    skills = []
    for folder in Path(skills_dir).iterdir():
        skill_file = folder / "SKILL.md"
        if skill_file.exists():
            metadata = parse_frontmatter(skill_file)
            skills.append({
                "name": metadata.get("name"),
                "description": metadata.get("description"),
                "path": str(skill_file)
            })
    return skills

def activate_skill(skill_path: str) -> str:
    """Load full skill instructions."""
    return Path(skill_path).read_text()
```

### System Prompt Integration

Include available skills in your agent's system prompt using XML format:

```xml
<available_skills>
  <skill>
    <name>hummingbot-setup</name>
    <description>Deploy and configure Hummingbot infrastructure</description>
    <location>/path/to/skills/setup/SKILL.md</location>
  </skill>
  <skill>
    <name>hummingbot-keys</name>
    <description>Manage exchange API credentials</description>
    <location>/path/to/skills/keys/SKILL.md</location>
  </skill>
  <skill>
    <name>hummingbot-executors</name>
    <description>Create and manage trading executors</description>
    <location>/path/to/skills/executors/SKILL.md</location>
  </skill>
  <skill>
    <name>hummingbot-candles</name>
    <description>Market data and technical indicators</description>
    <location>/path/to/skills/candles/SKILL.md</location>
  </skill>
</available_skills>
```

### Generating Prompt XML

Use the reference implementation CLI to generate the XML:

```bash
# Install skills-ref (reference implementation)
pip install agentskills

# Generate available_skills XML
skills-ref to-prompt /path/to/skills/*
```

Or use this helper script:

```bash
#!/bin/bash
# generate_skills_prompt.sh
# Generates <available_skills> XML for agent prompts

SKILLS_DIR="${1:-.}"

echo "<available_skills>"
for skill_dir in "$SKILLS_DIR"/*/; do
    skill_file="$skill_dir/SKILL.md"
    if [ -f "$skill_file" ]; then
        # Extract name and description from frontmatter
        name=$(grep "^name:" "$skill_file" | head -1 | cut -d':' -f2- | xargs)
        desc=$(grep "^description:" "$skill_file" | head -1 | cut -d':' -f2- | xargs)
        echo "  <skill>"
        echo "    <name>$name</name>"
        echo "    <description>$desc</description>"
        echo "    <location>$(realpath "$skill_file")</location>"
        echo "  </skill>"
    fi
done
echo "</available_skills>"
```

## Skill Structure

Each skill follows this structure:

```
skill-name/
├── SKILL.md              # Instructions + YAML frontmatter (required)
├── scripts/              # Executable scripts (optional)
│   ├── action1.sh
│   └── action2.sh
└── references/           # Supporting documentation (optional)
    └── api_docs.md
```

### SKILL.md Format

```markdown
---
name: skill-name
description: Brief description for agent context
version: 1.0.0
author: Hummingbot Foundation
triggers:
  - keyword1
  - keyword2
---

# Skill Name

Instructions for the agent on how to use this skill...

## Capabilities

### 1. Action One

Description and usage...

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/v1/resource | GET | Gets resource |
```

## Context Efficiency

Skills are designed for minimal context usage:

| Stage | Context Cost |
|-------|--------------|
| Discovery (frontmatter only) | ~100 tokens per skill |
| Full skill activation | <5,000 tokens |
| Script execution | Output only (code not in context) |

Compare to MCP tools which load **all definitions upfront** (~12,000-20,000 tokens for full toolset).

## Security Considerations

When executing skill scripts:

1. **Sandbox execution** - Run in isolated environments when possible
2. **Validate sources** - Only run scripts from trusted skill directories
3. **User confirmation** - Ask before executing potentially dangerous operations
4. **Audit logging** - Record all script executions

## Environment Variables

All skills support these common environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `API_URL` | `http://localhost:8000` | Hummingbot API server URL |
| `API_USER` | `admin` | API authentication username |
| `API_PASS` | `admin` | API authentication password |

## References

- [Agent Skills Specification](https://agentskills.io/specification)
- [Integration Guide](https://agentskills.io/integrate-skills)
- [Reference Implementation](https://github.com/agentskills/agentskills/tree/main/skills-ref)
