"""Client tipis ke service Node (Baileys). Ini satu-satunya tempat FastAPI
'ngomong' ke engine WhatsApp. Kalau nanti ganti engine, cukup ubah file ini."""
import requests
from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logging import get_logger

logger = get_logger("wa.gateway")

_HEADERS = {"X-Internal-Token": settings.WA_INTERNAL_TOKEN}
_TIMEOUT = 30


def _url(path: str) -> str:
    return f"{settings.WA_GATEWAY_URL.rstrip('/')}{path}"


def start_session(session_key: str) -> dict:
    r = requests.post(_url("/sessions"), json={"sessionKey": session_key}, headers=_HEADERS, timeout=_TIMEOUT)
    r.raise_for_status()
    return r.json()


def get_status(session_key: str) -> dict:
    try:
        r = requests.get(_url(f"/sessions/{session_key}"), headers=_HEADERS, timeout=_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        logger.warning("gateway status error: %s", e)
        return {"status": "disconnected", "qr": None, "phone": None}


def send_message(session_key: str, to: str, text: str) -> dict:
    try:
        r = requests.post(
            _url(f"/sessions/{session_key}/send"),
            json={"to": to, "text": text},
            headers=_HEADERS,
            timeout=_TIMEOUT,
        )
    except requests.RequestException as e:
        raise AppException(f"WA gateway tidak bisa dihubungi: {e}", 502)
    if r.status_code >= 400:
        detail = r.json().get("detail", "gagal kirim") if r.headers.get("content-type", "").startswith("application/json") else r.text
        raise AppException(f"Gagal kirim: {detail}", r.status_code if r.status_code < 500 else 502)
    return r.json()


def logout(session_key: str) -> None:
    try:
        requests.delete(_url(f"/sessions/{session_key}"), headers=_HEADERS, timeout=_TIMEOUT)
    except requests.RequestException as e:
        logger.warning("gateway logout error: %s", e)
