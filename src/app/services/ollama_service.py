from ollama import chat, generate

from src.app.models.chat import ChatRequest, TaskType

MODEL_NAME = 'qwen2.5:3b-instruct'

def model_chat(chat_request: ChatRequest) -> str:
    prompt = chat_request.prompt
    if chat_request.task_type is not None:
        prompt = _format_prompt(prompt, chat_request.task_type)

    try :
        answer = chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': prompt}])
        return answer.message.content
    except Exception:
        return "Error generating answer, try again later"

def ask(prompt) -> str:
    answer = generate(model=MODEL_NAME, prompt=prompt)
    return answer.response

def _format_prompt(prompt: str, task_type: TaskType):
    return f"Task: {task_type.value}\n User prompt:\n{prompt}"