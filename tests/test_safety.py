from smarttv_toolkit.adb import AdbClient, AdbError
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
    assert ANIMATION_KEYS == ("window_animation_scale", "transition_animation_scale", "animator_duration_scale")


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


def test_adb_host_with_explicit_port_is_not_doubled():
    client = AdbClient("192.168.1.20:5555")
    assert client.serial == "192.168.1.20:5555"


def test_adb_command_injection_is_rejected(monkeypatch):
    client = AdbClient("192.168.1.20")
    monkeypatch.setattr(client, "run", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("must not run")))
    for command in ("getprop; pm uninstall com.android.tv", "getprop $(id)", "df -h && reboot"):
        try:
            client.shell(command)
        except AdbError:
            pass
        else:
            raise AssertionError(f"Expected unsafe command to be rejected: {command}")
