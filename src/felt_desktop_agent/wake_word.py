"""Detects the spoken word "Felt" and fires the same action as
right-wheel-tilt (Mario, 2026-09-12: "felt -> voice command... right
wheel -> voice command" — three distinct trigger sources, the wheel-
tilts and this one, converging on the same start-voice action; see
wheel_toggle.py for the other two).

No pretrained openWakeWord model exists for "Felt" (its bundled models
cover phrases like "hey jarvis"/"alexa", not this one) — the model this
loads was custom-trained via github.com/lgpearson1771/openwakeword-
trainer on the Nitro5's RTX 3060 (see assistant-voice.md for the actual
training run and its result). `openwakeword`/`sounddevice` are imported
lazily inside the functions that need them, not at module level, so
importing this module — and therefore starting felt-desktop-agent at
all — doesn't require PortAudio/onnxruntime to be present on a machine
where `wake_word_model_path` is unset (feature disabled, same
"unset = disabled" convention as the rest of this codebase).
"""

import asyncio
import logging
import time

from felt_desktop_agent.wheel_toggle import send_trigger

logger = logging.getLogger(__name__)

_SAMPLE_RATE = 16000
_CHUNK_SAMPLES = 1280  # 80ms at 16kHz — openWakeWord's recommended frame size

# A single spoken "Felt" spans several consecutive 80ms frames, each of
# which can independently score above threshold — without a cooldown,
# one utterance would fire start-voice several times in a row.
_COOLDOWN_SECONDS = 3.0


class WakeWordDetector:
    """The actual detection + debounce logic, kept separate from the
    mic-capture loop below so it's unit-testable with a fake model and
    no real audio hardware (see tests/test_wake_word.py)."""

    def __init__(self, model, threshold: float) -> None:
        self._model = model
        self._threshold = threshold
        self._last_trigger = 0.0

    def feed(self, frame) -> bool:
        """Feed one audio frame through the model. Returns True if this
        frame caused a wake-word trigger (mainly useful for tests)."""
        predictions = self._model.predict(frame)
        now = time.monotonic()
        if now - self._last_trigger < _COOLDOWN_SECONDS:
            return False
        for name, score in predictions.items():
            if score > self._threshold:
                logger.info("wake word detected: %s (score=%.2f) — starting voice", name, score)
                self._last_trigger = now
                send_trigger("start-voice")
                return True
        return False


def _load_model(model_path: str):
    from openwakeword.model import Model

    return Model(wakeword_models=[model_path], inference_framework="onnx")


async def watch(model_path: str, threshold: float) -> None:
    import sounddevice as sd

    detector = WakeWordDetector(_load_model(model_path), threshold)
    logger.info('listening for the "Felt" wake word (model=%s, threshold=%.2f)', model_path, threshold)

    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()

    def _callback(indata, frames, time_info, status):
        del frames, time_info
        if status:
            logger.warning("mic input status: %s", status)
        # Runs on sounddevice's own audio thread, not the asyncio loop's
        # thread — call_soon_threadsafe is the correct handoff.
        loop.call_soon_threadsafe(queue.put_nowait, indata[:, 0].copy())

    with sd.InputStream(
        samplerate=_SAMPLE_RATE,
        channels=1,
        dtype="int16",
        blocksize=_CHUNK_SAMPLES,
        callback=_callback,
    ):
        while True:
            frame = await queue.get()
            detector.feed(frame)


async def run_forever(model_path: str, threshold: float = 0.5) -> None:
    """Reconnects on failure (e.g. the mic device disappearing) instead
    of watching once and silently going quiet forever — same reasoning
    as wheel_toggle.run_forever."""
    while True:
        try:
            await watch(model_path, threshold)
        except Exception:
            logger.exception("wake-word watcher crashed, restarting in 5s")
            await asyncio.sleep(5)
