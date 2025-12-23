"""
CLI for managing codebase ingestion and semantic linking.

This module provides a command-line interface for controlling the ingestion
and semantic linking flow of the project.
"""

import traceback
from pathlib import Path
from typing import List
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.app.services.ingestion.ingestion_service import IngestionService
from src.app.services.ingestion.ingestion_graph_service import IngestionServiceGraph
from src.app.services.ingestion.semantic_linking_service import SemanticLinkingService
from src.app.configuration.dependencies import (
    get_vector_db,
    get_code_classifier,
    get_graph_db_service,
)

app = typer.Typer(
    name="jaica",
    help="JAICA - CLI for codebase ingestion and semantic linking",
    add_completion=False,
)

console = Console()


def validate_paths(paths: List[str]) -> List[Path]:
    """Validate that all paths exist and are directories."""
    validated_paths = []
    for path_str in paths:
        path = Path(path_str)
        if not path.exists():
            console.print(f"[red]✗[/red] Path does not exist: {path}")
            continue
        if not path.is_dir():
            console.print(f"[red]✗[/red] Path is not a directory: {path}")
            continue
        validated_paths.append(path)
    return validated_paths


@app.command("full")
def full_ingestion(
    paths: List[str] = typer.Argument(
        ...,
        help="Paths to codebases to ingest",
    ),
    skip_semantic_linking: bool = typer.Option(
        False,
        "--skip-semantic-linking",
        help="Skip semantic linking after ingestion",
    ),
):
    """
    Perform full ingestion: vector DB + graph DB + semantic linking.

    This combines vector database ingestion, graph database ingestion,
    and semantic linking in one command.
    """
    console.print("\n[bold cyan]🚀 Starting Full Ingestion[/bold cyan]\n")

    validated_paths = validate_paths(paths)
    if not validated_paths:
        console.print("[red]No valid paths to process[/red]")
        raise typer.Exit(code=1)

    # Initialize service
    service = IngestionService(
        get_vector_db(),
        get_code_classifier(),
        get_graph_db_service()
    )

    project_names = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for folder in validated_paths:
            project_name = folder.name
            project_names.append(project_name)

            task = progress.add_task(
                f"Ingesting {project_name}...",
                total=None
            )

            try:
                service.ingest_codebase(folder, project_name)
                progress.update(task, description=f"[green]✓[/green] Ingested {project_name}")
                console.print(f"[green]✓[/green] Successfully ingested: {folder}")
            except Exception as e:
                progress.update(task, description=f"[red]✗[/red] Failed {project_name}")
                console.print(f"[red]✗[/red] Failed to ingest {folder}: {e}")
                traceback.print_exc()

    # Semantic linking
    if not skip_semantic_linking and project_names:
        console.print("\n[bold cyan]🔗 Starting Semantic Linking[/bold cyan]\n")
        _run_semantic_linking(project_names)

    console.print("\n[bold green]✓ Full ingestion complete![/bold green]\n")

@app.command("graph")
def graph_ingestion(
    paths: List[str] = typer.Argument(
        ...,
        help="Paths to codebases to ingest into graph DB",
    ),
    with_semantic_linking: bool = typer.Option(
        False,
        "--with-semantic-linking",
        "-s",
        help="Perform semantic linking after graph ingestion",
    ),
):
    """
    Perform graph DB ingestion only.

    This ingests code structure and relationships into the graph database,
    without updating the vector database.
    """
    console.print("\n[bold cyan]🚀 Starting Graph DB Ingestion[/bold cyan]\n")

    validated_paths = validate_paths(paths)
    if not validated_paths:
        console.print("[red]No valid paths to process[/red]")
        raise typer.Exit(code=1)

    # Initialize service
    service = IngestionServiceGraph(
        get_code_classifier(),
        get_graph_db_service()
    )

    project_names = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for folder in validated_paths:
            project_name = folder.name
            project_names.append(project_name)

            task = progress.add_task(
                f"Ingesting {project_name} to graph DB...",
                total=None
            )

            try:
                service.ingest_codebase(folder, project_name)
                progress.update(task, description=f"[green]✓[/green] Ingested {project_name}")
                console.print(f"[green]✓[/green] Successfully ingested to graph DB: {folder}")
            except Exception as e:
                progress.update(task, description=f"[red]✗[/red] Failed {project_name}")
                console.print(f"[red]✗[/red] Failed to ingest {folder}: {e}")
                traceback.print_exc()

    # Semantic linking
    if with_semantic_linking and project_names:
        console.print("\n[bold cyan]🔗 Starting Semantic Linking[/bold cyan]\n")
        _run_semantic_linking(project_names)

    console.print("\n[bold green]✓ Graph DB ingestion complete![/bold green]\n")


@app.command("link")
def semantic_linking(
    projects: List[str] = typer.Argument(
        ...,
        help="Project names to perform semantic linking on",
    ),
):
    """
    Perform semantic linking only.

    This creates semantic relationships between code entities in the graph database
    based on symbol usage, calls, implementations, and overrides.
    """
    console.print("\n[bold cyan]🔗 Starting Semantic Linking[/bold cyan]\n")

    if not projects:
        console.print("[red]No projects specified[/red]")
        raise typer.Exit(code=1)

    _run_semantic_linking(projects)

    console.print("\n[bold green]✓ Semantic linking complete![/bold green]\n")


def _run_semantic_linking(projects: List[str]):
    """Internal helper to run semantic linking."""
    graph_db_service = get_graph_db_service()
    semantic_linking_service = SemanticLinkingService(graph_db_service)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for project in projects:
            task = progress.add_task(
                f"Linking {project}...",
                total=None
            )

            if not graph_db_service.project_exists(project):
                progress.update(task, description=f"[yellow]⚠[/yellow] Project {project} not found")
                console.print(f"[yellow]⚠[/yellow] Project '{project}' not found in graph DB")
                continue

            try:
                semantic_linking_service.run(project)
                progress.update(task, description=f"[green]✓[/green] Linked {project}")
                console.print(f"[green]✓[/green] Successfully linked: {project}")
            except Exception as e:
                progress.update(task, description=f"[red]✗[/red] Failed {project}")
                console.print(f"[red]✗[/red] Failed to link {project}: {e}")
                traceback.print_exc()


@app.command("status")
def show_status():
    """
    Show the status of ingested projects.

    Displays information about projects in the graph database.
    """
    console.print("\n[bold cyan]📊 Project Status[/bold cyan]\n")

    try:
        graph_db_service = get_graph_db_service()

        # Get all projects (this assumes there's a method to get projects)
        # If not available, we'll show a generic message
        console.print("[yellow]Connecting to graph database...[/yellow]")

        # Try to query for projects using the underlying graph_db
        result = graph_db_service.graph_db.run_get_list("""
            MATCH (p:Project)
            OPTIONAL MATCH (p)-[:CONTAINS]->(f:File)
            OPTIONAL MATCH (f)-[:CONTAINS]->(n)
            WHERE n.node_type IN ['function', 'method', 'class', 'interface']
            RETURN p.name as project, 
                   COUNT(DISTINCT f) as file_count,
                   COUNT(DISTINCT n) as node_count
            ORDER BY p.name
        """)

        if result:
            table = Table(title="Ingested Projects")
            table.add_column("Project", style="cyan", no_wrap=True)
            table.add_column("Files", style="magenta")
            table.add_column("Code Nodes", style="green")

            for row in result:
                table.add_row(
                    str(row.get("project", "N/A")),
                    str(row.get("file_count", 0)),
                    str(row.get("node_count", 0)),
                )

            console.print(table)
        else:
            console.print("[yellow]No projects found in database[/yellow]")

    except Exception as e:
        console.print(f"[red]✗[/red] Failed to retrieve status: {e}")
        traceback.print_exc()

    console.print()


@app.command("info")
def show_info():
    """
    Display information about the CLI and available commands.
    """
    console.print("\n[bold cyan]ℹ️  JAICA CLI Information[/bold cyan]\n")

    info_text = """
[bold]Available Commands:[/bold]

  [cyan]full[/cyan]     - Complete ingestion pipeline (vector DB + graph DB + semantic linking)
  [cyan]vector[/cyan]   - Ingest codebase into vector database only
  [cyan]graph[/cyan]    - Ingest codebase into graph database only
  [cyan]link[/cyan]     - Perform semantic linking on existing graph data
  [cyan]status[/cyan]   - Show status of ingested projects
  [cyan]info[/cyan]     - Display this information

[bold]Usage Examples:[/bold]

  # Full ingestion of a project
  python -m src.app.cli full /path/to/project

  # Graph ingestion with semantic linking
  python -m src.app.cli graph /path/to/project --with-semantic-linking

  # Vector DB ingestion only
  python -m src.app.cli vector /path/to/project1 /path/to/project2

  # Semantic linking for existing projects
  python -m src.app.cli link project_name1 project_name2

  # Check project status
  python -m src.app.cli status

[bold]Notes:[/bold]

  • Multiple paths/projects can be specified for batch processing
  • Project name is derived from the folder name
  • Use --help on any command for detailed options
    """

    console.print(info_text)
    console.print()


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()

