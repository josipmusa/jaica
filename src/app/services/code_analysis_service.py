import re
from pathlib import Path
from typing import List, Optional, Dict

from src.app.dtos.issue import Issue, IssueType
from src.app.dtos.test import TestCodeAnalysisResult
from src.app.models.code_classifier.code_classifier import CodeClassifier
from src.app.services.detectors.java.java_detector import analyze_java
from src.app.services.detectors.python.python_detector import analyze_python
from src.app.services.file_metadata_service import extract_python_code, extract_java_code


class CodeAnalysisService:
    def __init__(self, code_classifier: CodeClassifier):
        self.code_classifier = code_classifier

    def analyze_code_for_tests(self, file_path: str, class_name: Optional[str] = None, method_name: Optional[str] = None) -> TestCodeAnalysisResult:
        file_path = Path(file_path)
        try:
            code = file_path.read_text(encoding="utf-8")
        except Exception:
            return TestCodeAnalysisResult(deep_nesting=False, long_function=False, many_params=False)

        if method_name:
            if file_path.suffix == ".py":
                code = extract_python_code(code, method_name, class_name)
            elif file_path.suffix == ".java":
                code = extract_java_code(code, method_name, class_name)
            else:
                return TestCodeAnalysisResult(deep_nesting=False, long_function=False, many_params=False)

        issues = self.analyze_raw_code(code)

        long_function, deep_nesting, many_params = False, False, False
        param_count = None

        for issue in issues:
            if issue.type == IssueType.LONG_FUNCTION:
                long_function = True
            elif issue.type == IssueType.DEEP_NESTING:
                deep_nesting = True
            elif issue.type == IssueType.MANY_PARAMS:
                many_params = True
                # Extract param count from message like "Function has too many parameters (5)."
                match = re.search(r"\((\d+)\)", issue.message)
                if match:
                    param_count = int(match.group(1))
                else:
                    param_count = None

        return TestCodeAnalysisResult(deep_nesting=deep_nesting, long_function=long_function, many_params=many_params, param_count=param_count)


    def analyze_raw_code(self, code) -> List[Issue]:
        language = self.code_classifier.predict(code).lower()

        if language == "python":
            issues = analyze_python(code)
        elif language == "java":
            issues = analyze_java(code)
        else:
            return []

        return issues