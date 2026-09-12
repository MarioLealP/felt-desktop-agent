"""Media transport control via MPRIS (`playerctl` under the hood) —
play/pause/skip/volume on whatever's currently loaded (Spotify desktop
client, a YouTube tab, etc.) without needing to know which app is active,
since anything MPRIS-aware exposes the same interface on Linux. Search-
and-play-new-content (Spotify/YouTube APIs) is a separate, not-yet-built
layer — see assistant-skills.md.
"""

import asyncio


async def _run(*args: str) -> tuple[str, int]:
    process = await asyncio.create_subprocess_exec(
        "playerctl", *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL
    )
    stdout, _ = await process.communicate()
    return stdout.decode().strip(), process.returncode


async def list_players() -> list[str]:
    output, returncode = await _run("-l")
    if returncode != 0:
        return []
    return [line.strip() for line in output.splitlines() if line.strip()]


def select_active_player(players: list[str], statuses: dict[str, str]) -> str | None:
    """Pure selection logic: prefer whichever player is actually
    "Playing"; fall back to the first one otherwise (e.g. so "pause" has
    something to target even if everything's already paused). None if
    there are no players at all.
    """
    for player in players:
        if statuses.get(player) == "Playing":
            return player
    return players[0] if players else None


async def _status(player: str) -> str:
    output, returncode = await _run("-p", player, "status")
    return output if returncode == 0 else "Unknown"


async def _metadata_field(player: str, field: str) -> str:
    output, returncode = await _run("-p", player, "metadata", field)
    return output if returncode == 0 else ""


async def _active_player() -> str | None:
    players = await list_players()
    if not players:
        return None
    statuses = {player: await _status(player) for player in players}
    return select_active_player(players, statuses)


async def get_status() -> dict:
    active = await _active_player()
    if active is None:
        return {"active": False}
    return {
        "active": True,
        "player": active,
        "status": await _status(active),
        "title": await _metadata_field(active, "xesam:title"),
        "artist": await _metadata_field(active, "xesam:artist"),
    }


async def _control(command: str) -> bool:
    active = await _active_player()
    if active is None:
        return False
    _, returncode = await _run("-p", active, command)
    return returncode == 0


async def play_pause() -> bool:
    return await _control("play-pause")


async def next_track() -> bool:
    return await _control("next")


async def previous_track() -> bool:
    return await _control("previous")


async def set_volume(level: float) -> bool:
    active = await _active_player()
    if active is None:
        return False
    _, returncode = await _run("-p", active, "volume", str(level))
    return returncode == 0
