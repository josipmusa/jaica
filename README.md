# JAICA - AI-Powered Codebase Analysis & Chat Assistant

JAICA (Just An Intelligent Code Assistant) is an advanced codebase analysis tool that combines **vector-based semantic search**, **graph-based structural reasoning**, and **LLM capabilities** to provide intelligent answers about your code. It ingests codebases into vector and graph databases, enabling both semantic retrieval and structural analysis for comprehensive code understanding.

## 🌟 Key Features

### 1. **Multi-Modal Code Understanding**
- **Vector Search (RAG)**: Semantic retrieval of code snippets and documentation
- **Graph Reasoning**: Structural analysis of code relationships, dependencies, and call chains
- **Hybrid Pipeline**: Combined semantic and structural analysis for complex queries

### 2. **Intelligent Query Routing**
JAICA automatically classifies user queries into different intents and routes them to the appropriate pipeline:
- **CODE_GRAPH_REASONING**: For structural/relational queries (call chains, dependencies, class hierarchies)
- **CODE_VECTOR_RETRIEVAL**: For finding code implementations and definitions
- **DOCS_VECTOR_RETRIEVAL**: For documentation, setup guides, and configuration
- **CODE_HYBRID**: For complex queries requiring both code semantics and structure
- **TEST_ANALYSIS**: For analyzing test coverage and suggesting missing tests
- **GENERAL**: For conversational queries

### 3. **Codebase Ingestion**
- Supports **Python** and **Java** codebases
- Extracts code structure using Tree-sitter AST parsing
- Creates graph database nodes for files, classes, methods, and functions
- Establishes structural relationships (CONTAINS, CALLS, IMPLEMENTS, etc.)
- Generates vector embeddings for semantic search

### 4. **Semantic Linking**
Automatically creates intelligent relationships between code entities:
- **CALLS** relationships between functions/methods
- **USES** relationships for symbol usage (classes, interfaces, enums)
- **IMPLEMENTS** relationships for interface implementations
- Cross-file and cross-module relationship detection

### 5. **Code Analysis & Quality Detection**
- ML-based code classifier (Python/Java)
- Detection of code issues: deep nesting, long functions, excessive parameters
- Test coverage analysis and recommendations

### 6. **REST API & CLI**
- FastAPI-based REST API for chat interactions
- Comprehensive CLI tool for codebase ingestion and management
- Status monitoring and project statistics

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         User Query                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
         ┌─────────────────────────┐
         │   Intent Classifier     │
         │        (LLM)            │
         └─────────────┬───────────┘
                       │
         ┌─────────────┴───────────┐
         │    Pipeline Router      │
         └─────────────┬───────────┘
                       │
    ┏━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━┓
    ▼                 ▼                  ▼
┌─────────┐    ┌──────────┐      ┌───────────┐
│   RAG   │    │  Graph   │      │  Hybrid   │
│Pipeline │    │ Pipeline │      │ Pipeline  │
└────┬────┘    └────┬─────┘      └─────┬─────┘
     │              │                   │
     ▼              ▼                   ▼
┌─────────┐    ┌──────────┐      ┌───────────┐
│ Vector  │    │  Neo4j   │      │   Both    │
│   DB    │    │ Graph DB │      │ DBs+LLM   │
└─────────┘    └──────────┘      └───────────┘
```

## 📋 Prerequisites

- **Python 3.10+**
- **Docker & Docker Compose** (for databases)
- **Ollama** (for LLM inference)
- Neo4j 5
- ChromaDB

## 🚀 Project Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd jaica
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

The main dependencies include:
- **FastAPI**: REST API framework
- **Typer & Rich**: CLI interface with beautiful terminal output
- **ChromaDB**: Vector database for semantic search
- **Neo4j**: Graph database for structural relationships
- **Tree-sitter**: AST parsing for Python and Java
- **Ollama**: LLM integration
- **ONNX Runtime**: ML model inference

### 3. Start Database Services

Start Neo4j and ChromaDB using Docker Compose:

```bash
docker compose up -d
```

This will start:
- **Neo4j** on ports 7474 (Browser) and 7687 (Bolt)
  - Credentials: `neo4j/qwerty`
  - Access browser: http://localhost:7474
- **ChromaDB** on port 8001
  - Persistent storage enabled

### 4. Configure Ollama

Install and start Ollama, then pull the required model:

```bash
ollama pull qwen2.5:3b-instruct
```

You can modify the model in `src/app/configuration/config.py` by changing the `MAIN_LLM_MODEL` variable.

### 5. Environment Configuration

The application uses the following default configurations (can be modified in `src/app/configuration/config.py`):

- **Neo4j**: `neo4j://localhost:7687` (user: neo4j, password: qwerty)
- **ChromaDB**: `http://localhost:8001`
- **LLM Model**: `qwen2.5:3b-instruct`

## 🛠️ CLI Usage

JAICA provides a powerful CLI tool for managing codebase ingestion. Make the CLI script executable:

```bash
chmod +x jaica
```

### Available Commands

#### 1. Full Ingestion (`full`)

Perform complete ingestion: vector DB + graph DB + semantic linking.

```bash
# Ingest a single project
./jaica full /path/to/your/project

# Ingest multiple projects
./jaica full /path/to/project1 /path/to/project2 /path/to/project3

# Skip semantic linking
./jaica full /path/to/project --skip-semantic-linking
```

**What it does:**
- Extracts code structure using AST parsing
- Creates vector embeddings for semantic search
- Builds graph database with nodes and relationships
- Performs semantic linking (calls, usages, implementations)

**Use case:** First-time ingestion of a codebase for full analysis capabilities.

---

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
- Creates nodes for files, classes, methods, functions
- Establishes CONTAINS relationships
- Optionally performs semantic linking

**Use case:** Building dependency graphs and code architecture visualization.

---

#### 3. Semantic Graph Linking (`link`)

Perform semantic linking on already-ingested projects.

```bash
# Single project
./jaica link project_name

# Multiple projects
./jaica link project1 project2 project3
```

**What it does:**
- Creates CALLS relationships between functions/methods
- Links symbol usages (USES relationships)
- Identifies IMPLEMENTS relationships
- Requires graph DB nodes to already exist

**Use case:** Adding semantic relationships after initial graph ingestion, or re-linking after code changes.

---

#### 4. Status Monitoring (`status`)

View information about ingested projects.

```bash
# List all projects with statistics
./jaica status
```

**What it shows:**
- Total files, classes, methods, functions
- Relationship counts (CONTAINS, CALLS, USES, IMPLEMENTS)
- Ingestion timestamps

---

### CLI Examples

```bash
# Complete workflow for a new project
./jaica full ~/code/my-python-app

# Ingest multiple microservices with linking
./jaica full ~/services/auth ~/services/api ~/services/worker

# Update graph structure only (after code changes)
./jaica graph ~/code/my-java-app -s

# Re-link relationships after code modifications
./jaica link my-python-app

# Check ingestion status
./jaica status
```

### Alternative CLI Invocation Methods

Besides using the `./jaica` script, you can also run the CLI as:

```bash
# Using Python module
python -m src.app.cli full /path/to/project

# Direct execution
python src/app/cli/ingestion_cli.py full /path/to/project
```

## 🌐 REST API Usage

### Start the API Server

```bash
uvicorn src.app.main:app --reload
```

The API will be available at `http://localhost:8000`.

### API Endpoints

#### 1. Chat Endpoint

**POST** `/api/chat`

Send a query about your codebase and get intelligent responses.

**Request Body:**
```json
{
  "prompt": "Show me all methods that call the authenticate function",
  "project_name": "my-project"
}
```

**Response:**
```json
{
  "answer": "The authenticate function is called by the following methods: ...",
  "intent": "CODE_GRAPH_REASONING",
  "dependency_graph": {
    "nodes": ["authenticate", "login", "verify_token"],
    "edges": [
      {"from": "login", "to": "authenticate"},
      {"from": "verify_token", "to": "authenticate"}
    ]
  },
  "retrieved_files": null
}
```

#### 2. Status Endpoint

**GET** `/api/status`

Check the health of the API and database connections.

**Response:**
```json
{
  "status": "ok",
  "vector_db": "connected",
  "graph_db": "connected",
  "llm": "connected"
}
```

**Status Values:**
- `"ok"`: All services (Vector DB, Graph DB, and LLM) are connected
- `"degraded"`: One or two services are disconnected or have errors
- `"error"`: All services are disconnected or have errors

Each service field (`vector_db`, `graph_db`, `llm`) can be:
- `"connected"`: Service is available
- `"disconnected"`: Service is not reachable
- `"error: {details}"`: Service connection failed with specific error

### Query Examples

```bash
# Semantic code search
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Find the implementation of user authentication", "project_name": "my-app"}'

# Graph-based reasoning
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What calls the process_payment method?", "project_name": "my-app"}'

# Test analysis
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Which methods in UserService are missing tests?", "project_name": "my-app"}'
```

## 📁 Project Structure

```
jaica/
├── src/
│   └── app/
│       ├── main.py                      # FastAPI application
│       ├── cli/                         # CLI tools
│       │   ├── __main__.py
│       │   └── ingestion_cli.py        # Main CLI implementation
│       ├── configuration/              # App configuration
│       │   ├── config.py               # Settings and prompts
│       │   ├── dependencies.py         # Dependency injection
│       │   ├── graph_db.py             # Neo4j configuration
│       │   └── vector_db.py            # ChromaDB configuration
│       ├── dtos/                        # Data transfer objects
│       │   ├── chat.py                 # Chat request/response
│       │   ├── intent.py               # Query intent types
│       │   └── graph.py                # Graph data structures
│       ├── models/                      # ML models
│       │   └── code_classifier/        # Code language classifier
│       ├── routes/                      # API routes
│       │   ├── chat.py                 # Chat endpoint
│       │   └── status.py               # Status endpoint
│       └── services/                    # Business logic
│           ├── llm_service.py          # LLM interactions
│           ├── graph_db_service.py     # Neo4j operations
│           ├── code_analysis_service.py # Code quality checks
│           ├── detectors/              # Language-specific parsers
│           │   ├── python/             # Python AST analysis
│           │   └── java/               # Java AST analysis
│           ├── ingestion/              # Ingestion services
│           │   ├── ingestion_service.py          # Full ingestion
│           │   ├── ingestion_graph_service.py    # Graph-only ingestion
│           │   └── semantic_linking_service.py   # Relationship linking
│           └── pipelines/              # Query pipelines
│               ├── pipeline_router.py   # Intent-based routing
│               ├── rag_pipeline.py      # Vector retrieval
│               ├── graph_pipeline.py    # Graph reasoning
│               └── hybrid_pipeline.py   # Combined approach
├── docker-compose.yml                   # Database services
├── requirements.txt                     # Python dependencies
├── jaica                                # CLI executable script
└── README.md                           # This file
```

## 🎯 Use Cases

### 1. Code Navigation & Discovery
```bash
# Find all implementations of an interface
"Show me all classes that implement the Repository interface"

# Discover related code
"What are the dependencies of the PaymentService class?"
```

### 2. Understanding Code Flow
```bash
# Trace execution paths
"Show me the call chain from the login endpoint to the database"

# Find usage patterns
"Where is the validateUser method called from?"
```

### 3. Refactoring & Impact Analysis
```bash
# Assess change impact
"What would be affected if I modify the authenticate method?"

# Find duplication
"Show me similar implementations of error handling"
```

### 4. Test Coverage Analysis
```bash
# Identify untested code
"Which methods in the UserController are missing tests?"

# Assess test quality
"Is the payment processing method properly tested?"
```

### 5. Documentation & Onboarding
```bash
# Understand architecture
"Explain how the authentication system works"

# Find configuration
"How do I set up the database connection?"
```

## 🔧 Advanced Configuration

### Customizing LLM Behavior

Edit `src/app/configuration/config.py` to modify:
- **LLM Model**: Change `MAIN_LLM_MODEL`
- **System Prompts**: Customize behavior for different query types
- **Intent Classification**: Adjust classification rules

### Supported Languages

Currently supports:
- **Python** (`.py` files)
- **Java** (`.java` files)

To add more languages:
1. Add parser in `src/app/services/detectors/`
2. Update `NODE_TYPES` in `ingestion_service.py`
3. Configure Tree-sitter parser in `parsers.py`

### Database Configuration

**Neo4j** - configured through env variables (in `src/app/configuration/graph_db.py`):
```python
NEO4J_URI = "neo4j://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "qwerty"
```

**ChromaDB** - configured through env variables (in `src/app/configuration/vector_db.py`):
```python
CHROMA_HOST = "localhost"
CHROMA_PORT = 8001
```

## 🐛 Troubleshooting

### Database Connection Issues
```bash
# Check if containers are running
docker compose ps

# Restart containers
docker compose down
docker compose up -d

# View logs
docker compose logs neo4j
docker compose logs chromadb
```

### Ollama Model Issues
```bash
# Verify Ollama is running
ollama list

# Re-pull the model
ollama pull qwen2.5:3b-instruct
```

### CLI Not Found
```bash
# Make script executable
chmod +x jaica

# Or use alternative invocation
python -m src.app.cli
```

### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade

# Verify Python version
python --version  # Should be 3.10+
```

## 📊 Performance Tips

1. **Ingestion Performance**: Use `--skip-semantic-linking` for faster initial ingestion, then run `link` separately
2. **Large Codebases**: Ingest projects separately rather than all at once
3. **Query Performance**: Use specific project names in queries to limit search scope
4. **Database Optimization**: Regularly backup and optimize Neo4j database

---

**JAICA** - Making codebases intelligently searchable and understandable 🚀

