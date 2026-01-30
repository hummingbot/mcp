# Skills Integration Approaches: Analysis for Hummingbot

## Executive Summary

**Recommendation: Filesystem-based approach is the clear winner for Hummingbot users.**

Given that the Hummingbot API server is already running, the filesystem approach:
- Works immediately with major agents (Claude Code, Cursor, VS Code, Gemini CLI)
- Requires zero custom tool implementation
- Maximizes context efficiency (~100 tokens vs ~20,000+)
- Skills call API directly via `curl` in scripts

---

## The Two Approaches

### 1. Filesystem-Based Agents

**How it works:**
```
┌─────────────────────────────────────────────────────────────────┐
│                    FILESYSTEM-BASED AGENT                        │
│               (Claude Code, Cursor, VS Code, etc.)               │
│                                                                  │
│  Built-in Tools:  Bash, Read, Write, Grep, etc.                 │
│                                                                  │
│  Skill Activation:                                               │
│    Agent reads: cat /path/to/skills/executors/SKILL.md          │
│                                                                  │
│  Skill Execution:                                                │
│    Agent runs: ./scripts/create_executor.sh --type position_... │
│                        │                                         │
│                        ▼                                         │
│              curl -X POST $API_URL/api/v1/executors             │
└─────────────────────────────────────────────────────────────────┘
```

**Characteristics:**
- Agent operates within a computer environment (bash/unix)
- Skills activate when model reads `SKILL.md` via shell commands
- Scripts execute via standard bash
- Most capable option for complex workflows

**Supported Agents:**
- Claude Code
- Cursor
- VS Code (GitHub Copilot)
- Gemini CLI
- OpenAI Codex
- Goose
- Amp
- Roo Code
- 20+ others (see [agentskills.io](https://agentskills.io))

### 2. Tool-Based Agents

**How it works:**
```
┌─────────────────────────────────────────────────────────────────┐
│                     TOOL-BASED AGENT                             │
│               (Custom agents, web interfaces)                    │
│                                                                  │
│  Custom Tools Required:                                          │
│    - discover_skills(dir) → list of skill metadata              │
│    - activate_skill(path) → full SKILL.md content               │
│    - execute_script(path, args) → script output                 │
│                                                                  │
│  Skill Activation:                                               │
│    Agent calls: tools.activate_skill("/path/to/SKILL.md")       │
│                                                                  │
│  Skill Execution:                                                │
│    Agent calls: tools.execute_script("./create_executor.sh",    │
│                                       ["--type", "position..."]) │
│                        │                                         │
│                        ▼                                         │
│              curl -X POST $API_URL/api/v1/executors             │
└─────────────────────────────────────────────────────────────────┘
```

**Characteristics:**
- Agent has no direct file system access
- Must implement custom tools for skill management
- More control over execution environment
- Requires more implementation work

**Use Cases:**
- Web-based chat interfaces
- Mobile applications
- Sandboxed environments
- Custom enterprise agents

---

## How MCP Factors Into Each Approach

### MCP's Role in Filesystem-Based Agents

```
┌─────────────────────────────────────────────────────────────────┐
│                  FILESYSTEM-BASED ARCHITECTURE                   │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    AGENT TOOLS                             │  │
│  │                                                            │  │
│  │  Built-in OR via MCP:                                      │  │
│  │    • Bash (shell execution)                                │  │
│  │    • Read (file reading)                                   │  │
│  │    • Write (file writing)                                  │  │
│  │    • Grep (search)                                         │  │
│  │                                                            │  │
│  │  Context cost: ~500-2000 tokens (fixed, always loaded)     │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                  HUMMINGBOT SKILLS                         │  │
│  │                                                            │  │
│  │  Metadata only at startup: ~100 tokens per skill           │  │
│  │  Full skill on activation: <5000 tokens                    │  │
│  │                                                            │  │
│  │  Skills contain bash scripts that call curl directly:      │  │
│  │    curl -X POST $API_URL/api/v1/executors                  │  │
│  │                                                            │  │
│  │  ⚠️  NO MCP INVOLVEMENT in Hummingbot API calls            │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                  HUMMINGBOT API                            │  │
│  │                  (Already Running)                         │  │
│  │                                                            │  │
│  │  REST endpoints at http://localhost:8000                   │  │
│  │  Direct HTTP calls from skill scripts                      │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

**Key insight:** MCP may provide the *agent's base tools* (Bash, Read), but is **not involved** in Hummingbot operations. Skills bypass MCP entirely by using `curl` scripts.

### MCP's Role in Tool-Based Agents

```
┌─────────────────────────────────────────────────────────────────┐
│                    TOOL-BASED ARCHITECTURE                       │
│                                                                  │
│  Option A: Native Tools (Recommended)                            │
│  ────────────────────────────────────                            │
│  Implement skill tools directly in your agent:                   │
│    • discover_skills() - scan directories                        │
│    • activate_skill() - read SKILL.md                            │
│    • execute_script() - run bash scripts                         │
│                                                                  │
│  Context cost: ~300 tokens for 3 tools                           │
│                                                                  │
│                                                                  │
│  Option B: MCP-Provided Tools (Not Recommended)                  │
│  ───────────────────────────────────────────────                 │
│  Create an MCP server with skill management tools:               │
│                                                                  │
│  ⚠️  Problem: MCP tools load ALL definitions upfront             │
│      Adding MCP overhead defeats the purpose of skills           │
│                                                                  │
│  Context cost: ~500-1000 tokens + MCP overhead                   │
└─────────────────────────────────────────────────────────────────┘
```

**Key insight:** For tool-based agents, **avoid using MCP** to provide skill management tools. Implement them natively to maintain context efficiency.

---

## Context Cost Comparison

| Approach | Startup Cost | Per-Skill Cost | Execution Cost | Total (4 skills) |
|----------|--------------|----------------|----------------|------------------|
| **Filesystem + Skills** | ~500 tokens (base tools) | ~100 tokens metadata | Output only | **~900 tokens** |
| **Tool-Based + Native** | ~300 tokens (skill tools) | ~100 tokens metadata | Output only | **~700 tokens** |
| **Tool-Based + MCP** | ~1000+ tokens (MCP overhead) | ~100 tokens metadata | Output only | **~1400+ tokens** |
| **Full MCP (old approach)** | ~12,000-20,000 tokens | N/A (all loaded) | Output only | **~20,000 tokens** |

As [Simon Willison notes](https://simonwillison.net/2025/Oct/16/claude-skills/):
> "GitHub's official MCP on its own famously consumes tens of thousands of tokens of context."

---

## Recommendation: Filesystem-Based for Hummingbot

### Why Filesystem Wins

1. **Zero Implementation Required**
   - Claude Code, Cursor already have Bash/Read tools
   - Just clone repo and configure skills directory
   - Works out of the box

2. **Maximum Agent Compatibility**
   - 20+ agents support filesystem-based skills
   - Industry standard (adopted by GitHub, VS Code, OpenAI)
   - Future-proof as more agents adopt the spec

3. **Most Capable Execution**
   - Full shell access for complex operations
   - Can chain commands, pipe output, handle errors
   - Natural for infrastructure management (Docker, curl, etc.)

4. **Best Context Efficiency**
   - Skills load metadata only at startup (~100 tokens each)
   - Full instructions load on-demand
   - Script code never enters context—only output

### When Tool-Based Makes Sense

Use tool-based only if you're building:
- A web-based trading interface (no shell access)
- A mobile trading app
- A sandboxed/restricted environment
- An enterprise agent with custom security requirements

---

## Implementation Guide: Filesystem Approach

### For Claude Code Users

```bash
# 1. Clone the skills repository
git clone https://github.com/hummingbot/mcp.git ~/.hummingbot-skills

# 2. Skills are automatically available via file system
# Claude Code can read: cat ~/.hummingbot-skills/skills/executors/SKILL.md

# 3. (Optional) Add skills to your project's .claudeignore or configure
# skill discovery in your system prompt
```

### For Cursor Users

```bash
# 1. Clone skills to your project or home directory
git clone https://github.com/hummingbot/mcp.git ./hummingbot-skills

# 2. Add skill awareness to .cursor/rules or system prompt:
# "Available skills in ./hummingbot-skills/skills/"
```

### System Prompt Addition

Add this to your agent's system prompt for skill awareness:

```xml
<available_skills>
  <skill>
    <name>hummingbot-setup</name>
    <description>Deploy and configure Hummingbot infrastructure</description>
    <location>/path/to/skills/setup/SKILL.md</location>
  </skill>
  <skill>
    <name>hummingbot-executors</name>
    <description>Create and manage trading executors (position, grid, DCA)</description>
    <location>/path/to/skills/executors/SKILL.md</location>
  </skill>
  <skill>
    <name>hummingbot-keys</name>
    <description>Manage exchange API credentials</description>
    <location>/path/to/skills/keys/SKILL.md</location>
  </skill>
  <skill>
    <name>hummingbot-candles</name>
    <description>Market data and technical indicators</description>
    <location>/path/to/skills/candles/SKILL.md</location>
  </skill>
</available_skills>

When a user task matches a skill's description, read the full SKILL.md file
for detailed instructions. Execute scripts via bash as needed.
```

---

## Execution Flow: Complete Example

**User request:** "Create a BTC position with 2% stop loss"

```
1. DISCOVERY (startup)
   Agent loads: name="hummingbot-executors",
                description="Create and manage trading executors"
   Context: +100 tokens

2. MATCHING
   User says "create position" → matches "executors" skill

3. ACTIVATION
   Agent runs: cat /path/to/skills/executors/SKILL.md
   Context: +3000 tokens (full instructions loaded)

4. EXECUTION
   Agent runs: ./scripts/create_executor.sh \
                 --type position_executor \
                 --connector binance_perpetual \
                 --pair BTC-USDT \
                 --side BUY \
                 --amount 0.001 \
                 --stop-loss 0.02

   Script internally calls:
   curl -X POST -u admin:admin \
     -H "Content-Type: application/json" \
     -d '{"executor_config": {...}, "account_name": "master_account"}' \
     http://localhost:8000/api/v1/executors

   Context: +200 tokens (JSON response only, curl code never loaded)

5. RESPONSE
   Agent reports: "Position executor created. ID: exec_12345"
```

**Total context used:** ~3,300 tokens
**MCP equivalent:** ~20,000+ tokens (all tools loaded upfront)

---

## Summary

| Factor | Filesystem-Based | Tool-Based |
|--------|------------------|------------|
| **Implementation effort** | None | Significant |
| **Agent compatibility** | 20+ agents | Custom only |
| **Context efficiency** | Excellent | Good (if native) |
| **Execution capability** | Full shell | Limited |
| **MCP involvement** | Base tools only | Should avoid |
| **Recommended for** | Most users | Web/mobile apps |

**Bottom line:** If your users have Claude Code, Cursor, or any filesystem-based agent, the skills are ready to use today. No MCP server needed for Hummingbot operations.

---

## References

- [Agent Skills Specification](https://agentskills.io/specification)
- [Simon Willison: Claude Skills are awesome](https://simonwillison.net/2025/Oct/16/claude-skills/)
- [Agent Skills Integration Guide](https://agentskills.io/integrate-skills)
- [What are Agent Skills?](https://agentskills.io/what-are-skills)
