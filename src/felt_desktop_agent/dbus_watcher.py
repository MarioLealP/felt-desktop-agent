"""Watches the session D-Bus for desktop notifications
(org.freedesktop.Notifications.Notify calls) via `dbus-monitor`.

Deliberately parses `dbus-monitor`'s text output rather than adding a
native D-Bus binding dependency — the Notify call's field order is fixed
and simple enough that this is robust in practice: among the `string`-
typed arguments (skipping the non-string replaces_id), the order is
always app_name, app_icon, summary, body.
"""

import asyncio
import re
from collections.abc import AsyncIterator

_STRING_RE = re.compile(r'^\s*string "(.*)"$')

MATCH_RULE = "interface='org.freedesktop.Notifications',member='Notify'"


async def watch_notifications() -> AsyncIterator[tuple[str, str, str]]:
    """Yields (app_name, summary, body) for every notification seen,
    unfiltered — the caller applies the allowlist."""
    process = await asyncio.create_subprocess_exec(
        "dbus-monitor", "--session", MATCH_RULE, stdout=asyncio.subprocess.PIPE
    )
    assert process.stdout is not None

    strings: list[str] = []
    in_event = False

    async for raw_line in process.stdout:
        line = raw_line.decode(errors="replace")
        if "member=Notify" in line:
            in_event = True
            strings = []
            continue
        if not in_event:
            continue
        if line.strip().startswith(("method call", "signal", "error")):
            # a new event started without us seeing 4 strings — reset
            in_event = False
            continue

        match = _STRING_RE.match(line)
        if match:
            strings.append(match.group(1))
            if len(strings) == 4:
                app_name, _app_icon, summary, body = strings
                yield app_name, summary, body
                in_event = False
