"""KDE Connect integration — battery status and find-my-phone, via
`kdeconnect-cli` + `busctl` (no new D-Bus binding dependency, consistent
with dbus_watcher.py's approach). Device ID is looked up live each call,
not hardcoded, so this keeps working if the paired device ever changes.
"""

import asyncio
import json


async def _run(*args: str) -> str:
    process = await asyncio.create_subprocess_exec(*args, stdout=asyncio.subprocess.PIPE)
    stdout, _ = await process.communicate()
    return stdout.decode().strip()


async def _first_device_id() -> str | None:
    output = await _run("kdeconnect-cli", "--list-available", "--id-only")
    lines = [line for line in output.splitlines() if line.strip()]
    return lines[0].strip() if lines else None


async def get_battery() -> dict | None:
    device_id = await _first_device_id()
    if not device_id:
        return None
    charge_json = await _run(
        "busctl", "--user", "--json=short", "get-property", "org.kde.kdeconnect",
        f"/modules/kdeconnect/devices/{device_id}/battery",
        "org.kde.kdeconnect.device.battery", "charge",
    )
    charging_json = await _run(
        "busctl", "--user", "--json=short", "get-property", "org.kde.kdeconnect",
        f"/modules/kdeconnect/devices/{device_id}/battery",
        "org.kde.kdeconnect.device.battery", "isCharging",
    )
    if not charge_json or not charging_json:
        return None
    return {
        "charge": json.loads(charge_json)["data"],
        "is_charging": json.loads(charging_json)["data"],
    }


async def ring_phone() -> bool:
    device_id = await _first_device_id()
    if not device_id:
        return False
    await _run("kdeconnect-cli", "--device", device_id, "--ring")
    return True
