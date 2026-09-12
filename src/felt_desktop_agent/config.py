from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FELT_AGENT_", env_file=".env", extra="ignore")

    voice_url: str = "http://192.168.1.104:8421"

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

    def allowed_apps_list(self) -> list[str]:
        return [a.strip().lower() for a in self.allowed_apps.split(",") if a.strip()]

    def kdeconnect_source_apps_list(self) -> list[str]:
        return [a.strip().lower() for a in self.kdeconnect_source_apps.split(",") if a.strip()]


def load_config() -> AgentConfig:
    return AgentConfig()
