from src.app.models.code_classifier.code_classifier import CodeClassifier
from src.app.services.detectors.java.java_detector import analyze_java
from src.app.services.detectors.python.python_detector import analyze_python

class CodeAnalyzer:
    def __init__(self, code_classifier: CodeClassifier):
        self.code_classifier = code_classifier

    def analyze(self, code):
        language = self.code_classifier.predict(code).lower()

        if language == "python":
            issues = analyze_python(code)
        elif language == "java":
            issues = analyze_java(code)
        else:
            return []

        return issues
