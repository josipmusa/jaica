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
        results = self.graph_db.run_get_list(query, params)
        return [dict(r["n"]) for r in results]

    def project_exists(self, project_name: str) -> bool:
        query = """
        MATCH (p:Project {name: $name})
        RETURN count(p) > 0 AS exists
        """
        result = self.graph_db.run_get_single(query, {"name": project_name})
        return result["exists"]

    def list_projects(self) -> List[dict]:
        """
        Returns a list of all projects in the graph database.
        Each project dict contains:
            - name: project name
            - node_count: number of code nodes in the project
        """
        query = """
        MATCH (p:Project)
        OPTIONAL MATCH (n:CodeNode {project: p.name})
        WITH p.name AS name, COUNT(n) AS node_count
        RETURN name, node_count
        ORDER BY name
        """
        results = self.graph_db.run_get_list(query, {})
        return [{"name": r["name"], "node_count": r["node_count"]} for r in results]

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
        results = self.graph_db.run_get_list(query, params)
        return [dict(r["n"]) for r in results]

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

        results = self.graph_db.run_get_list(query, params)
        return [dict(r["n"]) for r in results]

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

        results =  self.graph_db.run_get_list(query, params)
        return [dict(r["n"]) for r in results]

    def list_methods(self, class_name: Optional[str], project_name: str) -> list[dict]:
        """
        If class_name is provided → return methods/functions inside the class.
        If class_name is None → return all top-level functions in the project.

        Returns a list of dicts:
            {
                "method_name": str,
                "class_name": Optional[str],
                "file_path": str
            }
        """
        if class_name:
            query = """
            MATCH (c:CodeNode {node_kind: 'class', node_name: $class_name, project: $project})
            OPTIONAL MATCH (c)-[:CONTAINS]->(m:CodeNode)
            WHERE m.node_kind IN ['method', 'function']
            RETURN m.node_name AS method_name, c.node_name AS class_name, m.file_path AS file_path
            """
            params = {"project": project_name, "class_name": class_name}
        else:
            # top-level functions not contained in a class
            query = """
            MATCH (m:CodeNode)
            WHERE m.project = $project AND m.node_kind = 'function'
              AND NOT ( (:CodeNode {node_kind: 'class', project: $project})-[:CONTAINS]->(m) )
            RETURN m.node_name AS method_name, NULL AS class_name, m.file_path AS file_path
            """
            params = {"project": project_name}

        results = self.graph_db.run_get_list(query, params)
        return [r for r in results if r.get("method_name")]

    def find_class_for_method(self, method_name: str, project_name: str) -> Optional[str]:
        """
        Returns the class containing the method, or None if it's a module-level function.
        """
        query = """
        MATCH (c:CodeNode {node_kind: 'class', project: $project})-[:CONTAINS]->(m:CodeNode)
        WHERE m.node_name = $method_name AND m.node_kind IN ['method', 'function']
        RETURN c.node_name AS class_name
        LIMIT 1
        """
        params = {"project": project_name, "method_name": method_name}
        result = self.graph_db.run_get_single(query, params)
        return result["class_name"] if result else None

    def find_method_or_function_node(self, method_name: str, project_name: str) -> Optional[dict]:
        """
        Finds a method or module-level function node by name in the given project.
        Returns a dict with:
            {
                "method_name": str,
                "class_name": Optional[str],
                "file_path": Optional[str]
            }
        Returns None if not found.
        """
        query = """
        MATCH (m:CodeNode)
        WHERE m.project = $project
          AND m.node_name = $method_name
          AND m.node_kind IN ['method', 'function']
        OPTIONAL MATCH (c:CodeNode {node_kind: 'class', project: $project})-[:CONTAINS]->(m)
        RETURN m.node_name AS method_name,
               c.node_name AS class_name,
               m.file_path AS file_path
        LIMIT 1
        """
        params = {"project": project_name, "method_name": method_name}
        result = self.graph_db.run_get_single(query, params)
        return dict(result) if result else None

    def is_method_called_externally(self, class_name: Optional[str], method_name: str) -> bool:
        """
        Returns True if the method/function is called from outside its class.
        """
        if class_name:
            class_filter = """
            MATCH (c:CodeNode {node_kind: 'class', node_name: $class_name})-[:CONTAINS]->(m:CodeNode)
            """
            params = {"class_name": class_name, "method_name": method_name}
            external_filter = "AND NOT (caller)-[:CONTAINS]->(m)"
        else:
            class_filter = """
            MATCH (m:CodeNode {node_kind: 'function', node_name: $method_name})
            """
            params = {"method_name": method_name}
            external_filter = ""

        query = f"""
        {class_filter}
        MATCH (caller)-[r:SEMANTIC_LINK]->(m)
        WHERE m.node_name = $method_name
          AND r.type = 'CALLS'
          {external_filter}
        RETURN COUNT(caller) > 0 AS called_externally
        """

        result = self.graph_db.run_get_single(query, params)
        return result["called_externally"] if result else False

    def get_class_collaborator_count(self, class_name: str) -> int:
        """
        Returns the number of distinct classes that this class depends on.
        """
        query = """
        MATCH (c:CodeNode {node_kind: 'class', node_name: $class_name})-[:CONTAINS]->(m:CodeNode)
        MATCH (m)-[r:SEMANTIC_LINK]->(other:CodeNode {node_kind: 'class'})
        WHERE r.type IN ['USES', 'CALLS']
        RETURN COUNT(DISTINCT other) AS collaborator_count
        """
        params = {"class_name": class_name}
        result = self.graph_db.run_get_single(query, params)
        return result["collaborator_count"] if result else 0

    def get_method_dependencies(self, class_name: Optional[str], method_name: str) -> list[str]:
        """
        Returns a list of classes or methods that the given method/function depends on.
        """
        if class_name:
            query = """
            MATCH (c:CodeNode {node_kind: 'class', node_name: $class_name})-[:CONTAINS]->(m:CodeNode)
            WHERE m.node_name = $method_name AND m.node_kind IN ['method', 'function']
            MATCH (m)-[r:SEMANTIC_LINK]->(dep:CodeNode)
            WHERE r.type IN ['USES', 'CALLS']
            RETURN DISTINCT dep.node_name AS dependency
            """
            params = {"class_name": class_name, "method_name": method_name}
        else:
            query = """
            MATCH (m:CodeNode {node_kind: 'function', node_name: $method_name})
            MATCH (m)-[r:SEMANTIC_LINK]->(dep:CodeNode)
            WHERE r.type IN ['USES', 'CALLS']
            RETURN DISTINCT dep.node_name AS dependency
            """
            params = {"method_name": method_name}

        results = self.graph_db.run_get_list(query, params)
        return [r["dependency"] for r in results]

