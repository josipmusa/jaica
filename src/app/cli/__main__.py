"""
Entry point for running the CLI as a module.
Allows running: python -m src.app.services.ingestion.cli
"""

from src.app.cli.ingestion_cli import main

if __name__ == "__main__":
    main()

