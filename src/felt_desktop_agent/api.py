"""felt-desktop-agent's HTTP API — desktop-local capabilities felt-core
can't reach directly (KDE Connect lives on the desktop where kdeconnectd
runs, not on the server)."""

import uvicorn
from fastapi import FastAPI, HTTPException

from felt_desktop_agent.config import load_config
from felt_desktop_agent.kdeconnect import get_battery, ring_phone
from felt_desktop_agent.media import get_status, next_track, play_pause, previous_track, set_volume

app = FastAPI(title="felt-desktop-agent", version="0.1.0")


@app.get("/v1/kdeconnect/battery")
async def battery_endpoint() -> dict:
    result = await get_battery()
    if result is None:
        raise HTTPException(status_code=503, detail="No KDE Connect device available.")
    return result


@app.post("/v1/kdeconnect/ring")
async def ring_endpoint() -> dict:
    ok = await ring_phone()
    if not ok:
        raise HTTPException(status_code=503, detail="No KDE Connect device available.")
    return {"ok": True}


@app.get("/v1/media/status")
async def media_status_endpoint() -> dict:
    return await get_status()


@app.post("/v1/media/play-pause")
async def media_play_pause_endpoint() -> dict:
    ok = await play_pause()
    if not ok:
        raise HTTPException(status_code=503, detail="No media player available.")
    return {"ok": True}


@app.post("/v1/media/next")
async def media_next_endpoint() -> dict:
    ok = await next_track()
    if not ok:
        raise HTTPException(status_code=503, detail="No media player available.")
    return {"ok": True}


@app.post("/v1/media/previous")
async def media_previous_endpoint() -> dict:
    ok = await previous_track()
    if not ok:
        raise HTTPException(status_code=503, detail="No media player available.")
    return {"ok": True}


@app.post("/v1/media/volume")
async def media_volume_endpoint(level: float) -> dict:
    ok = await set_volume(level)
    if not ok:
        raise HTTPException(status_code=503, detail="No media player available.")
    return {"ok": True}


def run_api() -> None:
    config = load_config()
    uvicorn.run(app, host="0.0.0.0", port=config.api_port)
