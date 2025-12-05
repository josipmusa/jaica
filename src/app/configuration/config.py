from pathlib import Path

CODE_CLASSIFIER_MODEL_URL = "https://huggingface.co/josipmusa/code-classifier/resolve/main/code_classifier.onnx"
CODE_CLASSIFIER_LABEL_URL = "https://huggingface.co/josipmusa/code-classifier/resolve/main/labels.json"
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
VECTORSTORE_PATH = PROJECT_ROOT / "vectorstore"