import os
from typing import List

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

    def run_get_single(self, query:str, params: dict = None):
        with self.driver.session() as session:
            result = session.run(query, params or {})
            return result.single()  # returns first record or None

    def run_get_list(self, query: str, name: str, project_name: str, limit: int) -> List[dict]:
        with self.driver.session() as session:
            result = session.run(
                query,
                name=name,
                project_name=project_name,
                limit=limit,
            )
            return [record["n"] for record in result]

    def run_get_list_by_node_id(self, query: str, node_id: str) -> List[dict]:
        with self.driver.session() as session:
            result = session.run(query, node_id=node_id)
            return [record["m"] for record in result]