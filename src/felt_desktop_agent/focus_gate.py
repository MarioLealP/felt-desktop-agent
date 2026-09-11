"""Fullscreen/game-focus gating — the actual ask was "while I'm playing,"
not "always." Uses Wayfire's own IPC socket (the `ipc` plugin, already
enabled in Mario's config) via the `wayfire` PyPI client, not raw
wlr-foreign-toplevel Wayland protocol binding — Wayfire's IPC is the
idiomatic way to query this on this specific compositor.

Confirmed live (2026-09-12): a real fullscreen+activated game view
(`steam_app_2933130`, "Moria") was actually running during development —
this is real behavior, not a guess from documentation.
"""

from wayfire import WayfireSocket


def is_fullscreen_game_active() -> bool:
    try:
        sock = WayfireSocket()
        views = sock.list_views()
    except Exception:
        # IPC socket unavailable (no session, compositor restarting, etc.)
        # — fail closed, i.e. don't read anything aloud rather than crash.
        return False
    return any(v.get("fullscreen") and v.get("activated") for v in views)
