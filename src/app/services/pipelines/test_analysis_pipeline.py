from typing import Optional, List

from src.app.dtos.chat import ChatRequest
from src.app.dtos.test import TestGapFinding
from src.app.services.code_analysis_service import CodeAnalysisService
from src.app.services.file_metadata_service import is_file_recently_modified
from src.app.services.graph_db_service import GraphDBService
from src.app.services.llm_service import extract_class_method


class TestAnalysisPipeline:
    def __init__(self, graph_db_service: GraphDBService, code_analysis_service: CodeAnalysisService):
        self.graph_db_service = graph_db_service
        self.code_analysis_service = code_analysis_service

    #TODO add LLM reasoning with the current response from this method and return that reasoning as the result of the pipeline
    def run(self, chat_request: ChatRequest) -> List[TestGapFinding]:
        if chat_request.project_name is None:
            print(f"Project name is required for test analysis pipeline")

        extracted_entities = extract_class_method(chat_request.prompt)
        if extracted_entities.class_name is None and extracted_entities.method_name is None:
            return []

        findings: List[TestGapFinding] = []

        # Resolve class if only method is given
        class_to_check = extracted_entities.class_name
        if extracted_entities.method_name and not extracted_entities.class_name:
            class_to_check = self.graph_db_service.find_class_for_method(extracted_entities.method_name, chat_request.project_name)

            if class_to_check is None:
                # Try to find module-level function/method node in graph
                node_info = self.graph_db_service.find_method_or_function_node(extracted_entities.method_name, chat_request.project_name)
                if node_info is None:
                    return []  # Nothing found
                # Use node_info to fill methods_info for scoring
                methods_info = [{
                    "class_name": node_info.get("class_name"),  # might be None
                    "method_name": node_info["method_name"],
                    "file_path": node_info.get("file_path")
                }]
            else:
                methods_info = self.graph_db_service.list_methods(
                    class_to_check,
                    chat_request.project_name
                )
                methods_info = [
                    m for m in methods_info
                    if m["method_name"] == extracted_entities.method_name
                ]
        else:
            # Get methods with file paths
            methods_info = self.graph_db_service.list_methods(class_to_check, chat_request.project_name)
            if extracted_entities.method_name:
                methods_info = [m for m in methods_info if m["method_name"] == extracted_entities.method_name]

        if not methods_info:
            return []  # No matching methods found

        for m_info in methods_info:
            cls = m_info.get("class_name")
            method = m_info["method_name"]
            file_path = m_info.get("file_path")

            score = 0
            reasons = []

            # External calls
            if self.graph_db_service.is_method_called_externally(cls, method):
                score += 1
                reasons.append("Method/function is called from outside the class/module")

            # Static analysis using actual code from file
            test_code_analysis_result = self.code_analysis_service.analyze_code_for_tests(file_path, cls, method)

            if test_code_analysis_result.long_function:
                score += 1
                reasons.append("Long function detected")
            if test_code_analysis_result.deep_nesting:
                score += 1
                reasons.append("Deep nesting detected")
            if test_code_analysis_result.many_params:
                score += 1
                param_count = test_code_analysis_result.param_count
                reasons.append(
                    f"{param_count} parameters detected" if param_count is not None
                    else "Many parameters detected"
                )

            # File metadata (only if file exists)
            if file_path and is_file_recently_modified(file_path):
                score += 1
                reasons.append("Recently modified file")

            # Class collaborators (only if class)
            if cls and self.graph_db_service.get_class_collaborator_count(cls) > 3:
                score += 1
                reasons.append("Class has many collaborators")

            # Threshold to flag missing tests
            if score >= 2:
                suggested_focus = self.suggest_focus(cls, method)
                findings.append(TestGapFinding(
                    class_name=cls,
                    method_name=method,
                    reasons=reasons,
                    priority=score,
                    suggested_focus=suggested_focus
                ))

        return findings if findings else None

    def suggest_focus(self, class_name: Optional[str], method_name: str) -> Optional[str]:
        deps = self.graph_db_service.get_method_dependencies(class_name, method_name)
        if deps:
            return f"Consider mocking: {', '.join(deps)}"
        return None
