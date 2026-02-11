<div align="center">

# 📦 RappterHub

### The registry for Single File Agents

**One file. Documentation + contract + deterministic code. Shareable, installable, evolvable.**

[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3b82f6.svg)](https://python.org)
[![openrappter](https://img.shields.io/badge/openrappter-Compatible-a855f7.svg)](https://github.com/kody-w/openrappter)

[openrappter](https://github.com/kody-w/openrappter) • [Manifesto](https://kody-w.github.io/rappterhub/single-file-agents.html) • [Browse Agents](#available-agents) • [Publish Your Own](#publishing-a-single-file-agent)

---

</div>

## The Single File Agent Standard

The AI ecosystem is converging on "skills" — flat text files that tell an AI what to do. Skills are a start, but they're **not deterministic**. A skill tells the AI *what* to do but not *how*. The result? Inconsistent behavior, security gaps, and an inevitable bolt-on of plugins to add the determinism that was missing from the start.

**RappterHub is built on a different foundation: the Single File Agent.**

A single file agent merges three layers into one portable file:

| Layer | Purpose | In the File |
|-------|---------|-------------|
| 📋 **Native Metadata** | Deterministic contract — name, parameters, schema | `self.metadata = {...}` in `__init__()` |
| 📖 **Module Docstring** | Documentation — what it does, how to use it | Module docstring |
| ⚙️ **Executable Code** | Deterministic `perform()` — same input, same output | Class implementation |

**Why does this matter?**

- **Skills alone aren't deterministic.** An LLM interprets a text file differently each time. A `perform()` method doesn't.
- **Skills and plugins are two files.** A single file agent is one. No drift between what the docs say and what the code does.
- **Skills can't be tested.** You can't write a unit test for a Markdown file. You can test `perform()`.
- **Skills have no security boundary.** A single file agent has a typed parameter contract — it can only accept what the schema allows.

> 📄 **[Read the full manifesto →](https://kody-w.github.io/rappterhub/single-file-agents.html)**

## Quick Start

```bash
# Search for agents
openrappter rappterhub search "weather"

# Install an agent — it's just one file
openrappter rappterhub install kody-w/weather-poet

# Use it immediately
openrappter --exec WeatherPoet "Tokyo"
```

## The Single File Agent Format

Every agent published to RappterHub is a **single `.py` file** that contains its complete identity:

```python
"""
WeatherPoet Agent — Fetches weather and writes haiku poetry about conditions.
Returns mood, condition, temp_f for downstream agent chaining.
"""
import json
from openrappter.agents.basic_agent import BasicAgent

class WeatherPoetAgent(BasicAgent):
    def __init__(self):
        self.name = 'WeatherPoet'
        self.metadata = {
            "name": self.name,
            "description": "Fetches weather and writes haiku poetry about conditions",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "City name to get weather for"}
                },
                "required": []
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs):
        query = kwargs.get('query', '')
        weather = self.fetch_weather(query)
        haiku = self.compose_haiku(weather)
        return json.dumps({
            "status": "success",
            "haiku": haiku,
            "data_slush": {"mood": weather["condition"], "temp_f": weather["temp"]}
        })
```

**That's the entire agent.** No separate manifest. No companion files. No configuration to keep in sync. The file IS the agent IS the documentation IS the contract.

## Publishing a Single File Agent

### Option 1: Submit a PR

```bash
# Fork this repo, add your agent
mkdir -p registry/agents/your-name/your-agent/
cp your_agent.py registry/agents/your-name/your-agent/agent.py

# Submit a PR
```

### Option 2: Use the CLI

```bash
# Validate your agent
rappterhub publish ./my_agent.py --dry-run

# Publish to the registry
rappterhub publish ./my_agent.py
```

### What Gets Extracted

When you publish a single file agent, RappterHub automatically extracts:

- **Name, description** extracted from native metadata dict
- **Tags** for categorization
- **Documentation** from the module docstring
- **Parameter schema** for validation

No separate `AGENT.md` needed. The file contains everything.

## Available Agents

| Agent | Author | Description |
|-------|--------|-------------|
| [weather-poet](registry/agents/kody-w/weather-poet/) | kody-w | Fetches weather and writes haiku poetry |

> More agents coming soon. [Publish yours →](#publishing-a-single-file-agent)

## CLI Commands

| Command | Description |
|---------|-------------|
| `rappterhub search <query>` | Search for agents by name, description, or tags |
| `rappterhub install <author/name>` | Install an agent (downloads the single file) |
| `rappterhub list` | List installed agents |
| `rappterhub uninstall <name>` | Remove an agent |
| `rappterhub publish <path>` | Publish an agent to the registry |
| `rappterhub info <name>` | Show agent details (parsed from the file itself) |

## Registry Structure

```
registry/
├── agents/
│   └── {author}/
│       └── {agent-name}/
│           └── agent.py        # The single file agent. That's it.
└── index.json                  # Searchable index (auto-generated from metadata)
```

## Integration with openrappter

RappterHub is built into [openrappter](https://github.com/kody-w/openrappter):

```bash
# All commands work through openrappter
openrappter rappterhub search "web scraping"
openrappter rappterhub install kody-w/weather-poet
openrappter rappterhub list
```

Installed agents are auto-discovered — no restart needed. They inherit data sloshing (automatic context enrichment) and data slush (agent-to-agent signal chaining) from the openrappter framework.

## Why Not Just Skills?

Every major AI framework is discovering the same progression:

1. ✅ **Skills** — flat text files. Already mainstream.
2. 🔄 **Plugins** — deterministic code called by skills. Arriving now.
3. 🔜 **Unified format** — skill + plugin + contract merged into one file.

RappterHub starts at step 3. The single file agent pattern has been running in production for over a year — generating agents, chaining them, evolving them through natural language feedback, and deploying them across endpoints.

The industry will arrive here. We're already here.

## Contributing

1. **Publish an agent**: Fork, add your single file agent, submit a PR
2. **Improve the CLI**: Check out `cli/` in this repo
3. **Report issues**: Open an issue on GitHub

## Related

- [openrappter](https://github.com/kody-w/openrappter) — The AI agent framework
- [Single File Agent Manifesto](https://kody-w.github.io/rappterhub/single-file-agents.html) — Why skills alone aren't enough

## License

MIT

---

<div align="center">

**The standard for shareable AI agents** 🦖

</div>
