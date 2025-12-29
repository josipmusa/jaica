import json
from typing import List, Tuple, Optional

from src.app.dtos.chat import ChatRequest, DependencyGraph, DependencyEdge, ContentChunk, MetadataChunk
from src.app.dtos.graph import GraphQueryPlan
from src.app.dtos.intent import Intent
from src.app.services.graph_db_service import GraphDBService
from src.app.services.llm_service import extract_graph_query_plan, general_model_chat, general_model_chat_stream

UI_MAX_EDGES_PER_NODE=5

class GraphReasoningPipeline:
    def __init__(self, graph_db_service: GraphDBService):
        self.graph_db_service = graph_db_service

    def run(self, chat_request: ChatRequest):
        plan = extract_graph_query_plan(chat_request.prompt)

        # Not a graph question
        if not plan:
            content_chunk = ContentChunk(content="Sorry, I can't answer that question")
            yield json.dumps(content_chunk.model_dump(by_alias=True, exclude_none=False)) + "\n"
            return

        nodes = self._resolve_nodes(
            symbols=plan.symbols,
            project_name=chat_request.project_name,
        )

        # Graph question, but no symbols resolved
        if not nodes:
            content_chunk = ContentChunk(content="Sorry, I can't answer that question")
            yield json.dumps(content_chunk.model_dump(by_alias=True, exclude_none=False)) + "\n"
            return

        contexts, dependency_graph = self._traverse(nodes, plan)

        # No graph edges worth showing
        if not dependency_graph or not dependency_graph.edges:
            content_chunk = ContentChunk(content="Sorry, I can't answer that question")
            yield json.dumps(content_chunk.model_dump(by_alias=True, exclude_none=False)) + "\n"
            return

        metadata_chunk = MetadataChunk(
            intent=Intent.CODE_GRAPH_REASONING,
            dependencyGraph=dependency_graph
        )
        yield json.dumps(metadata_chunk.model_dump(by_alias=True, exclude_none=False)) + "\n"

        graph_prompt = self._get_graph_prompt(chat_request.prompt, contexts)
        for chunk in general_model_chat_stream(graph_prompt):
            content_chunk = ContentChunk(content=chunk)
            yield json.dumps(content_chunk.model_dump(by_alias=True, exclude_none=False)) + "\n"

    def run_for_hybrid(self, chat_request: ChatRequest) -> Tuple[Optional[str], Optional[DependencyGraph]]:
        plan = extract_graph_query_plan(chat_request.prompt)

        # Not a graph question
        if not plan:
            return None, None

        nodes = self._resolve_nodes(
            symbols=plan.symbols,
            project_name=chat_request.project_name,
        )

        # Graph question, but no symbols resolved
        if not nodes:
            return None, None

        contexts, dependency_graph = self._traverse(nodes, plan)

        # No graph edges worth showing
        if not dependency_graph or not dependency_graph.edges:
            return None, None

        graph_prompt = self._get_graph_prompt(chat_request.prompt, contexts)
        answer = general_model_chat(graph_prompt)

        return answer, dependency_graph

    def _resolve_nodes(self, symbols: List[str], project_name: str) -> List[dict]:
        resolved = []

        for symbol in symbols:
            nodes = self.graph_db_service.find_nodes_by_name(
                name=symbol,
                project_name=project_name,
                limit=3,
            )
            resolved.extend(nodes)

        return resolved

    def _traverse(
            self,
            nodes: List[dict],
            plan: GraphQueryPlan,
    ) -> Tuple[List[str], DependencyGraph]:

        contexts: List[str] = []
        edges: List[DependencyEdge] = []
        used_nodes = set()

        for node in nodes:
            source_name = node["node_name"]
            used_nodes.add(source_name)

            related = self.graph_db_service.traverse(
                node_id=node["node_id"],
                operation=plan.operation,
                max_depth=10,  # deep for reasoning
            )

            # Limit graph expansion for UI
            graph_related = related[:UI_MAX_EDGES_PER_NODE]

            for rel in graph_related:
                target_name = rel["node_name"]
                used_nodes.add(target_name)

                edges.append(
                    DependencyEdge(
                        from_=source_name,
                        to=target_name,
                    )
                )

            # Full context still uses all related nodes
            contexts.append(
                self._format_context(
                    node=node,
                    related_nodes=related,
                    operation=plan.operation,
                )
            )

        # Deduplicate edges
        edges = list({(e.from_, e.to): e for e in edges}.values())

        graph = DependencyGraph(
            nodes=sorted(used_nodes),
            edges=edges,
            description=f"{plan.operation.value.replace('_', ' ').title()} relationships",
        )

        return contexts, graph

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


    def _get_graph_prompt(self, user_prompt: str, contexts: List[str]):
        prompt = f"""
User question:
{user_prompt}

Code information:
{chr(10).join(contexts)}

Answer the user's question using the provided code information. 
Do not mention the code or the fact that it was provided to you; just answer concisely and authoritatively.
    """
        return prompt
