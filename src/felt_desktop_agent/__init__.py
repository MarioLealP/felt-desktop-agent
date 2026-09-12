import asyncio
import logging

import uvicorn

from felt_desktop_agent.api import app as fastapi_app
from felt_desktop_agent.config import load_config
from felt_desktop_agent.dbus_watcher import watch_notifications
from felt_desktop_agent.filters import is_allowed
from felt_desktop_agent.focus_gate import is_fullscreen_game_active
from felt_desktop_agent.player import speak
from felt_desktop_agent.wheel_toggle import run_forever as run_wheel_toggle_forever

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def _watch_notifications_loop() -> None:
    config = load_config()
    logger.info(
        "watching notifications, native allowlist=%s, KDE Connect source allowlist=%s",
        config.allowed_apps_list() or "(empty)",
        config.kdeconnect_source_apps_list() or "(empty)",
    )

    async for app_name, summary, body in watch_notifications():
        if not is_allowed(app_name, summary, config):
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
    config = load_config()
    tasks = [_watch_notifications_loop(), _run_api()]
    if config.wheel_toggle_device_name:
        tasks.append(run_wheel_toggle_forever(config.wheel_toggle_device_name))
    await asyncio.gather(*tasks)


def main() -> None:
    asyncio.run(_run())
