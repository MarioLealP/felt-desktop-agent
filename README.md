# felt-desktop-agent

Felt's desktop-side sensor — currently: D-Bus desktop-notification
passthrough, read aloud via `felt-voice`'s TTS. Part of the
[Felt](https://git.clockmost.com/Benylin/Felt) project.

Runs *on the user's own desktop* (not the server) since it needs the
session D-Bus and the local audio output — a natural home for other
desktop-side pieces later (fullscreen/game-focus gating, KDE Connect
integration).

## Why it exists

"If I'm playing I don't want to have to read it, just read my WhatsApp
message or something" (Mario) — a fullscreen game means desktop toast
notifications go unseen.

## Config

- `FELT_AGENT_VOICE_URL` — felt-voice's URL (default assumes the Nitro5).
- `FELT_AGENT_ALLOWED_APPS` — comma-separated, case-insensitive app-name
  allowlist. **Empty by default — nothing is read aloud until an app is
  explicitly added.** This is deliberate: no default-everything behavior.

## Quickstart

```
uv sync
cp .env.example .env   # set FELT_AGENT_ALLOWED_APPS
uv run felt-desktop-agent
```

## Status (2026-09-12)

Built and verified: fires a real D-Bus notification, reads it aloud
through felt-voice + local audio playback, confirmed with a live test
(`notify-send`, allowlisted for the test). **Not yet done**:
- Fullscreen/game-focus gating — the actual ask was "while I'm playing,"
  not "always." Currently reads aloud any allowlisted notification,
  any time. Needs Wayfire's `wlr-foreign-toplevel` state.
- Real app allowlist entries — only `notify-send` (the test tool) is
  confirmed. WhatsApp/Discord's actual D-Bus `app_name` values need
  confirming against a real notification from each before adding them.
