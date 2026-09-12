from felt_desktop_agent import wake_word


class _FakeModel:
    """Returns one canned prediction dict per call, in order — lets a
    test script exactly what a real openWakeWord model would return for
    a sequence of frames without needing a real trained model."""

    def __init__(self, score_sequence):
        self._score_sequence = list(score_sequence)

    def predict(self, frame):
        del frame
        return self._score_sequence.pop(0)


def test_feed_triggers_when_score_above_threshold(monkeypatch):
    sent = []
    monkeypatch.setattr(wake_word, "send_trigger", lambda command: sent.append(command))
    detector = wake_word.WakeWordDetector(_FakeModel([{"felt": 0.9}]), threshold=0.5)

    fired = detector.feed(b"frame")

    assert fired is True
    assert sent == ["start-voice"]


def test_feed_does_not_trigger_below_threshold(monkeypatch):
    sent = []
    monkeypatch.setattr(wake_word, "send_trigger", lambda command: sent.append(command))
    detector = wake_word.WakeWordDetector(_FakeModel([{"felt": 0.2}]), threshold=0.5)

    fired = detector.feed(b"frame")

    assert fired is False
    assert sent == []


def test_feed_debounces_repeated_triggers_within_cooldown(monkeypatch):
    # A single spoken "Felt" spans several consecutive 80ms frames, each
    # independently scoring above threshold — without this debounce,
    # one utterance would fire start-voice several times in a row.
    sent = []
    monkeypatch.setattr(wake_word, "send_trigger", lambda command: sent.append(command))
    monkeypatch.setattr(wake_word.time, "monotonic", lambda: 100.0)
    detector = wake_word.WakeWordDetector(_FakeModel([{"felt": 0.9}, {"felt": 0.9}]), threshold=0.5)

    first = detector.feed(b"frame1")
    second = detector.feed(b"frame2")

    assert first is True
    assert second is False
    assert sent == ["start-voice"]


def test_feed_triggers_again_after_cooldown_elapses(monkeypatch):
    sent = []
    monkeypatch.setattr(wake_word, "send_trigger", lambda command: sent.append(command))
    times = iter([100.0, 110.0])
    monkeypatch.setattr(wake_word.time, "monotonic", lambda: next(times))
    detector = wake_word.WakeWordDetector(_FakeModel([{"felt": 0.9}, {"felt": 0.9}]), threshold=0.5)

    first = detector.feed(b"frame1")
    second = detector.feed(b"frame2")

    assert first is True
    assert second is True
    assert sent == ["start-voice", "start-voice"]
