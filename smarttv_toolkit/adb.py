from __future__ import annotations

import os
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
    candidates = [configured, shutil.which("adb")]
    for candidate in candidates:
        if candidate and os.path.isfile(candidate):
            return candidate
    raise AdbError("ADB не найден. Установи Android SDK Platform-Tools и добавь adb.exe в PATH или настрой ADB_PATH.")


class AdbClient:
    def __init__(self, host: str, port: int = 5555) -> None:
        self.host = host.strip()
        self.port = port
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
        result = subprocess.run([self.adb, "disconnect", self.serial], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15, check=False)
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
        allowed = (
            "getprop", "pm list packages", "settings get ", "settings put global ",
            "pm trim-caches ", "cmd package compile ", "cat /proc/meminfo",
            "df -h", "dumpsys meminfo", "dumpsys cpuinfo",
        )
        clean = command.strip()
        if not clean or not clean.startswith(allowed):
            raise AdbError("Команда заблокирована защитным списком.")
        result = self.run("shell", "sh", "-c", clean, timeout=timeout)
        output = (result.stdout + result.stderr).strip()
        if result.returncode != 0:
            raise AdbError(output or f"Команда завершилась с кодом {result.returncode}")
        return output
