import os
import sys
import requests
import time
from dotenv import load_dotenv
from google import genai
from google.api_core.exceptions import GoogleAPIError

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODELS = os.getenv("GEMINI_MODELS", "")


def prompt_model(model: str, prompt: str) -> str:
    """
    Prompt the model provided with the prompt given as the argument.

    returns an output string containing the model's response.
    """

    if model in GEMINI_MODELS:
        return prompt_gemini(model, prompt)

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0, "num_ctx": 4096, "num_predict": 1024},
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
        "total_time": data["total_duration"] / 1000000,
    }


def prompt_gemini(model_name: str, prompt: str) -> str:
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
        # genai.configure(api_key=API_KEY)
        # model = genai.GenerativeModel(model_name)
        # start = time.perf_counter()
        # response = model.generate_content(prompt)
        # end = time.perf_counter()
        if __name__ == "__main__":
            print("\n--- RESPONSE ---\n")
        return {
            "model": response.model_version,
            "response": response.text,
            "tokens_used": response.usage_metadata.total_token_count,
            "total_time": (end - start) * 1000,
        }

    except GoogleAPIError as e:
        return f"[Gemini Error]: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"


def main() -> None:
    """
    Execute the program.
    """
    models = [
        "llama3.1",
        "phi3",
        "deepseek-r1:1.5b",
        "gemma3",
        "qwen2.5-coder",
        "gemini-2.5-flash",
        "gemini-3-flash-preview",
    ]
    if len(sys.argv) != 3:
        print("Usage: uv run prompt_model.py <model> <prompt>")
        return
    try:
        model = sys.argv[1]
        prompt = sys.argv[2]

        if model not in models:
            raise ValueError(f"Invalid model provided!\nModels available: {models}")

        output = prompt_model(model, prompt)

        print(output["response"])
        if __name__ != "__main__":
            print(
                f"Total tokens used: {output['tokens_used']}, took {output['total_time']}ms"
            )
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
