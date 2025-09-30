"""Database CLI commands for initialization and management."""

import typer
from rich.console import Console
from sqlmodel import text

from .config import db_settings
from .connection import engine, get_session_sync, test_connection
from .models import ADDITIONAL_SQL

console = Console()
app = typer.Typer(help="Database management commands")


@app.command()
def init():
    """Initialize the database with tables and indexes."""
    console.print("🔧 [bold]Initializing Opinometer database...[/]")

    # Test connection first
    if not test_connection():
        console.print("❌ [bold red]Database connection failed![/]")
        console.print(f"   Connection URL: {db_settings.connection_url}")
        raise typer.Exit(1)

    console.print("✅ Database connection successful")

    try:
        # Create all tables using SQLModel
        from sqlmodel import SQLModel

        console.print("📦 Creating tables...")
        SQLModel.metadata.create_all(engine)
        console.print("✅ Tables created successfully")

        # Execute additional SQL (indexes, constraints)
        console.print("🔍 Creating indexes and constraints...")
        with get_session_sync() as session:
            # Execute each statement separately
            statements = [
                stmt.strip() for stmt in ADDITIONAL_SQL.split(";") if stmt.strip()
            ]
            for statement in statements:
                if statement.startswith("--") or not statement:
                    continue
                try:
                    session.exec(text(statement))  # type: ignore[call-overload]
                except Exception as e:
                    # Some constraints might already exist, that's ok
                    console.print(f"[dim]Note: {statement[:50]}... -> {e}[/]")

            session.commit()

        console.print("✅ Indexes and constraints created")
        console.print("🎉 [bold green]Database initialization complete![/]")

    except Exception as e:
        console.print(f"❌ [bold red]Database initialization failed:[/] {e}")
        raise typer.Exit(1)


@app.command()
def test():
    """Test database connection."""
    console.print("🔍 [bold]Testing database connection...[/]")
    console.print(f"   Host: {db_settings.db_host}:{db_settings.db_port}")
    console.print(f"   Database: {db_settings.db_name}")
    console.print(f"   User: {db_settings.db_user}")

    if test_connection():
        console.print("✅ [bold green]Database connection successful![/]")
    else:
        console.print("❌ [bold red]Database connection failed![/]")
        raise typer.Exit(1)


@app.command()
def reset():
    """Reset the database (drop and recreate all tables)."""
    console.print("⚠️  [bold yellow]This will delete ALL data![/]")
    confirm = typer.confirm("Are you sure you want to reset the database?")
    if not confirm:
        console.print("Aborted.")
        return

    try:
        from sqlmodel import SQLModel

        console.print("🗑️  Dropping all tables...")
        SQLModel.metadata.drop_all(engine)

        console.print("📦 Recreating tables...")
        SQLModel.metadata.create_all(engine)

        # Re-run additional SQL
        console.print("🔍 Recreating indexes and constraints...")
        with get_session_sync() as session:
            statements = [
                stmt.strip() for stmt in ADDITIONAL_SQL.split(";") if stmt.strip()
            ]
            for statement in statements:
                if statement.startswith("--") or not statement:
                    continue
                try:
                    session.exec(text(statement))  # type: ignore[call-overload]
                except Exception as e:
                    console.print(f"[dim]Note: {statement[:50]}... -> {e}[/]")

            session.commit()

        console.print("✅ [bold green]Database reset complete![/]")

    except Exception as e:
        console.print(f"❌ [bold red]Database reset failed:[/] {e}")
        raise typer.Exit(1)


@app.command()
def status():
    """Show database status and table information."""
    console.print("📊 [bold]Database Status[/]")
    console.print(f"   Connection: {db_settings.connection_url}")

    if not test_connection():
        console.print("❌ [bold red]Database not accessible![/]")
        return

    try:
        with get_session_sync() as session:
            # Check tables exist
            tables = [
                ("search_queries", "Search Queries"),
                ("posts", "Posts"),
                ("content", "Content"),
                ("sentiment_analyses", "Sentiment Analyses"),
            ]

            console.print("\n📋 [bold]Table Status:[/]")
            for table_name, display_name in tables:
                try:
                    result = session.exec(
                        text(f"SELECT COUNT(*) FROM {table_name}")  # type: ignore[arg-type]
                    ).first()
                    count = result if result is not None else 0
                    console.print(f"   ✅ {display_name}: {count} records")
                except Exception:
                    console.print(f"   ❌ {display_name}: Table not found")

            # Check indexes
            console.print("\n🔍 [bold]Index Status:[/]")
            try:
                result = session.exec(
                    text("""
                    SELECT schemaname, tablename, indexname
                    FROM pg_indexes
                    WHERE schemaname = 'public'
                    AND tablename IN ('search_queries', 'posts', 'content', 'sentiment_analyses')
                    ORDER BY tablename, indexname
                    """)  # type: ignore[arg-type]
                ).fetchall()

                current_table = None
                for schema, table, index in result:
                    if table != current_table:
                        console.print(f"   📊 {table}:")
                        current_table = table
                    console.print(f"      - {index}")

            except Exception as e:
                console.print(f"   ❌ Could not fetch index information: {e}")

    except Exception as e:
        console.print(f"❌ [bold red]Error checking database status:[/] {e}")


if __name__ == "__main__":
    app()
