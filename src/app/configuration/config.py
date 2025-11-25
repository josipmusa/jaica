from pathlib import Path

BUG_CLASSIFIER_MODEL_URL = "https://huggingface.co/josipmusa/bug-classifier/resolve/main/bug_classifier.onnx"
BUG_CLASSIFIER_LABEL_URL = "https://huggingface.co/josipmusa/bug-classifier/resolve/main/labels.json"
CODE_CLASSIFIER_MODEL_URL = "https://huggingface.co/josipmusa/code-classifier/resolve/main/code_classifier.onnx"
CODE_CLASSIFIER_LABEL_URL = "https://huggingface.co/josipmusa/code-classifier/resolve/main/labels.json"
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
VECTORSTORE_PATH = PROJECT_ROOT / "vectorstore"