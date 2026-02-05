"""
RappterHub CLI

Command-line interface for searching, installing, and publishing openrappter agents.
"""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer
import yaml
from rich import print as rprint
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="rappterhub",
    help="Agent registry for openrappter - search, install, and publish agents.",
    no_args_is_help=True,
)

console = Console()

# Configuration
RAPPTERHUB_DIR = Path.home() / ".rappterhub"
AGENTS_DIR = Path.home() / ".openrappter" / "agents"
REGISTRY_URL = "https://api.rappterhub.dev"
REGISTRY_GITHUB = "https://github.com/rappterhub/registry"
LOCK_FILE = RAPPTERHUB_DIR / "lock.json"


def ensure_dirs():
    """Ensure required directories exist."""
    RAPPTERHUB_DIR.mkdir(parents=True, exist_ok=True)
    AGENTS_DIR.mkdir(parents=True, exist_ok=True)


def load_lock() -> dict:
    """Load the lock file tracking installed agents."""
    if LOCK_FILE.exists():
        try:
            return json.loads(LOCK_FILE.read_text())
        except json.JSONDecodeError:
            pass
    return {"installed": {}, "version": 1}


def save_lock(lock: dict):
    """Save the lock file."""
    LOCK_FILE.write_text(json.dumps(lock, indent=2))


def parse_agent_md(path: Path) -> Optional[dict]:
    """Parse an AGENT.md file."""
    if not path.exists():
        return None

    content = path.read_text(encoding="utf-8")

    # Parse YAML frontmatter
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
    if not match:
        return None

    try:
        frontmatter = yaml.safe_load(match.group(1))
        body = match.group(2)

        if not isinstance(frontmatter, dict):
            return None

        frontmatter["_body"] = body
        frontmatter["_path"] = str(path.parent)
        return frontmatter
    except yaml.YAMLError:
        return None


def validate_agent(agent_dir: Path) -> tuple[bool, str, Optional[dict]]:
    """Validate an agent directory structure."""
    agent_md = agent_dir / "AGENT.md"
    if not agent_md.exists():
        return False, "Missing AGENT.md", None

    manifest = parse_agent_md(agent_md)
    if not manifest:
        return False, "Invalid AGENT.md format", None

    required = ["name", "version", "description", "author", "runtime"]
    missing = [f for f in required if f not in manifest]
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}", None

    # Check for implementation file
    runtime = manifest.get("runtime", "python")
    if runtime == "python" or runtime == "both":
        if not (agent_dir / "agent.py").exists():
            return False, "Missing agent.py for Python runtime", None
    if runtime == "typescript" or runtime == "both":
        if not (agent_dir / "agent.ts").exists():
            return False, "Missing agent.ts for TypeScript runtime", None

    return True, "Valid", manifest


# ═══════════════════════════════════════════════════════════════════════════════
# COMMANDS
# ═══════════════════════════════════════════════════════════════════════════════


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum results"),
):
    """Search for agents in the registry."""
    ensure_dirs()

    with console.status(f"Searching for '{query}'..."):
        # Try API search first
        try:
            import requests

            response = requests.get(
                f"{REGISTRY_URL}/search",
                params={"q": query, "limit": limit},
                timeout=10,
            )
            if response.status_code == 200:
                results = response.json().get("agents", [])
            else:
                results = []
        except Exception:
            # Fallback: search local cache
            results = search_local(query)

    if not results:
        rprint(f"[yellow]No agents found for '{query}'[/yellow]")
        return

    table = Table(title=f"Search Results for '{query}'")
    table.add_column("Name", style="cyan")
    table.add_column("Author", style="green")
    table.add_column("Description")
    table.add_column("Version")

    for agent in results[:limit]:
        table.add_row(
            agent.get("name", "?"),
            agent.get("author", "?"),
            agent.get("description", "")[:50] + "...",
            agent.get("version", "?"),
        )

    console.print(table)


def search_local(query: str) -> list[dict]:
    """Search installed agents locally."""
    results = []
    query_lower = query.lower()

    for agent_dir in AGENTS_DIR.iterdir():
        if not agent_dir.is_dir():
            continue

        agent_md = agent_dir / "AGENT.md"
        if not agent_md.exists():
            continue

        manifest = parse_agent_md(agent_md)
        if not manifest:
            continue

        name = manifest.get("name", "").lower()
        desc = manifest.get("description", "").lower()
        tags = " ".join(manifest.get("tags", [])).lower()

        if query_lower in name or query_lower in desc or query_lower in tags:
            results.append(manifest)

    return results


@app.command()
def install(
    agent_ref: str = typer.Argument(..., help="Agent reference (author/name or URL)"),
    force: bool = typer.Option(False, "--force", "-f", help="Force reinstall"),
):
    """Install an agent from the registry."""
    ensure_dirs()

    # Parse agent reference
    if "/" in agent_ref and not agent_ref.startswith("http"):
        # Format: author/name
        author, name = agent_ref.split("/", 1)
        source = f"{REGISTRY_GITHUB}/raw/main/agents/{author}/{name}"
    elif agent_ref.startswith("http"):
        # Direct URL
        source = agent_ref
        name = agent_ref.rstrip("/").split("/")[-1]
        author = "unknown"
    else:
        rprint(f"[red]Invalid agent reference: {agent_ref}[/red]")
        rprint("Use format: author/name or a URL")
        raise typer.Exit(1)

    # Check if already installed
    lock = load_lock()
    if agent_ref in lock["installed"] and not force:
        rprint(f"[yellow]Agent '{agent_ref}' is already installed. Use --force to reinstall.[/yellow]")
        return

    with console.status(f"Installing {agent_ref}..."):
        target_dir = AGENTS_DIR / name

        # Try git clone first
        try:
            if target_dir.exists():
                shutil.rmtree(target_dir)

            # Clone from GitHub
            result = subprocess.run(
                ["git", "clone", "--depth", "1", source, str(target_dir)],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                # Try downloading AGENT.md and agent.py directly
                download_agent(source, target_dir)

        except Exception as e:
            rprint(f"[red]Failed to install: {e}[/red]")
            raise typer.Exit(1)

    # Validate installed agent
    valid, msg, manifest = validate_agent(target_dir)
    if not valid:
        rprint(f"[red]Invalid agent: {msg}[/red]")
        shutil.rmtree(target_dir, ignore_errors=True)
        raise typer.Exit(1)

    # Update lock file
    lock["installed"][agent_ref] = {
        "name": manifest.get("name"),
        "version": manifest.get("version"),
        "path": str(target_dir),
        "author": manifest.get("author"),
    }
    save_lock(lock)

    # Install dependencies if needed
    install_dependencies(target_dir, manifest)

    rprint(f"[green]Successfully installed {manifest.get('name')} v{manifest.get('version')}[/green]")


def download_agent(source: str, target_dir: Path):
    """Download agent files directly."""
    import requests

    target_dir.mkdir(parents=True, exist_ok=True)

    files = ["AGENT.md", "agent.py", "agent.ts", "requirements.txt", "package.json"]
    downloaded = False

    for filename in files:
        url = f"{source}/{filename}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                (target_dir / filename).write_text(response.text)
                downloaded = True
        except Exception:
            pass

    if not downloaded:
        raise Exception("Failed to download agent files")


def install_dependencies(agent_dir: Path, manifest: dict):
    """Install agent dependencies."""
    runtime = manifest.get("runtime", "python")

    # Python dependencies
    if runtime in ("python", "both"):
        requirements = agent_dir / "requirements.txt"
        if requirements.exists():
            rprint("[dim]Installing Python dependencies...[/dim]")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-q", "-r", str(requirements)],
                capture_output=True,
            )

    # Node dependencies
    if runtime in ("typescript", "both"):
        package_json = agent_dir / "package.json"
        if package_json.exists():
            rprint("[dim]Installing Node dependencies...[/dim]")
            subprocess.run(
                ["npm", "install", "--silent"],
                cwd=agent_dir,
                capture_output=True,
            )


@app.command(name="list")
def list_agents(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed info"),
):
    """List installed agents."""
    ensure_dirs()

    lock = load_lock()
    installed = lock.get("installed", {})

    if not installed:
        rprint("[yellow]No agents installed.[/yellow]")
        rprint("Use 'rappterhub search <query>' to find agents.")
        return

    table = Table(title="Installed Agents")
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Author")

    if verbose:
        table.add_column("Path")

    for ref, info in installed.items():
        row = [
            info.get("name", ref),
            info.get("version", "?"),
            info.get("author", "?"),
        ]
        if verbose:
            row.append(info.get("path", "?"))
        table.add_row(*row)

    console.print(table)


@app.command()
def uninstall(
    agent_name: str = typer.Argument(..., help="Agent name to uninstall"),
):
    """Uninstall an agent."""
    ensure_dirs()

    lock = load_lock()

    # Find agent by name or ref
    found_ref = None
    for ref, info in lock.get("installed", {}).items():
        if info.get("name") == agent_name or ref == agent_name:
            found_ref = ref
            break

    if not found_ref:
        rprint(f"[red]Agent '{agent_name}' not found.[/red]")
        raise typer.Exit(1)

    info = lock["installed"][found_ref]
    agent_path = Path(info.get("path", ""))

    if agent_path.exists():
        shutil.rmtree(agent_path)

    del lock["installed"][found_ref]
    save_lock(lock)

    rprint(f"[green]Uninstalled {agent_name}[/green]")


@app.command()
def publish(
    agent_dir: Path = typer.Argument(..., help="Path to agent directory"),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Validate without publishing"),
):
    """Publish an agent to the registry."""
    if not agent_dir.is_dir():
        rprint(f"[red]Not a directory: {agent_dir}[/red]")
        raise typer.Exit(1)

    # Validate agent
    valid, msg, manifest = validate_agent(agent_dir)
    if not valid:
        rprint(f"[red]Validation failed: {msg}[/red]")
        raise typer.Exit(1)

    rprint(f"[green]Agent validated:[/green]")
    rprint(f"  Name: {manifest.get('name')}")
    rprint(f"  Version: {manifest.get('version')}")
    rprint(f"  Author: {manifest.get('author')}")
    rprint(f"  Runtime: {manifest.get('runtime')}")

    if dry_run:
        rprint("\n[yellow]Dry run - not publishing.[/yellow]")
        return

    # Create publish bundle
    rprint("\n[dim]Publishing to RappterHub...[/dim]")

    # For now, guide user to create a PR
    author = manifest.get("author")
    name = manifest.get("name")

    rprint(f"""
[green]To publish your agent:[/green]

1. Fork {REGISTRY_GITHUB}
2. Add your agent to: agents/{author}/{name}/
3. Create a pull request

[dim]Automated publishing coming soon![/dim]
""")


@app.command()
def init(
    name: str = typer.Argument(..., help="Agent name"),
    output: Path = typer.Option(Path("."), "--output", "-o", help="Output directory"),
):
    """Initialize a new agent project."""
    agent_dir = output / name
    agent_dir.mkdir(parents=True, exist_ok=True)

    # Create AGENT.md template
    agent_md = f"""---
name: {name}
version: 0.1.0
description: A brief description of what this agent does
author: your-github-username
license: MIT
runtime: python
tags:
  - example
requires:
  python: ">=3.10"
---

## Overview

Describe your agent's capabilities and use cases.

## Usage

```python
# Example usage
result = agent.execute(query="example query")
```

## Configuration

Document any configuration options here.
"""
    (agent_dir / "AGENT.md").write_text(agent_md)

    # Create agent.py template
    agent_py = f'''"""
{name} - openrappter Agent

Description of what this agent does.
"""

import json
from typing import Any

# Import BasicAgent if available
try:
    from openrappter.agents.basic_agent import BasicAgent
except ImportError:
    # Standalone mode
    class BasicAgent:
        def __init__(self, name: str, metadata: dict):
            self.name = name
            self.metadata = metadata
            self.context = {{}}

        def execute(self, **kwargs) -> str:
            return self.perform(**kwargs)

        def perform(self, **kwargs) -> str:
            raise NotImplementedError


class {name.replace("-", "_").title().replace("_", "")}Agent(BasicAgent):
    """
    {name} Agent - Add your description here.
    """

    def __init__(self):
        metadata = {{
            "name": "{name}",
            "description": "A brief description of what this agent does",
            "parameters": {{
                "type": "object",
                "properties": {{
                    "query": {{
                        "type": "string",
                        "description": "The query or command for this agent"
                    }}
                }},
                "required": []
            }}
        }}
        super().__init__("{name}", metadata)

    def perform(self, **kwargs) -> str:
        """
        Execute the agent's main functionality.

        Args:
            query: The user's query or command

        Returns:
            JSON string with the result
        """
        query = kwargs.get("query", "")

        # TODO: Implement your agent logic here

        return json.dumps({{
            "status": "success",
            "message": f"Processed: {{query}}",
            "result": None
        }})


# Allow direct execution for testing
if __name__ == "__main__":
    agent = {name.replace("-", "_").title().replace("_", "")}Agent()
    result = agent.execute(query="test")
    print(result)
'''
    (agent_dir / "agent.py").write_text(agent_py)

    rprint(f"[green]Created new agent at {agent_dir}[/green]")
    rprint(f"""
Next steps:
  1. Edit {agent_dir}/AGENT.md with your details
  2. Implement your logic in {agent_dir}/agent.py
  3. Test with: python {agent_dir}/agent.py
  4. Publish with: rappterhub publish {agent_dir}
""")


@app.command()
def info(
    agent_name: str = typer.Argument(..., help="Agent name"),
):
    """Show detailed information about an agent."""
    ensure_dirs()

    # Check installed agents first
    lock = load_lock()
    for ref, info in lock.get("installed", {}).items():
        if info.get("name") == agent_name or ref == agent_name:
            agent_path = Path(info.get("path", ""))
            agent_md = agent_path / "AGENT.md"

            if agent_md.exists():
                manifest = parse_agent_md(agent_md)
                if manifest:
                    rprint(f"[cyan]{manifest.get('name')}[/cyan] v{manifest.get('version')}")
                    rprint(f"[dim]by {manifest.get('author')}[/dim]\n")
                    rprint(manifest.get("description", ""))
                    rprint(f"\n[dim]Runtime:[/dim] {manifest.get('runtime', 'python')}")
                    rprint(f"[dim]Tags:[/dim] {', '.join(manifest.get('tags', []))}")
                    rprint(f"[dim]Path:[/dim] {agent_path}")

                    if manifest.get("_body"):
                        rprint(f"\n[dim]{'─' * 40}[/dim]\n")
                        rprint(manifest["_body"][:1000])
                    return

    rprint(f"[yellow]Agent '{agent_name}' not found locally.[/yellow]")
    rprint("Use 'rappterhub search' to find agents in the registry.")


if __name__ == "__main__":
    app()
