from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class DeviceInfo:
    serial: str
    manufacturer: str
    model: str
    android: str
    state: str


class AdbError(RuntimeError):
    pass


def find_adb() -> str:
    configured = os.environ.get("ADB_PATH")
    for candidate in (configured, shutil.which("adb")):
        if candidate and os.path.isfile(candidate):
            return candidate
    raise AdbError("ADB не найден. Установи Android SDK Platform-Tools и добавь adb.exe в PATH или настрой ADB_PATH.")


class AdbClient:
    """Small ADB wrapper restricted to read-only diagnostics and approved tweaks."""

    def __init__(self, host: str, port: int = 5555) -> None:
        host = host.strip()
        if host.count(":") == 1 and host.rsplit(":", 1)[1].isdigit():
            host, port_text = host.rsplit(":", 1)
            port = int(port_text)
        if not re.fullmatch(r"[A-Za-z0-9._:-]+", host):
            raise AdbError("Некорректный IP-адрес или имя устройства.")
        if not 1 <= int(port) <= 65535:
            raise AdbError("Некорректный ADB-порт.")
        self.host = host
        self.port = int(port)
        self.serial = f"{self.host}:{self.port}"

    @property
    def adb(self) -> str:
        return find_adb()

    def run(self, *args: str, timeout: int = 15) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                [self.adb, "-s", self.serial, *args],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise AdbError(f"ADB timeout after {timeout}s") from exc
        except OSError as exc:
            raise AdbError(f"Не удалось запустить ADB: {exc}") from exc

    def connect(self) -> str:
        try:
            result = subprocess.run(
                [self.adb, "connect", self.serial],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=15,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise AdbError(str(exc)) from exc
        output = (result.stdout + result.stderr).strip()
        if result.returncode != 0 or "unable" in output.lower() or "failed" in output.lower():
            raise AdbError(output or "ADB connect failed")
        return output

    def disconnect(self) -> str:
        try:
            result = subprocess.run(
                [self.adb, "disconnect", self.serial],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=15,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise AdbError(str(exc)) from exc
        return (result.stdout + result.stderr).strip()

    def info(self) -> DeviceInfo:
        result = self.run("get-state")
        if result.returncode != 0 or result.stdout.strip() != "device":
            raise AdbError(result.stderr.strip() or "Устройство не подключено или не авторизовано")

        def prop(name: str) -> str:
            res = self.run("shell", "getprop", name)
            return res.stdout.strip() if res.returncode == 0 else "unknown"

        return DeviceInfo(
            serial=self.serial,
            manufacturer=prop("ro.product.manufacturer"),
            model=prop("ro.product.model"),
            android=prop("ro.build.version.release"),
            state="device",
        )

    def shell(self, command: str, timeout: int = 20) -> str:
        """Run a narrow, validated command set; rejects shell metacharacters."""
        clean = command.strip()
        if not clean or any(char in clean for char in (";", "|", "&", "`", "$", ">", "<", "\n", "\r")):
            raise AdbError("Команда заблокирована защитным списком.")

        # Exact command patterns only. No shell chaining/substitution is permitted.
        allowed_patterns = (
            r"getprop(?: [A-Za-z0-9._-]+)?",
            r"pm list packages",
            r"settings get global (?:window_animation_scale|transition_animation_scale|animator_duration_scale)",
            r"settings put global (?:window_animation_scale|transition_animation_scale|animator_duration_scale) (?:0|0\.0|0\.5|1|1\.0|1\.5|2|2\.0)",
            r"pm trim-caches (?:256M|512M|1024M)",
            r"cmd package compile -m speed-profile -a",
            r"cat /proc/meminfo",
            r"df -h",
            r"dumpsys meminfo(?: [A-Za-z0-9._]+)?",
            r"dumpsys cpuinfo",
        )
        if not any(re.fullmatch(pattern, clean) for pattern in allowed_patterns):
            raise AdbError("Команда заблокирована защитным списком.")

        # ADB receives the validated command as arguments. No local shell is involved.
        parts = clean.split()
        result = self.run("shell", *parts, timeout=timeout)
        output = (result.stdout + result.stderr).strip()
        if result.returncode != 0:
            raise AdbError(output or f"Команда завершилась с кодом {result.returncode}")
        return output
