from __future__ import annotations

from duui_py.models.config import FrameworkSettings

_settings: FrameworkSettings = FrameworkSettings()
_settings_initialized = False


def set_settings_once(settings: FrameworkSettings) -> None:
    global _settings, _settings_initialized
    if _settings_initialized:
        raise RuntimeError("framework settings already initialized for this process")
    _settings = settings
    _settings_initialized = True


def get_settings() -> FrameworkSettings:
    return _settings


def is_settings_initialized() -> bool:
    return _settings_initialized
