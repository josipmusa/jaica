from typing import List, Optional

from src.app.configuration.graph_db import GraphDB
from src.app.dtos.graph import GraphOperation


class GraphDBService:
    def __init__(self, graph_db: GraphDB):
        self.graph_db = graph_db
        self._create_constraints()
        self._create_indexes()

    # -------------------------
    # Schema
    # -------------------------

    def _create_constraints(self):
        self.graph_db.run("""
            CREATE CONSTRAINT code_node_id_unique IF NOT EXISTS
            FOR (n:CodeNode)
            REQUIRE n.node_id IS UNIQUE
        """)

    def _create_indexes(self):
        self.graph_db.run("""
                          CREATE INDEX code_node_id IF NOT EXISTS
                              FOR (n:CodeNode) ON (n.node_id)
                          """)
        self.graph_db.run("""
                          CREATE INDEX code_node_name IF NOT EXISTS
                              FOR (n:CodeNode) ON (n.node_name)
                          """)
        self.graph_db.run("""
                          CREATE INDEX code_node_project IF NOT EXISTS
                              FOR (n:CodeNode) ON (n.project)
                          """)
        self.graph_db.run("""
                          CREATE INDEX code_node_symbols_defined IF NOT EXISTS
                              FOR (n:CodeNode) ON (n.symbols_defined)
                          """)

    def upsert_node(
            self,
            node_id: str,
            node_name: str,
            node_kind: str,
            node_type: str,
            language: str,
            file_path: str,
            project_name: str,
            start_line: int,
            end_line: int,
            summary: str,
            symbols_defined: list[str],
            symbols_used: list[str],
            node_hash: str | None = None,
    ):
        query = """
        MERGE (n:CodeNode {node_id: $node_id})
        SET n.node_name       = $node_name,
            n.node_kind       = $node_kind,
            n.node_type       = $node_type,
            n.language        = $language,
            n.file_path       = $file_path,
            n.project         = $project,
            n.start_line      = $start_line,
            n.end_line        = $end_line,
            n.summary         = $summary,
            n.symbols_defined = $symbols_defined,
            n.symbols_used    = $symbols_used
        """

        params = {
            "node_id": node_id,
            "node_name": node_name,
            "node_kind": node_kind,
            "node_type": node_type,
            "language": language,
            "file_path": file_path,
            "project": project_name,
            "start_line": start_line,
            "end_line": end_line,
            "summary": summary,
            "symbols_defined": symbols_defined,
            "symbols_used": symbols_used,
        }

        if node_hash:
            query += "\nSET n.node_hash = $node_hash"
            params["node_hash"] = node_hash

        self.graph_db.run(query, params)

    def upsert_project(self, project_name: str):
        self.graph_db.run(
            """
            MERGE (p:Project {name: $name})
            """,
            {"name": project_name},
        )

    def get_node(self, node_id: str) -> Optional[dict]:
        query = """
        MATCH (n:CodeNode {node_id: $node_id})
        RETURN n
        """
        params = {
            "node_id": node_id
        }
        result = self.graph_db.run_get_single(query, params)
        return dict(result["n"]) if result else None

    def get_nodes_by_project(self, project_name: str) -> List[dict]:
        query = """
        MATCH (n:CodeNode)
        WHERE n.project = $project
        RETURN n
        """

        params = {
            "project": project_name
        }
        return self.graph_db.run_get_list(query, params)

    def project_exists(self, project_name: str) -> bool:
        query = """
        MATCH (p:Project {name: $name})
        RETURN count(p) > 0 AS exists
        """
        result = self.graph_db.run_get_single(query, {"name": project_name})
        return result["exists"]

    def resolve_symbol(
            self,
            symbol: str,
            project_name: str,
            limit: int = 5,
    ) -> list[dict]:
        """
        Resolves a symbol to nodes that define it.
        """
        query = """
        MATCH (n:CodeNode)
        WHERE n.project = $project
          AND $symbol IN n.symbols_defined
        RETURN n
        LIMIT $limit
        """
        params = {
            "symbol": symbol,
            "project": project_name,
            "limit": limit
        }
        return self.graph_db.run_get_list(query, params)

    # -------------------------
    # Relationships
    # -------------------------

    def link(
            self,
            from_node_id: str,
            to_node_id: str,
            rel_type: str,
            properties: dict | None = None,
    ):
        props = ""
        if properties:
            props = " SET r += $props"

        query = f"""
        MATCH (a:CodeNode {{node_id: $from}})
        MATCH (b:CodeNode {{node_id: $to}})
        MERGE (a)-[r:{rel_type}]->(b)
        {props}
        """

        self.graph_db.run(
            query,
            {
                "from": from_node_id,
                "to": to_node_id,
                "props": properties or {},
            },
        )

    def link_project_to_node(
            self,
            project_name: str,
            node_id: str,
            rel_type: str,
            properties: dict | None = None,
    ):
        props = " SET r += $props" if properties else ""
        query = f"""
        MATCH (p:Project {{name: $project}})
        MATCH (n:CodeNode {{node_id: $node}})
        MERGE (p)-[r:{rel_type}]->(n)
        {props}
        """
        self.graph_db.run(
            query,
            {"project": project_name, "node": node_id, "props": properties or {}},
        )

    def link_batch(self, links: list[dict]):
        """
        Each link:
        {
            "from": str,
            "to": str,
            "type": str,
            "confidence": float,
            "source": str,
            "props": dict
        }
        """

        query = """
        UNWIND $links AS link
        MATCH (a:CodeNode {node_id: link.from})
        MATCH (b:CodeNode {node_id: link.to})
        WHERE a <> b
        MERGE (a)-[r:SEMANTIC_LINK {type: link.type}]->(b)
        SET r += link.props
        """

        self.graph_db.run(query, {"links": links})

    # -------------------------
    # Query helpers
    # -------------------------

    def find_nodes_by_name(
            self,
            name: str,
            project_name: str,
            limit: int = 5,
    ) -> List[dict]:
        query = """
        MATCH (n:CodeNode)
        WHERE n.project = $project
          AND (
            n.node_name = $name
            OR n.node_id ENDS WITH $name
          )
        RETURN n
        LIMIT $limit
        """

        params = {
            "name": name,
            "project": project_name,
            "limit": limit
        }

        return self.graph_db.run_get_list(query, params)

    # -------------------------
    # Traversal
    # -------------------------

    def traverse(
            self,
            node_id: str,
            operation: GraphOperation,
            max_depth: int = 5,
    ) -> list[dict]:

        op_to_types = {
            GraphOperation.STRUCTURE: ["CONTAINS"],
            GraphOperation.CALLS: ["CALLS"],
            GraphOperation.CALLED_BY: ["CALLS"],
            GraphOperation.USES: ["USES"],
            GraphOperation.DEPENDENCIES: ["USES", "CALLS"],
        }

        if operation not in op_to_types:
            raise ValueError(operation)

        types = op_to_types[operation]

        # Direction
        if operation == GraphOperation.CALLED_BY:
            arrow = f"<-[:SEMANTIC_LINK*1..{max_depth}]-"
        else:
            arrow = f"-[:SEMANTIC_LINK*1..{max_depth}]->"

        query = f"""
        MATCH path = (start:CodeNode {{node_id: $node_id}}){arrow}(target)
        WHERE ALL(rel IN relationships(path) WHERE rel.type IN $types)
        RETURN DISTINCT target AS n
        """

        params = {
            "node_id": node_id,
            "types": types
        }

        return self.graph_db.run_get_list(query, params)

