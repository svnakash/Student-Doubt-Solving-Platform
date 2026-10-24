import json
import os
from urllib import error, request


def get_ai_settings() -> dict:
    """Read AI settings from environment variables."""
    return {
        "enabled": os.getenv("AI_ENABLED", "false").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        },
        "api_key": (os.getenv("AI_API_KEY") or "").strip(),
        "base_url": (os.getenv("AI_API_BASE_URL") or "https://api.openai.com/v1").rstrip("/"),
        "model": (os.getenv("AI_MODEL") or "gpt-4o-mini").strip(),
        "timeout": int(os.getenv("AI_TIMEOUT_SECONDS") or "20"),
    }


def generate_ai_answer_for_question(question) -> dict:
    """Generate an answer for a question using an OpenAI-compatible API."""
    settings = get_ai_settings()

    if not settings["enabled"]:
        return {
            "success": False,
            "code": "AI_NOT_CONFIGURED",
            "message": "AI answer generation is not enabled.",
        }

    if not settings["api_key"]:
        return {
            "success": False,
            "code": "AI_API_KEY_MISSING",
            "message": "The AI provider API key is not configured.",
        }

    prompt = (
        "You are a helpful academic assistant for a student support platform. "
        "Answer only using the question provided and avoid making up facts. "
        "If the question is unclear, ask for clarification instead of guessing.\n\n"
        f"Subject: {question.subject}\n"
        f"Title: {question.title}\n"
        f"Question: {question.body}"
    )

    payload = {
        "model": settings["model"],
        "temperature": 0.2,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a grounded academic assistant. Give concise, helpful guidance "
                    "for students. Be truthful and avoid unsupported claims."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings['api_key']}",
    }

    url = f"{settings['base_url']}/chat/completions"
    request_body = json.dumps(payload).encode("utf-8")

    try:
        req = request.Request(url, data=request_body, headers=headers, method="POST")
        with request.urlopen(req, timeout=settings["timeout"]) as response:
            response_data = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        try:
            error_body = exc.read().decode("utf-8")
            message = json.loads(error_body).get("error", {}).get("message", str(exc))
        except Exception:
            message = str(exc)

        return {
            "success": False,
            "code": "AI_PROVIDER_ERROR",
            "message": f"The AI provider rejected the request: {message}",
        }
    except Exception as exc:
        return {
            "success": False,
            "code": "AI_UNAVAILABLE",
            "message": "AI answer generation is temporarily unavailable.",
        }

    try:
        answer = response_data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError, ValueError):
        return {
            "success": False,
            "code": "AI_RESPONSE_INVALID",
            "message": "The AI provider returned an invalid response.",
        }

    if not answer:
        return {
            "success": False,
            "code": "AI_RESPONSE_EMPTY",
            "message": "The AI provider returned an empty answer.",
        }

    return {
        "success": True,
        "answer": answer,
    }
