"""Install-wide settings (not per-profile): currently the player's own
image-generation API key. Stored in saves/settings.json on the player's
machine — it's their key on their disk, plaintext is acceptable; it is
never sent to the world server. The key is the opt-in for personal AI art
generation: without one (and without a local ComfyUI), heroes come from the
bundled default art pool."""
import json
import os
from fastapi import APIRouter, HTTPException, Body

router = APIRouter()

_SETTINGS_PATH = os.path.join("saves", "app_settings.json")


def _load() -> dict:
    if os.path.exists(_SETTINGS_PATH):
        try:
            return json.load(open(_SETTINGS_PATH, encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save(data: dict):
    os.makedirs(os.path.dirname(_SETTINGS_PATH), exist_ok=True)
    json.dump(data, open(_SETTINGS_PATH, "w", encoding="utf-8"), indent=2)


def get_generation_api_key() -> str | None:
    """For the generation pipeline: returns the stored key or None."""
    return _load().get("generation_api_key") or None


@router.get("/apikey")
def apikey_status():
    """Masked status only — the full key never leaves the settings file."""
    key = get_generation_api_key()
    if not key:
        return {"set": False, "masked": None}
    masked = key[:4] + "…" + key[-4:] if len(key) > 10 else "•" * len(key)
    return {"set": True, "masked": masked}


@router.post("/apikey")
def set_apikey(payload: dict = Body(...)):
    key = (payload.get("api_key") or "").strip()
    data = _load()
    if not key:
        data.pop("generation_api_key", None)
        _save(data)
        return {"set": False}
    if len(key) < 8 or len(key) > 300:
        raise HTTPException(status_code=400, detail="That doesn't look like a valid API key")
    data["generation_api_key"] = key
    _save(data)
    return {"set": True}
