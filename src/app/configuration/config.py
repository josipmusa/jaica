from pathlib import Path

CODE_CLASSIFIER_MODEL_URL = "https://huggingface.co/josipmusa/code-classifier/resolve/main/code_classifier.onnx"
CODE_CLASSIFIER_LABEL_URL = "https://huggingface.co/josipmusa/code-classifier/resolve/main/labels.json"
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
VECTORSTORE_PATH = PROJECT_ROOT / "vectorstore"
MAIN_LLM_MODEL = 'qwen2.5:3b-instruct'
DEFAULT_SYSTEM_PROMPT = """
You are a helpful and concise AI assistant. 
Always provide accurate and clear answers. 
Do not make up facts; if you do not know the answer, say "I don't know."
Answer in a friendly and professional tone.
Tailor your response to the user's intent as efficiently as possible.
"""
CLASSIFIER_SYSTEM_PROMPT = """
You are a routing classifier for a coding assistant.
Given a user prompt, classify it into exactly one of the following categories:

1. CODE_REASONING
   For questions about how code works, causes of errors, data flow, type resolution,
   relationships between classes/functions/modules, behaviors, or dependency chains.

2. CODE_RETRIEVAL
   When the user wants to see the full contents of a file, snippet, codebase file,
   class, method, module, or specific source.

3. DOCS_RETRIEVAL
   When the user asks about documentation, README content, ADRs,
   comments, or high-level descriptions.

4. HYBRID
   When the user wants a deep reasoned explanation AND raw code is needed
   (ex: bug explanations, multi-file reasoning, mixed tasks).

5. GENERAL
   When the question is general programming knowledge or does not require retrieving code.

Respond with ONLY the label. No explanations. No punctuation.
"""