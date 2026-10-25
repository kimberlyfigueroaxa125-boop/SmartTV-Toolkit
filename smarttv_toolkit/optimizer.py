from __future__ import annotations

from dataclasses import dataclass

from .adb import AdbClient, AdbError


ANIMATION_KEYS = (
    "window_animation_scale",
    "transition_animation_scale",
    "animator_duration_scale",
)


@dataclass(frozen=True)
class OptimizationResult:
    changed: tuple[str, ...]
    skipped: tuple[str, ...]


class TvOptimizer:
    """Reversible, conservative Android TV optimizations."""

    def __init__(self, client: AdbClient) -> None:
        self.client = client

    def read_animation_scales(self) -> dict[str, str]:
        result: dict[str, str] = {}
        for key in ANIMATION_KEYS:
            try:
                result[key] = self.client.shell(f"settings get global {key}").strip()
            except AdbError:
                result[key] = "null"
        return result

    def apply_fast_ui(self) -> OptimizationResult:
        changed: list[str] = []
        skipped: list[str] = []
        for key in ANIMATION_KEYS:
            try:
                self.client.shell(f"settings put global {key} 0")
                changed.append(f"{key}=0")
            except AdbError as exc:
                skipped.append(f"{key}: {exc}")
        return OptimizationResult(tuple(changed), tuple(skipped))

    def restore_ui(self, values: dict[str, str] | None = None) -> OptimizationResult:
        values = values or {key: "1.0" for key in ANIMATION_KEYS}
        changed: list[str] = []
        skipped: list[str] = []
        for key in ANIMATION_KEYS:
            value = values.get(key, "1.0").strip()
            if value in {"", "null", "None"}:
                value = "1.0"
            if value not in {"0", "0.0", "0.5", "1", "1.0", "1.5", "2", "2.0"}:
                skipped.append(f"{key}: invalid saved value")
                continue
            try:
                self.client.shell(f"settings put global {key} {value}")
                changed.append(f"{key}={value}")
            except AdbError as exc:
                skipped.append(f"{key}: {exc}")
        return OptimizationResult(tuple(changed), tuple(skipped))

    def trim_caches(self) -> str:
        return self.client.shell("pm trim-caches 512M", timeout=60)

    def compile_apps(self) -> str:
        return self.client.shell("cmd package compile -m speed-profile -a", timeout=180)
