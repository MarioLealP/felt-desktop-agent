from felt_desktop_agent.media import select_active_player


def test_prefers_playing_player_over_paused():
    players = ["firefox.instance_1", "spotify"]
    statuses = {"firefox.instance_1": "Paused", "spotify": "Playing"}
    assert select_active_player(players, statuses) == "spotify"


def test_falls_back_to_first_player_when_none_playing():
    players = ["firefox.instance_1", "spotify"]
    statuses = {"firefox.instance_1": "Paused", "spotify": "Paused"}
    assert select_active_player(players, statuses) == "firefox.instance_1"


def test_no_players_returns_none():
    assert select_active_player([], {}) is None


def test_first_playing_player_wins_when_multiple_are_playing():
    players = ["a", "b", "c"]
    statuses = {"a": "Paused", "b": "Playing", "c": "Playing"}
    assert select_active_player(players, statuses) == "b"
