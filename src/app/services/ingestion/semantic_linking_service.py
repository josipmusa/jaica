import time
from collections import defaultdict
from typing import Dict, List

from src.app.services.graph_db_service import GraphDBService


# --- simple node-kind compatibility rules ---
ALLOWED_CALLER_KINDS = {"function", "method"}
ALLOWED_CALLEE_KINDS = {"function", "method"}

ALLOWED_USAGE_KINDS = {
    "class",
    "interface",
    "enum",
    "function",
    "method",
}


class SemanticLinkingService:
    def __init__(self, graph_db_service: GraphDBService):
        self.graph_db_service = graph_db_service

    def run(self, project_name: str):
        nodes = self.graph_db_service.get_nodes_by_project(project_name)
        symbol_index = self._build_symbol_index(nodes)

        links: list[dict] = []

        links += self._collect_calls(nodes, symbol_index)
        links += self._collect_usages(nodes, symbol_index)
        links += self._collect_implements(nodes, symbol_index)
        links += self._collect_overrides(nodes, symbol_index)

        if links:
            links = self._dedupe(links)
            self.graph_db_service.link_batch(links)


    def _build_symbol_index(self, nodes: List[dict]) -> Dict[str, List[dict]]:
        """
        Maps symbol_name -> defining nodes
        """
        index: Dict[str, List[dict]] = defaultdict(list)

        for node in nodes:
            for symbol in node.get("symbols_defined", []):
                normalized = self._normalize_symbol(symbol)
                index[normalized].append(node)

        return index

    def _collect_calls(
            self,
            nodes: list[dict],
            symbol_index: dict[str, list[dict]],
    ) -> list[dict]:
        links = []

        for node in nodes:
            caller_id = node["node_id"]
            caller_kind = node.get("node_kind")

            if caller_kind not in ALLOWED_CALLER_KINDS:
                continue

            for used in node.get("symbols_used", []):
                symbol = self._normalize_symbol(used)
                candidates = symbol_index.get(symbol)

                if not candidates:
                    continue

                callee = self._select_best_candidate(
                    candidates,
                    allowed_kinds=ALLOWED_CALLEE_KINDS,
                )

                if not callee:
                    continue

                if callee["node_id"] == caller_id:
                    continue  # guard self-link

                links.append({
                    "from": caller_id,
                    "to": callee["node_id"],
                    "type": "CALLS",
                    "props": {
                        "confidence": 0.6,
                        "source": "semantic_linker:v1",
                        "created_at": time.time(),
                    },
                })

        return links

    def _collect_usages(
            self,
            nodes: list[dict],
            symbol_index: dict[str, list[dict]],
    ) -> list[dict]:
        links = []

        for node in nodes:
            user_id = node["node_id"]

            for used in node.get("symbols_used", []):
                symbol = used.split(".")[-1]
                candidates = symbol_index.get(symbol)

                if not candidates:
                    continue

                target = self._select_best_candidate(candidates, ALLOWED_USAGE_KINDS)

                if target["node_id"] == user_id:
                    continue

                links.append({
                    "from": user_id,
                    "to": target["node_id"],
                    "type": "USES",
                    "props": {
                        "confidence": 0.5,
                        "source": "semantic_linker:v1",
                        "created_at": time.time(),
                    },
                })

        return links

    def _collect_implements(
            self,
            nodes: list[dict],
            symbol_index: dict[str, list[dict]],
    ) -> list[dict]:
        links = []

        for node in nodes:
            if node.get("node_kind") != "class":
                continue

            class_id = node["node_id"]

            for used in node.get("symbols_used", []):
                symbol = used.split(".")[-1]
                candidates = symbol_index.get(symbol)

                if not candidates:
                    continue

                for target in candidates:
                    if target.get("node_kind") != "interface":
                        continue

                    links.append({
                        "from": class_id,
                        "to": target["node_id"],
                        "type": "IMPLEMENTS",
                        "props": {
                            "confidence": 0.75,
                            "source": "semantic_linker:v1",
                            "created_at": time.time(),
                        },
                    })

        return links

    def _collect_overrides(
            self,
            nodes: list[dict],
            symbol_index: dict[str, list[dict]],
    ) -> list[dict]:
        links = []

        for node in nodes:
            if node.get("node_kind") != "method":
                continue

            method_name = node["node_name"]
            method_id = node["node_id"]

            for used in node.get("symbols_used", []):
                symbol = used.split(".")[-1]
                candidates = symbol_index.get(symbol)

                if not candidates:
                    continue

                for parent in candidates:
                    if parent.get("node_kind") != "method":
                        continue

                    if parent["node_name"] != method_name:
                        continue

                    links.append({
                        "from": method_id,
                        "to": parent["node_id"],
                        "type": "OVERRIDES",
                        "props": {
                            "confidence": 0.8,
                            "source": "semantic_linker:v1",
                            "created_at": time.time(),
                        },
                    })

        return links


    # -------------------------
    # HELPERS
    # -------------------------
    def _normalize_symbol(self, symbol: str) -> str:
        """
        Normalizes symbols like:
        - self.foo -> foo
        - Class.method -> method
        - module.func -> func
        """
        return symbol.split(".")[-1].strip()

    def _select_best_candidate(
        self,
        candidates: List[dict],
        allowed_kinds: set,
    ) -> dict | None:
        """
        Picks the first compatible candidate.
        Deterministic and safe.
        """
        for node in candidates:
            if node.get("node_kind") in allowed_kinds:
                return node
        return None

    def _dedupe(self, links: list[dict]) -> list[dict]:
        seen = set()
        unique = []

        for l in links:
            key = (l["from"], l["to"], l["type"])
            if key in seen:
                continue
            seen.add(key)
            unique.append(l)

        return unique

