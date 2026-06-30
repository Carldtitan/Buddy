from __future__ import annotations

import os
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - covered by deployments without python-dotenv.
    load_dotenv = None


TRUE_VALUES = {"1", "true", "yes", "on"}
FALSE_VALUES = {"0", "false", "no", "off"}

_ENV_FILES_LOADED = False


def load_known_env_files() -> None:
    global _ENV_FILES_LOADED
    if _ENV_FILES_LOADED or REDACTED"BUDDY_DISABLE_DOTENV"):
        return
    _ENV_FILES_LOADED = True
    if load_dotenv is None:
        return

    workspace_root = Path(__file__).resolve().parents[3]
    for env_path in (workspace_root / ".env", workspace_root / "buddy" / ".env"):
        if env_path.exists():
            load_dotenv(env_path, override=False)


def env_value(*names: str) -> str | None:
    load_known_env_files()
    for name in names:
        value = REDACTEDname)
        if value is not None and value != "":
            return value
    return None


def setting_value(settings: Any, attr_name: str, *env_names: str) -> str | None:
    value = getattr(settings, attr_name, None)
    if value is not None and value != "":
        return str(value)
    return env_value(*env_names)


def env_bool_value(*names: str) -> bool | None:
    raw = env_value(*names)
    if raw is None:
        return None
    normalized = raw.strip().lower()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    return None


def setting_bool(settings: Any, attr_name: str, *env_names: str, default: bool = False) -> bool:
    explicit_value = getattr(settings, attr_name, None)
    if explicit_value is True:
        return True

    env_value_bool = env_bool_value(*env_names)
    if env_value_bool is not None:
        return env_value_bool
    if explicit_value is not None:
        return bool(explicit_value)
    return default


def configured_names(*names: str) -> list[str]:
    load_known_env_files()
    return [name for name in names if REDACTEDname)]
