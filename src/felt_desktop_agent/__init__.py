import asyncio
import logging

import uvicorn

from felt_desktop_agent.api import app as fastapi_app
from felt_desktop_agent.config import load_config
from felt_desktop_agent.dbus_watcher import watch_notifications
from felt_desktop_agent.focus_gate import is_fullscreen_game_active
from felt_desktop_agent.player import speak

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _is_allowed(app_name: str, summary: str, config) -> bool:
    if app_name.lower() in config.allowed_apps_list():
        return True
    # KDE-Connect-forwarded phone notifications all share app_name="KDE
    # Connect" — the real source app is in `summary` instead.
    if app_name == "KDE Connect" and summary.lower() in config.kdeconnect_source_apps_list():
        return True
    return False


async def _watch_notifications_loop() -> None:
    config = load_config()
    logger.info(
        "watching notifications, native allowlist=%s, KDE Connect source allowlist=%s",
        config.allowed_apps_list() or "(empty)",
        config.kdeconnect_source_apps_list() or "(empty)",
    )

    async for app_name, summary, body in watch_notifications():
        if not _is_allowed(app_name, summary, config):
            logger.info("ignored (not allowlisted): app=%s summary=%r", app_name, summary)
            continue
        if not is_fullscreen_game_active():
            logger.info("ignored (no fullscreen game active): app=%s summary=%r", app_name, summary)
            continue
        logger.info("reading aloud: app=%s summary=%r", app_name, summary)
        text = f"{summary}. {body}" if body else summary
        await speak(text, config)


async def _run_api() -> None:
    config = load_config()
    server_config = uvicorn.Config(fastapi_app, host="0.0.0.0", port=config.api_port, log_level="info")
    await uvicorn.Server(server_config).serve()


async def _run() -> None:
    await asyncio.gather(_watch_notifications_loop(), _run_api())


def main() -> None:
    asyncio.run(_run())
