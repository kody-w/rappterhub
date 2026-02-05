# RappterHub Registry

This directory contains the agent registry structure. In production, this would be hosted as a separate GitHub repository at `github.com/rappterhub/registry`.

## Structure

```
registry/
├── agents/
│   ├── {author}/
│   │   ├── {agent-name}/
│   │   │   ├── AGENT.md
│   │   │   ├── agent.py
│   │   │   └── ...
│   │   └── ...
│   └── ...
├── index.json          # Agent index for fast searching
└── README.md
```

## Adding an Agent

1. Fork this repository
2. Create a directory: `agents/{your-github-username}/{agent-name}/`
3. Add your agent files (AGENT.md, agent.py, etc.)
4. Submit a pull request

## Agent Index

The `index.json` file is automatically generated from AGENT.md files and provides:
- Fast search without downloading all agents
- Version tracking
- Tag-based filtering

## Moderation

All pull requests are reviewed before merging. Agents must:
- Follow the AGENT.md specification
- Not contain malicious code
- Have a valid license
- Include working tests (recommended)

## API

The registry API is available at `api.rappterhub.dev`:

- `GET /search?q={query}` - Search agents
- `GET /agents/{author}/{name}` - Get agent info
- `GET /agents/{author}/{name}/download` - Download agent files
