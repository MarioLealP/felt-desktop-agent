from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FELT_AGENT_", env_file=".env", extra="ignore")

    voice_url: str = "http://192.168.1.104:8421"

    api_port: int = 8422

    # Per-app allowlist — deliberately empty by default. Nothing gets read
    # aloud until explicitly added; never a default-everything behavior.
    allowed_apps: str = ""

    def allowed_apps_list(self) -> list[str]:
        return [a.strip().lower() for a in self.allowed_apps.split(",") if a.strip()]


def load_config() -> AgentConfig:
    return AgentConfig()
