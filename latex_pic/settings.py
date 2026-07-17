from __future__ import annotations

import json
import os
import sys
import winreg
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Settings:
    hotkey: str = "`"
    enabled: bool = True
    wrap_math: bool = False
    start_minimized: bool = False
    start_on_boot: bool = False
    api_base: str = "https://openrouter.ai/api/v1"
    api_model: str = "google/gemini-2.5-flash-lite"

    @property
    def hotkey_label(self) -> str:
        return "~（键盘左上角）" if self.hotkey == "`" else self.hotkey


def settings_path() -> Path:
    base = Path(os.environ.get("APPDATA", Path.home())) / "LatexPic"
    base.mkdir(parents=True, exist_ok=True)
    return base / "settings.json"


def env_path() -> Path:
    return Path(__file__).resolve().parent.parent / ".env"


def load_api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if key:
        return key
    path = env_path()
    if not path.exists():
        return ""
    try:
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if line.startswith("OPENROUTER_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return ""


def save_api_key(api_key: str) -> None:
    path = env_path()
    existing = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    replacement = f"OPENROUTER_API_KEY={api_key.strip()}"
    output: list[str] = []
    replaced = False
    for line in existing:
        if line.strip().startswith("OPENROUTER_API_KEY="):
            if not replaced:
                output.append(replacement)
                replaced = True
        else:
            output.append(line)
    if not replaced:
        output.append(replacement)
    path.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8")


def load_settings() -> Settings:
    path = settings_path()
    if not path.exists():
        return Settings()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        allowed = {key: value for key, value in data.items() if key in Settings.__dataclass_fields__}
        settings = Settings(**allowed)
        if settings.api_base.rstrip("/") == "https://api.openai.com/v1":
            settings.api_base = "https://openrouter.ai/api/v1"
        if settings.api_model == "gpt-4o-mini":
            settings.api_model = "google/gemini-2.5-flash-lite"
        return settings
    except (OSError, ValueError, TypeError):
        return Settings()


def save_settings(settings: Settings) -> None:
    settings_path().write_text(
        json.dumps(asdict(settings), ensure_ascii=False, indent=2), encoding="utf-8"
    )


def configure_startup(enabled: bool) -> None:
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    value_name = "LatexPic"
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE
    ) as key:
        if enabled:
            project_root = Path(__file__).resolve().parent.parent
            pythonw = Path(sys.executable).with_name("pythonw.exe")
            if not pythonw.exists():
                pythonw = Path(sys.executable)
            command = f'"{pythonw}" "{project_root / "main.py"}" --minimized'
            winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, command)
        else:
            try:
                winreg.DeleteValue(key, value_name)
            except FileNotFoundError:
                pass
