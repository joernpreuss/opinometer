#!/usr/bin/env python3
"""Database setup script for Opinometer."""

import subprocess
import sys
import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

console = Console()


def find_docker_compose() -> str | None:
    """Find the correct docker compose command."""
    # Try modern "docker compose" first
    try:
        subprocess.run(
            ["docker", "compose", "--version"], check=True, capture_output=True
        )
        return "docker compose"
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Try legacy "docker-compose"
    try:
        subprocess.run(["docker-compose", "--version"], check=True, capture_output=True)
        return "docker-compose"
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    return None


def run_command(command: list[str], description: str) -> bool:
    """Run a command and return success status."""
    try:
        console.print(f"🔧 {description}...")
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        if result.stdout:
            console.print(f"[dim]{result.stdout.strip()}[/]")
        return True
    except subprocess.CalledProcessError as e:
        console.print(f"❌ [bold red]Failed:[/] {e}")
        if e.stderr:
            console.print(f"[dim red]{e.stderr.strip()}[/]")
        return False
    except FileNotFoundError:
        console.print(f"❌ [bold red]Command not found:[/] {command[0]}")
        return False


def main():
    """Main setup process."""
    console.print(
        Panel.fit(
            "[bold blue]🗄️  Opinometer Database Setup[/]\n\n"
            "[dim]Setting up PostgreSQL database with Docker[/]",
            title="[bold blue]Database Setup[/]",
            border_style="blue",
        )
    )

    # Find Docker Compose command
    docker_compose_cmd = find_docker_compose()
    if not docker_compose_cmd:
        console.print("❌ [bold red]Docker Compose not found![/]")
        console.print("Please install Docker Compose:")
        console.print("- Modern: [cyan]docker compose --version[/]")
        console.print("- Legacy: [cyan]docker-compose --version[/]")
        sys.exit(1)

    console.print(f"✅ Found Docker Compose: [cyan]{docker_compose_cmd}[/]")

    # Step 1: Install dependencies
    if not run_command(["uv", "sync"], "Installing dependencies"):
        sys.exit(1)

    # Step 2: Start Docker container
    cmd_parts = docker_compose_cmd.split() + ["up", "-d"]
    if not run_command(cmd_parts, "Starting PostgreSQL container"):
        sys.exit(1)

    # Step 3: Wait for database to be ready
    console.print("⏳ Waiting for database to be ready...")
    max_attempts = 30
    for attempt in range(max_attempts):
        cmd_parts = docker_compose_cmd.split() + [
            "exec",
            "-T",
            "postgres",
            "pg_isready",
            "-U",
            "opinometer",
        ]
        if run_command(
            cmd_parts,
            f"Checking database readiness (attempt {attempt + 1}/{max_attempts})",
        ):
            break
        time.sleep(2)
    else:
        console.print("❌ [bold red]Database failed to start![/]")
        sys.exit(1)

    console.print("✅ Database is ready!")

    # Step 4: Initialize Alembic
    if not run_command(
        [
            "uv",
            "run",
            "alembic",
            "revision",
            "--autogenerate",
            "--rev-id",
            "0001",
            "-m",
            "Initial migration",
        ],
        "Creating initial migration",
    ):
        console.print("[yellow]Note: Migration might already exist[/]")

    # Step 5: Run migrations
    if not run_command(
        ["uv", "run", "alembic", "upgrade", "head"], "Running database migrations"
    ):
        sys.exit(1)

    # Step 6: Initialize database
    if not run_command(
        ["uv", "run", "python", "-m", "src.database.cli", "init"],
        "Initializing database",
    ):
        sys.exit(1)

    # Step 7: Test connection
    if not run_command(
        ["uv", "run", "python", "-m", "src.database.cli", "test"],
        "Testing database connection",
    ):
        sys.exit(1)

    # Success!
    console.print(
        Panel.fit(
            "✅ [bold green]Database setup complete![/]\n\n"
            "[dim]You can now use the Opinometer database.[/]\n\n"
            "[bold]Next steps:[/]\n"
            "• Copy [cyan].env.example[/] to [cyan].env[/] and customize if needed\n"
            "• Run [cyan]uv run python -m src.database.cli status[/] to check status\n"
            "• Run [cyan]uv run src/main.py[/] to start collecting data",
            title="[bold green]Setup Complete[/]",
            border_style="green",
        )
    )


if __name__ == "__main__":
    main()
