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


# Límite de tokens por minuto del plan gratis de Groq (gpt-oss-120b = 8000).
# Groq rechaza (429) si entrada + max_tokens supera ese límite, aunque no hayas usado nada,
# así que max_tokens se ajusta al tamaño del prompt.
GROQ_TPM = int(os.environ.get("GROQ_TPM", "8000"))
GROQ_MAX_OUTPUT = 4000
GROQ_MIN_OUTPUT = 2500


def _estimate_tokens(text):
    # Aproximación: ~3.5 caracteres por token (español/inglés mezclado)
    return int(len(text or "") / 3.5) + 1


def _call_groq(prompt, api_key, model):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    est_input = _estimate_tokens(SYSTEM_PROMPT) + _estimate_tokens(prompt)
    max_out = max(GROQ_MIN_OUTPUT, min(GROQ_MAX_OUTPUT, GROQ_TPM - est_input - 300))
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": max_out,
        "response_format": {"type": "json_object"},
    }
    r = requests.post(url, headers=headers, json=payload, timeout=TIMEOUT)
    r.raise_for_status()
    return _extract_text(r.json(), "groq")


def verify_groq_key(api_key):
    """Comprueba una key de Groq SIN gastar tokens (lista los modelos).
    Devuelve (ok, mensaje)."""
    try:
        r = requests.get(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=15,
        )
        if r.status_code == 200:
            return True, "ok"
        if r.status_code in (401, 403):
            return False, "Groq dice que esa API key no es válida."
        return False, f"Groq respondió HTTP {r.status_code}. Intenta de nuevo."
    except Exception:
        return False, "No se pudo conectar con Groq para verificar la key."


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


def generate_with_fallback(prompt, personal_key=None):
    """
    Recorre los proveedores en orden. Devuelve (text, provider_used, errores).
    Orden: key personal del docente -> Groq 1 -> Groq 2 -> Groq 3 (emergencia)
           -> Gemini -> Mistral. Si todos fallan, text = None.
    """
    groq_key = os.environ.get("GROQ_API_KEY")
    groq_key2 = os.environ.get("GROQ_API_KEY_2")
    groq_key3 = os.environ.get("GROQ_API_KEY_3")  # emergencia
    gemini_key = os.environ.get("GEMINI_API_KEY")
    mistral_key = os.environ.get("MISTRAL_API_KEY")

    groq_model = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
    gemini_model = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")
    mistral_model = os.environ.get("MISTRAL_MODEL", "mistral-large-latest")

    chain = []
    # (nombre, función, condición de que exista la key)
    if personal_key:
        chain.append(("groq_personal",
                      lambda: _call_groq(prompt, personal_key, groq_model), True))
    chain += [
        ("groq", lambda: _call_groq(prompt, groq_key, groq_model),    bool(groq_key)),
        ("groq2", lambda: _call_groq(prompt, groq_key2, groq_model),   bool(groq_key2)),
        ("groq3", lambda: _call_groq(prompt, groq_key3, groq_model),   bool(groq_key3)),
        ("gemini", lambda: _call_gemini(
            prompt, gemini_key, gemini_model), bool(gemini_key)),
        ("mistral", lambda: _call_mistral(
            prompt, mistral_key, mistral_model), bool(mistral_key)),
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
