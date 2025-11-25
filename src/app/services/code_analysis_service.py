from src.app.dtos.issue import Issue, Severity
from src.app.models.bug_classifier.bug_classifier import BugClassifier
from src.app.models.code_classifier.code_classifier import CodeClassifier
from src.app.services.detectors.java.java_detector import analyze_java
from src.app.services.detectors.python.python_detector import analyze_python

class CodeAnalyzer:
    def __init__(self, bug_classifier: BugClassifier, code_classifier: CodeClassifier):
        self.bug_classifier = bug_classifier
        self.code_classifier = code_classifier

    def analyze(self, code):
        language = self.code_classifier.predict(code).lower()

        if language == "python":
            issues = analyze_python(code)
        elif language == "java":
            issues = analyze_java(code)
        else:
            return []

        output = self._analyze_semantic_bug(code)
        if output is not None:
            issues.append(output)

        return issues

    def _analyze_semantic_bug(self, code) -> Issue | None:
        predicted_label, confidence, line_number = self.bug_classifier.predict(code)

        if predicted_label != "CLEAN":
            semantic_issue = Issue(
                type=predicted_label,
                message=f"Possible {predicted_label} issue in your code",
                severity=Severity.HIGH,
                confidence=confidence,
                line_start=line_number
            )
            return semantic_issue

        return None
