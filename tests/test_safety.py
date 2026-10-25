from smarttv_toolkit.optimizer import ANIMATION_KEYS, TvOptimizer


class FakeClient:
    def __init__(self):
        self.calls = []
    def shell(self, command, timeout=20):
        self.calls.append(command)
        if command.startswith("settings get"):
            return "1.0"
        return "OK"


def test_animation_keys_are_limited_and_known():
    assert ANIMATION_KEYS == (
        "window_animation_scale",
        "transition_animation_scale",
        "animator_duration_scale",
    )


def test_turbo_only_changes_animation_settings():
    client = FakeClient()
    result = TvOptimizer(client).apply_fast_ui()
    assert len(result.changed) == 3
    assert all(command.startswith("settings put global ") for command in client.calls)
    assert not result.skipped


def test_restore_uses_stored_values():
    client = FakeClient()
    values = {key: "0.5" for key in ANIMATION_KEYS}
    result = TvOptimizer(client).restore_ui(values)
    assert len(result.changed) == 3
    assert all(command.endswith(" 0.5") for command in client.calls)
