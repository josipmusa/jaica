import json
import re

from ollama import chat, generate

from src.app.dtos.graph import GraphQueryPlan
from src.app.dtos.intent import Intent
from src.app.configuration.config import (MAIN_LLM_MODEL, INTENT_CLASSIFIER_SYSTEM_PROMPT, DEFAULT_SYSTEM_PROMPT,
                                          GRAPH_SYMBOL_EXTRACTION_SYSTEM_PROMPT, TEST_ANALYSIS_EXTRACTION_SYSTEM_PROMPT,
                                          TEST_ANALYSIS_SYSTEM_PROMPT)
from src.app.dtos.test import TestAnalysisExtractedEntities, TestGapFinding


def general_model_chat(prompt: str, system_prompt: str = DEFAULT_SYSTEM_PROMPT) -> str:
    try :
        answer = chat(model=MAIN_LLM_MODEL, messages=[
            {"role": "system", "content": system_prompt},
            {'role': 'user', 'content': prompt}
        ])
        return answer.message.content
    except Exception:
        return "Error generating answer, try again later"

def classify_intent(prompt: str) -> Intent:
    llm_response = chat(model=MAIN_LLM_MODEL, messages=[
        {"role": "system", "content": INTENT_CLASSIFIER_SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
    ])

    label = llm_response.message.content.strip().upper().replace('"', '')
    intent = Intent.from_str(label)
    if intent is None:
        intent = Intent.GENERAL

    return intent

def extract_class_method(prompt: str) -> TestAnalysisExtractedEntities | None:
    llm_response = chat(
        model=MAIN_LLM_MODEL,
        messages=[
            {"role": "system", "content": TEST_ANALYSIS_EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
    )

    raw = llm_response.message.content.strip()
    raw = re.sub(r"^```json\s*|\s*```$", "", raw, flags=re.IGNORECASE).strip()

    raw = _extract_json_object(raw)
    if not raw:
        return None

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None

    try:
        return TestAnalysisExtractedEntities.model_validate(data)
    except Exception:
        return None


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

def analyze_test_gaps(findings: list[TestGapFinding], prompt: str) -> str:
    formatted_findings = _format_test_findings(findings)
    modified_prompt = f"""
User question:
{prompt}

Identified test gaps:
{formatted_findings}
"""
    return general_model_chat(prompt=modified_prompt, system_prompt=TEST_ANALYSIS_SYSTEM_PROMPT)

def _extract_json_object(raw: str) -> str | None:
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None
    return raw[start:end + 1]

def _format_test_findings(findings: list[TestGapFinding]) -> str:
    lines = []
    for f in findings:
        lines.append(
            f"""- Method: {f.method_name} (Class: {f.class_name or "module-level"})
      Reasons:
      - {chr(10).join(f.reasons)}
      Suggested focus: {f.suggested_focus or "N/A"}"""
        )
    return "\n".join(lines)