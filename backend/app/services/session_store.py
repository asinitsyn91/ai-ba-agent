import uuid
from typing import Dict, Any

# In-memory session store (replace with Redis/DB for production)
_sessions: Dict[str, Dict[str, Any]] = {}


def create_session(data: dict) -> str:
    sid = str(uuid.uuid4())
    _sessions[sid] = data
    return sid


def get_session(sid: str) -> dict | None:
    return _sessions.get(sid)


def update_session(sid: str, data: dict):
    if sid in _sessions:
        _sessions[sid].update(data)


def delete_session(sid: str):
    _sessions.pop(sid, None)
