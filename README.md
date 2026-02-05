<div align="center">

# 📦 RappterHub

### The package registry for AI agents

**npm for AI agents. Search, install, publish.**

[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3b82f6.svg)](https://python.org)
[![openrappter](https://img.shields.io/badge/openrappter-Compatible-a855f7.svg)](https://github.com/kody-w/openrappter)

[openrappter](https://github.com/kody-w/openrappter) • [Browse Agents](#) • [Publish Your Own](#publishing)

---

</div>

## What is RappterHub?

RappterHub is a community-driven registry for [openrappter](https://github.com/kody-w/openrappter) agents. Think npm, but for AI agents.

```bash
# Install an agent with one command
rappterhub install kody-w/git-helper

# Use it immediately
openrappter "summarize my commits this week"
```

## Quick Start

```bash
# Install the CLI
pip install rappterhub

# Search for agents
rappterhub search "git automation"
# Found 12 agents matching "git automation"
#   kody-w/git-helper — Automate commits, PRs, and changelogs
#   devops/changelog — Generate semantic changelogs

# Install an agent
rappterhub install kody-w/git-helper
# ✓ Installed git-helper v1.2.0

# List installed agents
rappterhub list
```

## Creating an Agent

```bash
# Scaffold a new agent
rappterhub init my-agent

# This creates:
# my-agent/
# ├── AGENT.md      # Manifest (required)
# ├── agent.py      # Implementation (required)
# └── README.md     # Documentation (optional)
```

### AGENT.md Format

```yaml
---
name: my-agent
version: 1.0.0
description: Short description of what this agent does
author: your-github-username
license: MIT
runtime: python
tags:
  - automation
  - git
---

## Overview

Detailed description of capabilities.

## Usage

Examples of how to use the agent.
```

### agent.py Template

```python
from openrappter.agents.basic_agent import BasicAgent
import json

class MyAgent(BasicAgent):
    def __init__(self):
        metadata = {
            "name": "my-agent",
            "description": "What this agent does",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "User query"}
                },
                "required": []
            }
        }
        super().__init__("my-agent", metadata)

    def perform(self, **kwargs) -> str:
        query = kwargs.get("query", "")
        # Your agent logic here
        return json.dumps({"status": "success", "result": "..."})
```

## Publishing

```bash
# Validate your agent
rappterhub publish ./my-agent --dry-run

# Publish to the registry
rappterhub publish ./my-agent
```

Currently, publishing creates a PR to the [registry repository](https://github.com/rappterhub/registry). Automated publishing coming soon.

## CLI Commands

| Command | Description |
|---------|-------------|
| `rappterhub search <query>` | Search for agents |
| `rappterhub install <author/name>` | Install an agent |
| `rappterhub list` | List installed agents |
| `rappterhub uninstall <name>` | Remove an agent |
| `rappterhub init <name>` | Create a new agent project |
| `rappterhub publish <path>` | Publish an agent |
| `rappterhub info <name>` | Show agent details |

## Integration with openrappter

RappterHub is built into openrappter:

```bash
# Using openrappter CLI directly
openrappter rappterhub search "web scraping"
openrappter rappterhub install kody-w/scraper
openrappter rappterhub list
```

## Registry Structure

```
registry/
├── agents/
│   └── {author}/
│       └── {agent-name}/
│           ├── AGENT.md      # Manifest
│           ├── agent.py      # Python implementation
│           └── agent.ts      # TypeScript (optional)
└── index.json               # Searchable index
```

## Contributing

We welcome contributions!

1. **Add an agent**: Fork the registry, add your agent, submit a PR
2. **Improve the CLI**: Check out `cli/` in this repo
3. **Report issues**: Open an issue on GitHub

## Related Projects

- [openrappter](https://github.com/kody-w/openrappter) — The AI agent framework
- [ClawHub](https://clawhub.ai) — Skill registry for OpenClaw (compatible with openrappter)

## License

MIT

---

<div align="center">

**Built for the [openrappter](https://github.com/kody-w/openrappter) community** 🦖

</div>
