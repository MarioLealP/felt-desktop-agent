import asyncio
import logging

from felt_desktop_agent.config import load_config
from felt_desktop_agent.dbus_watcher import watch_notifications
from felt_desktop_agent.focus_gate import is_fullscreen_game_active
from felt_desktop_agent.player import speak

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def _run() -> None:
    config = load_config()
    allowed = config.allowed_apps_list()
    logger.info("watching notifications, allowlist=%s", allowed or "(empty — nothing will be read aloud)")

    async for app_name, summary, body in watch_notifications():
        if app_name.lower() not in allowed:
            logger.info("ignored (not allowlisted): app=%s summary=%r", app_name, summary)
            continue
        if not is_fullscreen_game_active():
            logger.info("ignored (no fullscreen game active): app=%s summary=%r", app_name, summary)
            continue
        logger.info("reading aloud: app=%s summary=%r", app_name, summary)
        text = f"{summary}. {body}" if body else summary
        await speak(text, config)


def main() -> None:
    asyncio.run(_run())
