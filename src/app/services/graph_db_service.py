from typing import List

from src.app.configuration.graph_db import GraphDB
from src.app.dtos.graph import GraphOperation


class GraphDBService:
    def __init__(self, graph_db: GraphDB):
        self.graph_db = graph_db
        self._create_constraints()
        self._create_indexes()

    def _create_constraints(self):
        """Ensures schema exists — executed once at startup."""
        self.graph_db.run("""
            CREATE CONSTRAINT code_node_id_unique IF NOT EXISTS
            FOR (n:CodeNode)
            REQUIRE n.node_id IS UNIQUE
        """)

    def _create_indexes(self):
        self.graph_db.run("""
                          CREATE INDEX code_node_id IF NOT EXISTS FOR (n:CodeNode) ON (n.node_id)
                          """)
        self.graph_db.run("""
                          CREATE INDEX code_node_name IF NOT EXISTS FOR (n:CodeNode) ON (n.node_name)
                          """)
        self.graph_db.run("""
                          CREATE INDEX code_project IF NOT EXISTS FOR (n:CodeNode) ON (n.project_name)
                          """)

    def upsert_node(
            self,
            node_id: str,
            node_name: str,
            node_type: str,
            language: str,
            file_path: str,
            project_name: str,
            start_line: int,
            end_line: int,
            summary: str,
            node_hash: str = None
    ):
        """
        Create or update a code node.
        MERGE is done only on the immutable ID field.
        Other properties are SET so they can be updated during re-ingestion.
        """
        query = """
        MERGE (n:CodeNode {node_id: $node_id})
        SET n.node_name   = $node_name,
            n.node_type   = $node_type,
            n.language    = $language,
            n.file_path   = $file_path,
            n.project     = $project,
            n.start_line  = $start_line,
            n.end_line    = $end_line,
            n.summary     = $summary
        """
        if node_hash:
            query += "\nSET n.node_hash = $node_hash"

        params = {
            "node_id": node_id,
            "node_name": node_name,
            "node_type": node_type,
            "language": language,
            "file_path": file_path,
            "project": project_name,
            "start_line": start_line,
            "end_line": end_line,
            "summary": summary,
        }
        if node_hash:
            params["node_hash"] = node_hash

        self.graph_db.run(query, params)

    def link_parent(self, parent_id: str, child_id: str):
        """
        Link a parent node to a child node.
        Creates parent node if it does not exist.
        """
        query = """
        MATCH (child:CodeNode {node_id: $child_id})
        MERGE (parent:CodeNode {node_id: $parent_id})
        MERGE (parent)-[:CONTAINS]->(child)
        """
        self.graph_db.run(query, {
            "child_id": child_id,
            "parent_id": parent_id
        })

    def get_node(self, node_id: str) -> dict | None:
        """
        Retrieve a node by its ID.
        Returns a dict of properties if found, else None.
        """
        query = """
        MATCH (n:CodeNode {node_id: $node_id})
        RETURN n LIMIT 1
        """
        result = self.graph_db.run_get_single(query, {"node_id": node_id})
        if result:
            # result["n"] is a Node object from neo4j driver
            return dict(result["n"])
        return None

    def find_nodes_by_name(
            self,
            name: str,
            project_name: str,
            limit: int = 5,
    ) -> List[dict]:
        query = """
           MATCH (n:CodeNode)
           WHERE n.project = $project_name
             AND (
               n.node_name = $name
               OR n.node_id ENDS WITH $name
             )
           RETURN n
           LIMIT $limit
           """

        return self.graph_db.run_get_list(query=query, name=name, project_name=project_name, limit=limit)

    def traverse(
            self,
            node_id: str,
            operation: GraphOperation,
            max_depth: int = 10,
    ) -> List[dict]:

        #TODO implement call edges
        # For now, all operations fallback to CONTAINS
        query = f"""
           MATCH (n:CodeNode {{node_id: $node_id}})
           MATCH (n)-[:CONTAINS*1..{max_depth}]->(m)
           RETURN DISTINCT m
           """

        return self.graph_db.run_get_list_by_node_id(query, node_id)
