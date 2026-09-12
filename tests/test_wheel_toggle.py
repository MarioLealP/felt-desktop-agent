import socket

from felt_desktop_agent import wheel_toggle


class _FakeDevice:
    def __init__(self, path, name):
        self.path = path
        self.name = name


def test_find_device_matches_by_case_insensitive_substring(monkeypatch):
    monkeypatch.setattr(wheel_toggle.evdev, "list_devices", lambda **_kwargs: ["/dev/input/event1"])
    monkeypatch.setattr(
        wheel_toggle.evdev, "InputDevice", lambda path: _FakeDevice(path, "SteelSeries Aerox 9 Wireless")
    )
    device = wheel_toggle.find_device("steelseries")
    assert device is not None
    assert device.path == "/dev/input/event1"


def test_find_device_skips_permission_denied_devices(monkeypatch):
    # Real 2026-09-12 bug: most /dev/input/event* nodes aren't readable by
    # this user; opening one to check its name raises PermissionError,
    # which must be skipped rather than aborting the whole search before
    # reaching the actually-accessible target device later in the list.
    monkeypatch.setattr(
        wheel_toggle.evdev, "list_devices", lambda **_kwargs: ["/dev/input/event1", "/dev/input/event2"]
    )

    def fake_input_device(path):
        if path == "/dev/input/event1":
            raise PermissionError("denied")
        return _FakeDevice(path, "SteelSeries Aerox 9 Wireless")

    monkeypatch.setattr(wheel_toggle.evdev, "InputDevice", fake_input_device)
    device = wheel_toggle.find_device("steelseries")
    assert device is not None
    assert device.path == "/dev/input/event2"


def test_find_device_returns_none_when_no_match(monkeypatch):
    monkeypatch.setattr(wheel_toggle.evdev, "list_devices", lambda **_kwargs: ["/dev/input/event1"])
    monkeypatch.setattr(wheel_toggle.evdev, "InputDevice", lambda path: _FakeDevice(path, "Some Other Mouse"))
    assert wheel_toggle.find_device("steelseries") is None


def test_send_trigger_does_not_raise_when_socket_unreachable(monkeypatch, tmp_path):
    # If felt-dashboard's tray app isn't running there's nothing
    # listening — a dropped trigger should be logged, not crash the
    # whole watcher loop.
    monkeypatch.setattr(wheel_toggle, "_trigger_socket_path", lambda: str(tmp_path / "nonexistent.sock"))
    wheel_toggle.send_trigger("show-text")  # must not raise


def test_send_trigger_sends_the_command_over_a_real_socket(monkeypatch, tmp_path):
    sock_path = str(tmp_path / "felt-tray.sock")
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(sock_path)
    server.listen(1)
    monkeypatch.setattr(wheel_toggle, "_trigger_socket_path", lambda: sock_path)

    wheel_toggle.send_trigger("start-voice")

    conn, _ = server.accept()
    received = conn.recv(1024)
    conn.close()
    server.close()
    assert received == b"start-voice\n"
