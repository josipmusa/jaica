import os

from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

class GraphDB:
    def __init__(self):
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USERNAME")
        password = os.getenv("NEO4J_PASSWORD")
        if not uri or not user or not password:
            raise RuntimeError("Missing Neo4j environment variables")

        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def run(self, query: str, params: dict = None):
        with self.driver.session() as session:
            return session.run(query, params or {})

    def run_get_single(self, query: str, params: dict = None):
        with self.driver.session() as session:
            result = session.run(query, params or {})
            record = result.single()
            return dict(record) if record else None

    def run_get_list(self, query: str, params: dict = None):
        """
        Returns a list of dicts for each record.
        Each dict maps field name -> value.
        """
        with self.driver.session() as session:
            result = session.run(query, params or {})
            return [dict(record) for record in result]
