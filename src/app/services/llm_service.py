import json
import re

from ollama import chat, generate

from src.app.dtos.graph import GraphQueryPlan
from src.app.dtos.intent import Intent
from src.app.configuration.config import MAIN_LLM_MODEL, CLASSIFIER_SYSTEM_PROMPT, DEFAULT_SYSTEM_PROMPT, GRAPH_SYMBOL_EXTRACTION_SYSTEM_PROMPT

def general_model_chat(prompt: str, system_prompt: str = DEFAULT_SYSTEM_PROMPT) -> str:
    try :
        answer = chat(model=MAIN_LLM_MODEL, messages=[
            {"role": "system", "content": system_prompt},
            {'role': 'user', 'content': prompt}
        ])
        return answer.message.content
    except Exception:
        return "Error generating answer, try again later"

def ask(prompt) -> str:
    answer = generate(model=MAIN_LLM_MODEL, prompt=prompt)
    return answer.response

def classify(prompt: str) -> Intent:
    llm_response = chat(model=MAIN_LLM_MODEL, messages=[
        {"role": "system", "content": CLASSIFIER_SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
    ])

    label = llm_response.message.content.strip().upper().replace('"', '')
    intent = Intent.from_str(label)
    if intent is None:
        intent = Intent.GENERAL

    return intent


def extract_graph_query_plan(prompt: str) -> GraphQueryPlan | None:
    llm_response = chat(
        model=MAIN_LLM_MODEL,
        messages=[
            {"role": "system", "content": GRAPH_SYMBOL_EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ])

    raw = llm_response.message.content.strip()
    raw = re.sub(r"^```json\s*|\s*```$", "", raw, flags=re.IGNORECASE).strip()

    raw = _extract_json_object(raw)
    if not raw:
        return None

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None

    if not data.get("symbols"):
        return None

    if "operation" in data:
        data["operation"] = data["operation"].lower()

    try:
        return GraphQueryPlan.model_validate(data)
    except Exception:
        return None


def summarize_code(code: str) -> str:
    prompt = f"""
You are a helpful programming assistant.
Summarize the following code in 1-2 sentences, focusing on its purpose and functionality:
{code}
Summary:"""
    try:
        answer = generate(model=MAIN_LLM_MODEL, prompt=prompt)
        summary = answer.response.strip()
        return summary
    except Exception as e:
        print(f"Error summarizing code: {e}")
        return "Unable to summarize"

def _extract_json_object(raw: str) -> str | None:
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None
    return raw[start:end + 1]