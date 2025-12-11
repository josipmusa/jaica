from ollama import chat, generate

from src.app.dtos.intent import Intent
from src.app.configuration.config import MAIN_LLM_MODEL, CLASSIFIER_SYSTEM_PROMPT, DEFAULT_SYSTEM_PROMPT

def general_model_chat(prompt: str) -> str:
    try :
        answer = chat(model=MAIN_LLM_MODEL, messages=[
            {"role": "system", "content": DEFAULT_SYSTEM_PROMPT},
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

    print(f"Intent is {intent}")
    return intent

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