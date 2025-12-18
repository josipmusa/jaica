from src.app.dtos.chat import PromptRequest
from src.app.services.pipelines.graph_pipeline import GraphReasoningPipeline
from src.app.services.pipelines.rag_pipeline import RagPipeline
from src.app.services.llm_service import general_model_chat
from src.app.configuration.config import HYBRID_SYSTEM_PROMPT


class HybridPipeline:
    def __init__(self, rag_pipeline: RagPipeline, graph_pipeline: GraphReasoningPipeline):
        self.rag_pipeline = rag_pipeline
        self.graph_pipeline = graph_pipeline

    def run(self, prompt_request: PromptRequest) -> str:
        graph_context = self.graph_pipeline.run(prompt_request)
        rag_context = self.rag_pipeline.run(prompt_request)

        combined_prompt = f"""
        User question:
        {prompt_request.prompt}

        Code structure and relationships (graph reasoning):
        {graph_context}

        Relevant semantic context (vector retrieval):
        {rag_context}

        Using the information above, answer the user's question.
        Focus on correctness, clarity, and actionable insights.
        Do not mention the code or the fact that it was provided to you; just answer concisely and authoritatively.
        """

        return general_model_chat(prompt=combined_prompt, system_prompt=HYBRID_SYSTEM_PROMPT)
