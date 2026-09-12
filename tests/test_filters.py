from felt_desktop_agent.filters import is_allowed


class _Config:
    def __init__(self, allowed_apps=(), kdeconnect_source_apps=()):
        self._allowed_apps = allowed_apps
        self._kdeconnect_source_apps = kdeconnect_source_apps

    def allowed_apps_list(self):
        return list(self._allowed_apps)

    def kdeconnect_source_apps_list(self):
        return list(self._kdeconnect_source_apps)


def test_native_app_allowed_case_insensitive():
    config = _Config(allowed_apps=["vesktop"])
    assert is_allowed("VeSktop", "some message", config) is True


def test_native_app_not_allowlisted():
    config = _Config(allowed_apps=["vesktop"])
    assert is_allowed("Discord", "some message", config) is False


def test_kdeconnect_relay_matched_on_summary():
    # The real 2026-09-12 finding: WhatsApp notifications arrive with
    # app_name="KDE Connect", the real source app is in `summary`.
    config = _Config(kdeconnect_source_apps=["whatsapp"])
    assert is_allowed("KDE Connect", "WhatsApp", config) is True


def test_kdeconnect_relay_not_in_source_allowlist():
    config = _Config(kdeconnect_source_apps=["whatsapp"])
    assert is_allowed("KDE Connect", "Gmail", config) is False


def test_kdeconnect_app_name_alone_does_not_bypass_source_check():
    # app_name == "KDE Connect" is necessary but not sufficient — the
    # summary must also be on the source allowlist.
    config = _Config(allowed_apps=[], kdeconnect_source_apps=[])
    assert is_allowed("KDE Connect", "WhatsApp", config) is False


def test_empty_allowlists_allow_nothing():
    config = _Config()
    assert is_allowed("vesktop", "anything", config) is False
    assert is_allowed("KDE Connect", "WhatsApp", config) is False
