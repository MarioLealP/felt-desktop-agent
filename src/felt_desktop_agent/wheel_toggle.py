"""Triggers Felt's tray-app actions via a mouse's horizontal-scroll
wheel tilt (Mario's SteelSeries Aerox 9: "mousewheel left"/"mousewheel
right"). Real 2026-09-12 finding, confirmed by directly capturing raw
input events (not guessed): these buttons don't generate discrete
key/button presses at all — they're `REL_HWHEEL` (horizontal scroll
axis) events, value -1 (left) or +1 (right). No ordinary keybinding
mechanism (including Wayfire's own `[command]` plugin, built around
discrete KEY_/BTN_ triggers) can bind to an axis event directly, so
this watches for it directly instead.

Mario, same day: "left wheel -> text command... right wheel -> voice
command" — two distinct actions, not one generic toggle — sent as named
commands over felt-dashboard's trigger_socket (a Unix socket; see
src-tauri/src/trigger_socket.rs for why not more OS signals).
"""

import asyncio
import logging
import os
import socket

import evdev

logger = logging.getLogger(__name__)

_REL_HWHEEL = 6


def _trigger_socket_path() -> str:
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR", "/tmp")
    return f"{runtime_dir}/felt-tray.sock"


def find_device(name_substring: str) -> evdev.InputDevice | None:
    """Most /dev/input/event* nodes aren't readable by this user (only
    ones a udev rule or group membership grants access to) — opening one
    to check its name raises PermissionError, which must be skipped
    per-device rather than aborting the whole search on the first one
    hit (a real bug found 2026-09-12: the target device was never
    reached because an earlier, inaccessible one raised first)."""
    # writable=False: this only ever reads events, and evdev's default
    # (writable=True) silently excludes read-only-accessible devices —
    # exactly this one, granted read via a udev uaccess tag/chmod, not
    # write (a real bug found 2026-09-12: list_devices() returned an
    # empty list because of this default, not a permissions problem).
    for path in evdev.list_devices(writable=False):
        try:
            device = evdev.InputDevice(path)
        except (PermissionError, OSError):
            continue
        if name_substring.lower() in device.name.lower():
            return device
    return None


def send_trigger(command: str) -> None:
    """Best-effort: if felt-dashboard's tray app isn't running, there's
    nothing listening on the socket — connection failures are logged,
    not raised, since a mouse-tilt handler crashing the whole watcher
    over a transient "app not open yet" state would be worse than a
    dropped trigger."""
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.connect(_trigger_socket_path())
            sock.sendall(f"{command}\n".encode())
    except OSError as e:
        logger.warning("couldn't reach the Felt trigger socket: %s", e)


async def watch(name_substring: str) -> None:
    device = find_device(name_substring)
    if device is None:
        logger.warning("wheel-toggle device matching %r not found, not watching", name_substring)
        return

    logger.info("watching %s for wheel-tilt events", device.name)
    async for event in device.async_read_loop():
        if event.type == evdev.ecodes.EV_REL and event.code == _REL_HWHEEL and event.value in (-1, 1):
            if event.value == -1:
                logger.info("wheel tilt left — opening Felt for typing")
                send_trigger("show-text")
            else:
                logger.info("wheel tilt right — opening Felt and starting voice")
                send_trigger("start-voice")


async def run_forever(name_substring: str) -> None:
    """Reconnects if the device disappears (unplugged, sleep/wake,
    reboot of the mouse's wireless dongle, etc.) instead of watching
    once and silently going quiet forever."""
    while True:
        await watch(name_substring)
        await asyncio.sleep(5)
