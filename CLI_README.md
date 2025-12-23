# JAICA CLI - Codebase Ingestion & Semantic Linking Tool

A powerful command-line interface for managing codebase ingestion into vector and graph databases, with semantic linking capabilities.

## Overview

The JAICA CLI provides fine-grained control over the ingestion pipeline, allowing you to:

- **Full Ingestion**: Complete pipeline with vector DB, graph DB, and semantic linking
- **Vector DB Only**: Ingest code for semantic search capabilities
- **Graph DB Only**: Build code structure and relationships
- **Semantic Linking**: Create intelligent connections between code entities
- **Status Monitoring**: View ingested projects and their statistics

## Installation

The CLI uses Typer and Rich for an enhanced terminal experience. Dependencies should already be installed. If not:

```bash
pip install typer rich
```

## Usage

### Running the CLI

You have multiple ways to run the CLI:

```bash
# Using the convenience script
./jaica [command] [arguments] [options]

# Using Python module
python -m src.app.cli [command] [arguments] [options]

# Direct execution
python src/app/cli/ingestion_cli.py [command] [arguments] [options]
```

### Available Commands

#### 1. Full Ingestion (`full`)

Perform complete ingestion: vector DB + graph DB + semantic linking.

```bash
# Ingest one project
./jaica full /path/to/project

# Ingest multiple projects
./jaica full /path/to/project1 /path/to/project2 /path/to/project3

# Skip semantic linking
./jaica full /path/to/project --skip-semantic-linking
```

**What it does:**
- Extracts code structure and creates AST nodes
- Ingests code chunks into vector database for semantic search
- Creates graph database nodes and structural relationships
- Performs semantic linking (calls, usages, implementations, overrides)

#### 2. Graph DB Ingestion (`graph`)

Ingest codebase structure into graph database only.

```bash
# Without semantic linking
./jaica graph /path/to/project

# With semantic linking
./jaica graph /path/to/project --with-semantic-linking
./jaica graph /path/to/project -s  # short form
```

**What it does:**
- Creates file, class, method, and function nodes
- Establishes structural relationships (CONTAINS)
- Optionally performs semantic linking

**Use case:**
- When you only need code structure analysis
- Building dependency graphs
- Code architecture visualization

#### 3. Semantic Graph Linking (`link`)

Perform semantic graph linking on already-ingested projects.

```bash
# Single project
./jaica link project_name

# Multiple projects
./jaica link project1 project2 project3
```

**What it does:**
- Creates CALLS relationships between functions/methods
- Links symbol usages (classes, interfaces, enums)
- Identifies IMPLEMENTS relationships
- Detects method OVERRIDES

**Use case:**
- Re-linking after code updates
- Building call graphs
- Analyzing code dependencies

#### 4. Status (`status`)

Display information about ingested projects.

```bash
./jaica status
```

**Shows:**
- List of projects in the database
- File counts per project
- Code node counts (functions, methods, classes)

#### 5. Info (`info`)

Display CLI information and usage examples.

```bash
./jaica info
```

## Examples

### Basic Workflow

```bash
# 1. Full ingestion of a new project
./jaica full /home/user/projects/my-app

# 2. Check status
./jaica status

# 3. Add another project (graph only)
./jaica graph /home/user/projects/another-app

# 4. Perform semantic linking separately
./jaica link another-app
```

### Partial Updates

```bash
# Update graph structure only
./jaica graph /path/to/updated-project

# Re-link semantics after code changes
./jaica link updated-project
```

### Batch Processing

```bash
# Ingest multiple projects at once
./jaica full ~/projects/app1 ~/projects/app2 ~/projects/app3

# Link multiple projects
./jaica link app1 app2 app3
```

### Selective Ingestion

```bash
# Graph + linking, but skip vector DB
./jaica graph /path/to/project --with-semantic-linking
```

## Command Reference

### Global Options

All commands support `--help` for detailed information:

```bash
./jaica --help
./jaica full --help
./jaica graph --help
```

### Command Options

| Command | Arguments | Options | Description |
|---------|-----------|---------|-------------|
| `full` | paths... | `--skip-semantic-linking` | Complete ingestion pipeline |
| `vector` | paths... | - | Vector DB ingestion only |
| `graph` | paths... | `-s, --with-semantic-linking` | Graph DB ingestion |
| `link` | projects... | - | Semantic linking only |
| `status` | - | - | Show project statistics |
| `info` | - | - | Display CLI information |

## Architecture

### Ingestion Flow

```
┌─────────────┐
│   Source    │
│   Code      │
└──────┬──────┘
       │
       ├──────────────┬──────────────┐
       │              │              │
       ▼              ▼              ▼
┌────────────┐ ┌────────────┐ ┌────────────┐
│   Vector   │ │   Graph    │ │  Semantic  │
│     DB     │ │     DB     │ │  Linking   │
└────────────┘ └────────────┘ └────────────┘
```

### Services Used

- **IngestionService**: Handles vector + graph DB ingestion
- **IngestionServiceGraph**: Handles graph DB only ingestion
- **SemanticLinkingService**: Creates semantic relationships
- **GraphDBService**: Manages Neo4j operations
- **VectorDB**: Manages Chroma vector operations
- **CodeClassifier**: Classifies code by language

## Project Name Convention

The project name is automatically derived from the folder name:

```bash
./jaica full /home/user/projects/my-awesome-app
# Project name: "my-awesome-app"
```

When performing semantic linking, use the project name (not the path):

```bash
./jaica link my-awesome-app
```

## Supported Languages

Currently supports:
- Python (`.py`)
- Java (`.java`)

The CLI uses the CodeClassifier to detect language for files without standard extensions.

## Error Handling

The CLI provides rich error reporting:

- ✓ Green checkmarks for successful operations
- ✗ Red X marks for failures
- ⚠ Yellow warnings for skipped operations
- Detailed stack traces for debugging

## Tips & Best Practices

1. **Start with Full Ingestion**: For new projects, use `full` command first
2. **Batch Similar Operations**: Process multiple projects in one command
3. **Check Status Regularly**: Use `status` to monitor ingestion progress
4. **Re-link After Changes**: Run `link` after significant code updates
5. **Use Graph + Linking**: For structural analysis, use `graph -s`

## Troubleshooting

### Project Not Found

If semantic linking fails with "Project not found":
```bash
# Ensure the project is ingested first
./jaica graph /path/to/project
./jaica link project_name
```

### Path Validation Errors

Ensure paths are absolute or relative to current directory:
```bash
# Use absolute paths
./jaica full /home/user/projects/myapp

# Or relative paths
./jaica full ./myapp
```

### Database Connection Issues

Check that database services are running:
```bash
# Check docker-compose services
docker-compose ps
```

## Contributing

When adding new commands:
1. Add command function with `@app.command()` decorator
2. Use Rich console for output formatting
3. Include progress indicators for long operations
4. Add comprehensive docstrings
5. Update this README

## License

[Your License Here]

