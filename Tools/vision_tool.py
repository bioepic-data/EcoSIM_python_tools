import requests
import base64
import sys
import json


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def query_qwen_vision(image_path, prompts, model="qwen2.5vl:7b"):
    if isinstance(prompts, str):
        prompts = [prompts]

    base64_image = encode_image(image_path)
    results = {}

    for prompt in prompts:
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                    "images": [base64_image],
                }
            ],
            "stream": False,
        }

        response = requests.post(
            "http://localhost:11434/api/chat",
            json=payload,
            timeout=300,
        )
        response.raise_for_status()
        data = response.json()
        results[prompt] = data["message"]["content"]

    return results


if __name__ == "__main__":
    # Usage:
    # python vision_tool.py path/to/image.png "What text is in this image?" "Describe the chart." "Is there a table?"
    if len(sys.argv) < 3:
        print(
            'Usage: python vision_tool.py path/to/image.png "query1" "query2" ...',
            file=sys.stderr,
        )
        sys.exit(1)

    path = sys.argv[1]
    queries = sys.argv[2:]

    try:
        answers = query_qwen_vision(path, queries)
        print(json.dumps(answers, indent=2, ensure_ascii=False))
    except requests.RequestException as e:
        print(f"Request failed: {e}", file=sys.stderr)
        sys.exit(2)
    except KeyError:
        print("Unexpected response format from Ollama API.", file=sys.stderr)
        sys.exit(3)