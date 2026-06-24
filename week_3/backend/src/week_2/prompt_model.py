import os
import sys
import requests
import time
import ollama
from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODELS = os.getenv("GEMINI_MODELS", "")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

def prompt_model(model: str, prompt: str, images=None) -> str:
    """
    Prompt the model provided with the prompt given as the argument.

    returns an output string containing the model's response.
    """

    if model in GEMINI_MODELS:
        return prompt_gemini(model, prompt, images)

    try:
        try:
            models = ollama.list()
        except Exception:
            raise ValueError(
                "Ollama is not running or unavailable. Start with: "
                "docker compose --profile ollama up"
            )

        models = [model.model.replace(":latest", "") for model in models.models]
        if model not in models:
            raise ValueError(f"Invalid model provided!\nOllama models available: {models}")

        url = f"{OLLAMA_HOST}/api/generate"
        response = requests.post(
            url,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "images": images or [],
                "options": {
                    "temperature": 0,
                    "top_k": 20,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1,
                    "num_ctx": 2048,
                    "num_predict": 1024
                    },
            },
            timeout=60,
        )
        # raises exceptions on HTTP status
        response.raise_for_status()
        data = response.json()

        if __name__ == "__main__":
            print("\n--- RESPONSE ---\n")
        return {
            "model": model,
            "response": data["response"],
            "tokens_used": data["prompt_eval_count"] + data["eval_count"],
            "total_time": round(data["total_duration"] / 1000000, 3),
        }
    except Exception as e:
        return f"An unexpected error occurred while running ollama: {e}"


def prompt_gemini(model_name: str, prompt: str, images=None) -> str:
    """
    Prompt the Gemini model with the given prompt.

    returns an output string containing the model's response.
    """
    if not API_KEY:
        return "Error: GEMINI_API_KEY environment variable not set."

    try:
        client = genai.Client(api_key=API_KEY)

        start = time.perf_counter()
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        end = time.perf_counter()
        print(response)
        if __name__ == "__main__":
            print("\n--- RESPONSE ---\n")
        return {
            "model": response.model_version,
            "response": response.text,
            "tokens_used": response.usage_metadata.total_token_count,
            "total_time": round((end - start) * 1000, 3),
        }
    except Exception as e:
        return f"An unexpected error occurred [Gemini Error]: {e}"


def main() -> None:
    """
    Execute the program.
    """

    if len(sys.argv) != 3:
        print("Usage: uv run prompt_model.py <model> <prompt>")
        return
    try:
        model = sys.argv[1]
        prompt = sys.argv[2]
        output = prompt_model(model, prompt)
        
        if isinstance(output, dict):
            print(output["response"])
        else:
            print(output)
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
