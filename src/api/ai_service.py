"""
Servicio de IA con cadena de fallback: Groq -> Groq2 -> Gemini -> Mistral.
Mantiene la misma lógica que el Apps Script original: si un proveedor falla,
pasa automáticamente al siguiente para que la generación nunca se caiga.
"""
import os
import json
import requests

# Timeout por proveedor (segundos)
TIMEOUT = 60

SYSTEM_PROMPT = (
    "You are Lumi, an expert pedagogical lesson designer. "
    "You MUST respond with ONLY valid JSON (an array of session objects), "
    "no markdown, no code fences, no extra text before or after. "
    "Follow the user's schema and rules exactly."
)


def _extract_text(data, provider):
    """Extrae el texto de la respuesta según el proveedor."""
    try:
        if provider in ("groq", "groq2", "mistral"):
            return data["choices"][0]["message"]["content"]
        if provider == "gemini":
            return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return None
    return None


def _call_groq(prompt, api_key, model):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 8000,
        "response_format": {"type": "json_object"},
    }
    r = requests.post(url, headers=headers, json=payload, timeout=TIMEOUT)
    r.raise_for_status()
    return _extract_text(r.json(), "groq")


def _call_gemini(prompt, api_key, model):
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {"parts": [{"text": f"{SYSTEM_PROMPT}\n\n{prompt}"}]}
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 8000,
            "responseMimeType": "application/json",
        },
    }
    r = requests.post(url, headers=headers, json=payload, timeout=TIMEOUT)
    r.raise_for_status()
    return _extract_text(r.json(), "gemini")


def _call_mistral(prompt, api_key, model):
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 8000,
        "response_format": {"type": "json_object"},
    }
    r = requests.post(url, headers=headers, json=payload, timeout=TIMEOUT)
    r.raise_for_status()
    return _extract_text(r.json(), "mistral")


def generate_with_fallback(prompt):
    """
    Recorre los proveedores en orden. Devuelve (text, provider_used, errores).
    Si todos fallan, text = None.
    """
    groq_key = os.environ.get("GROQ_API_KEY")
    groq_key2 = os.environ.get("GROQ_API_KEY_2")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    mistral_key = os.environ.get("MISTRAL_API_KEY")

    groq_model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
    gemini_model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    mistral_model = os.environ.get("MISTRAL_MODEL", "mistral-large-latest")

    # (nombre, función, condición de que exista la key)
    chain = [
        ("groq",   lambda: _call_groq(prompt, groq_key, groq_model),    bool(groq_key)),
        ("groq2",  lambda: _call_groq(prompt, groq_key2, groq_model),   bool(groq_key2)),
        ("gemini", lambda: _call_gemini(prompt, gemini_key, gemini_model), bool(gemini_key)),
        ("mistral", lambda: _call_mistral(prompt, mistral_key, mistral_model), bool(mistral_key)),
    ]

    errors = []
    for name, fn, has_key in chain:
        if not has_key:
            errors.append(f"{name}: sin API key configurada")
            continue
        try:
            text = fn()
            if text and str(text).strip():
                return text, name, errors
            errors.append(f"{name}: respuesta vacía")
        except requests.exceptions.HTTPError as e:
            errors.append(f"{name}: HTTP {e.response.status_code}")
        except Exception as e:
            errors.append(f"{name}: {str(e)}")

    return None, None, errors