from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FELT_AGENT_", env_file=".env", extra="ignore")

    # felt-voice — unset means TTS-read-aloud is simply skipped, not a
    # guessed/hardcoded address (2026-09-12 finding: this used to default
    # to a real machine's actual IP, a real "no hardcoding" violation).
    voice_url: str | None = None

    api_port: int = 8422

    # Per-app allowlist for NATIVE desktop notifications — deliberately
    # empty by default. Nothing gets read aloud until explicitly added;
    # never a default-everything behavior.
    allowed_apps: str = ""

    # 2026-09-12 finding: phone notifications (WhatsApp, etc.) don't come
    # from a native app at all — KDE Connect forwards them, so the D-Bus
    # app_name is always "KDE Connect" with the real source app in the
    # notification's `summary` field instead. This is a SEPARATE allowlist
    # matched against `summary`, checked only when app_name == "KDE Connect".
    kdeconnect_source_apps: str = ""

    # Substring match (case-insensitive) against an input device's name,
    # used to find the mouse whose wheel-tilt should toggle the Felt
    # tray app's window. Empty = disabled. Not the exact device path
    # (those aren't stable across reconnects/reboots) — matched by name
    # via python-evdev each time the watcher (re)starts.
    wheel_toggle_device_name: str = ""

    def allowed_apps_list(self) -> list[str]:
        return [a.strip().lower() for a in self.allowed_apps.split(",") if a.strip()]

    def kdeconnect_source_apps_list(self) -> list[str]:
        return [a.strip().lower() for a in self.kdeconnect_source_apps.split(",") if a.strip()]


def load_config() -> AgentConfig:
    return AgentConfig()
