"""
Mr. AI Smart Classroom — Automatic Ollama Model Detector & Intelligent Fallback
Scans local Ollama server, detects installed models, selects best match via priority list.
"""
import requests
import streamlit as st

PREFERRED_MODEL_PRIORITY = [
    "llama3:latest",
    "llama3",
    "llama3:8b",
    "gemma3:4b",
    "gemma3",
    "qwen2.5:3b",
    "qwen2.5",
    "mistral",
    "phi3",
]


def detect_available_models() -> list[str]:
    """
    Query local Ollama server GET http://localhost:11434/api/tags.
    Returns list of installed model names e.g. ['llama3:latest', 'gemma3:4b'].
    Returns [] if Ollama is offline or no models found.
    """
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=2)
        if resp.status_code == 200:
            models_data = resp.json().get("models", [])
            return [m["name"] for m in models_data if "name" in m]
    except Exception:
        pass
    return []


def get_best_model() -> str:
    """
    Select the highest-priority installed Ollama model.
    Falls back to first available model, or 'llama3' if Ollama is offline/empty.
    """
    installed = detect_available_models()
    if not installed:
        return "llama3"

    installed_bases = {m.split(":")[0]: m for m in installed}
    installed_exact = set(installed)

    # 1. Match priority list
    for pref in PREFERRED_MODEL_PRIORITY:
        if pref in installed_exact:
            return pref
        pref_base = pref.split(":")[0]
        if pref_base in installed_bases:
            return installed_bases[pref_base]

    # 2. Fallback to first installed model
    return installed[0]


def is_model_available(model_name: str) -> bool:
    """Check if specific model is currently installed in Ollama."""
    installed = detect_available_models()
    if not installed:
        return False
    installed_bases = {m.split(":")[0] for m in installed}
    return model_name in installed or model_name.split(":")[0] in installed_bases


def get_active_model() -> str:
    """
    Retrieve active_model from session state or auto-detect best available.
    Stores result in st.session_state['active_model'].
    """
    if "active_model" not in st.session_state or not st.session_state["active_model"]:
        st.session_state["active_model"] = get_best_model()
    return st.session_state["active_model"]


def refresh_model_cache() -> str:
    """Re-scan Ollama installed models and update active_model in session state."""
    best = get_best_model()
    st.session_state["active_model"] = best
    return best
