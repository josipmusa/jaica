from typing import List

from src.app.dtos.chat import PromptRequest
from src.app.dtos.graph import GraphQueryPlan
from src.app.services.graph_db_service import GraphDBService
from src.app.services.llm_service import extract_graph_query_plan, general_model_chat


class GraphReasoningPipeline:
    def __init__(self, graph_db_service: GraphDBService):
        self.graph_db_service = graph_db_service

    def run(self, prompt_request: PromptRequest) -> str:
        plan = extract_graph_query_plan(prompt_request.prompt)

        if not plan:
            return "I couldn't identify a code-related question."

        nodes = self._resolve_nodes(
            symbols=plan.symbols,
            project_name=prompt_request.project_name,
        )

        if not nodes:
            return "No matching symbols were found in the codebase."

        contexts = self._traverse(nodes, plan)

        return self._reason(prompt_request.prompt, contexts)

    def _resolve_nodes(self, symbols: List[str], project_name: str) -> List[dict]:
        resolved = []

        for symbol in symbols:
            print(f"DEBUG: Looking for symbol='{symbol}' in project='{project_name}'")
            nodes = self.graph_db_service.find_nodes_by_name(
                name=symbol,
                project_name=project_name,
                limit=3,
            )
            print(f"DEBUG: Found {len(nodes)} nodes")
            resolved.extend(nodes)

        return resolved

    def _traverse(self, nodes: List[dict], plan: GraphQueryPlan) -> List[str]:
        contexts = []

        for node in nodes:
            related = self.graph_db_service.traverse(
                node_id=node["node_id"],
                operation=plan.operation,
                max_depth=10,
            )

            context = self._format_context(
                node=node,
                related_nodes=related,
                operation=plan.operation,
            )
            contexts.append(context)

        return contexts

    def _format_context(self, node: dict, related_nodes: List[dict], operation) -> str:
        lines = []

        lines.append(f"Symbol: {node['node_name']} ({node['node_type']})")
        lines.append(f"Defined in: {node['file_path']}:{node['start_line']}")

        if not related_nodes:
            lines.append("\nNo related nodes found.")
            return "\n".join(lines)

        lines.append(f"\n{operation.value.replace('_', ' ').title()}:")

        for rel in related_nodes:
            lines.append(
                f"- {rel['node_name']} ({rel['node_type']}) "
                f"in {rel['file_path']}:{rel['start_line']}"
            )

        return "\n".join(lines)

    def _reason(self, user_prompt: str, contexts: List[str]) -> str:
            prompt = f"""
    You are a senior software engineer analyzing a codebase.

    User question:
    {user_prompt}

    Relevant code structure:
    {chr(10).join(contexts)}

    Answer clearly and concisely.
    """
            return general_model_chat(prompt)