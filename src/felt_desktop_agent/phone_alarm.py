"""Sets a real alarm in the phone's own Clock app via adb, instead of felt
reimplementing alarm scheduling/ringing itself (Mario, 2026-09-12: "Just
use the phone alarm stuff. Its already a done feature from Google just
need a way to call it."). A phone alarm actually rings out loud and
survives felt-core being down entirely, unlike a push notification felt
has to be running to send.

Talks to the phone via `adb shell am start` and the public
`android.intent.action.SET_ALARM` intent — not KDE Connect, which doesn't
expose this. Real, permanent limitation of that intent API, not something
missing from this integration: there's no equivalent public intent to
list or cancel an *existing* alarm remotely, only to add one (or open the
Clock app's own alarm list for a human to look at) — Android doesn't let
third parties enumerate or delete another app's alarms. See set_alarm/
skill.py in felt-core for how the caller handles that.
"""

import asyncio
import shlex


async def _adb(*args: str) -> tuple[int, str]:
    process = await asyncio.create_subprocess_exec(
        "adb", *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )
    stdout, _ = await process.communicate()
    return process.returncode, stdout.decode().strip()


async def set_phone_alarm(hour: int, minute: int, label: str) -> bool:
    args = [
        "am",
        "start",
        "-a",
        "android.intent.action.SET_ALARM",
        "--ei",
        "android.intent.extra.alarm.HOUR",
        str(hour),
        "--ei",
        "android.intent.extra.alarm.MINUTES",
        str(minute),
        # Sets it directly rather than just opening the Clock app's "new
        # alarm" screen pre-filled — Mario asked to call the feature, not
        # be handed a form to confirm each time.
        "--ez",
        "android.intent.extra.alarm.SKIP_UI",
        "true",
    ]
    if label:
        args += ["--es", "android.intent.extra.alarm.MESSAGE", label]
    # `adb shell` joins all its arguments into one string and hands that to
    # a shell running ON THE PHONE — a real bug found live, 2026-09-12: a
    # label containing a space ("felt test") arrived at this end as one
    # clean argv token, but adb shell re-split it on the phone's shell,
    # and `am` mis-parsed the stray second word as a package name
    # ("pkg=test"), failing with "unable to resolve Intent". Quoting each
    # token ourselves for that remote shell, not just passing a clean
    # local argv list, is what actually avoids this.
    command = " ".join(shlex.quote(arg) for arg in args)
    returncode, output = await _adb("shell", command)
    # `am start` exits 0 even for some failures (e.g. no matching activity)
    # and reports the real error in its own stdout instead.
    return returncode == 0 and "Error" not in output
