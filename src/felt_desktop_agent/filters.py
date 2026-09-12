"""Notification filtering — split out from __init__.py so it's testable
without spinning up the whole watcher loop."""


def is_allowed(app_name: str, summary: str, config) -> bool:
    if app_name.lower() in config.allowed_apps_list():
        return True
    # KDE-Connect-forwarded phone notifications all share app_name="KDE
    # Connect" — the real source app is in `summary` instead (2026-09-12
    # finding, confirmed against real logs, not guessed).
    if app_name == "KDE Connect" and summary.lower() in config.kdeconnect_source_apps_list():
        return True
    return False
