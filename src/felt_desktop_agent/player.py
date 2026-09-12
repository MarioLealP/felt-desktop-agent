"""Text -> speech (via felt-voice) -> played locally on this desktop."""

import asyncio
import logging
import tempfile

import httpx

from felt_desktop_agent.config import AgentConfig

logger = logging.getLogger(__name__)


async def speak(text: str, config: AgentConfig) -> None:
    if config.voice_url is None:
        logger.warning("can't read aloud: no voice_url configured")
        return

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(f"{config.voice_url}/v1/tts", json={"text": text})
        response.raise_for_status()
        audio = response.content

    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        tmp.write(audio)
        tmp.flush()
        process = await asyncio.create_subprocess_exec("paplay", tmp.name)
        await process.wait()
