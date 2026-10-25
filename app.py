from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QListWidgetItem, QFileDialog
from PySide6.QtUiTools import QUiLoader

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
BACKUPS = DATA / "backups"
LOG = DATA / "operations.log"
DATA.mkdir(exist_ok=True)
BACKUPS.mkdir(exist_ok=True)


def log(message: str):
    LOG.parent.mkdir(exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S}  {message}\n")


class Adb:
    def __init__(self, executable="adb"):
        self.executable = executable

    def run(self, *args, timeout=15):
        try:
            p = subprocess.run([self.executable, *args], text=True, capture_output=True, timeout=timeout, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except FileNotFoundError:
            raise RuntimeError("ADB was not found. Install Android platform-tools and add adb.exe to PATH.")
        if p.returncode:
            raise RuntimeError(p.stderr.strip() or p.stdout.strip() or f"ADB exited with {p.returncode}")
        return p.stdout.strip()

    def devices(self):
        out = self.run("devices")
        return [line.split("\t")[0] for line in out.splitlines()[1:] if "\tdevice" in line]

    def shell(self, command):
        return self.run("shell", *command.split(), timeout=20)

    def props(self):
        raw = self.shell("getprop")
        result = {}
        for line in raw.splitlines():
            if "]:[" in line:
                k, v = line.split("]:[", 1)
                result[k.lstrip("[")] = v.rstrip("]")
        return result

    def packages(self):
        return [x.replace("package:", "", 1) for x in self.shell("pm list packages").splitlines() if x.startswith("package:")]

    def disable(self, package):
        return self.shell(f"pm disable-user --user 0 {package}")

    def enable(self, package):
        return self.shell(f"pm enable --user 0 {package}")

    def uninstall_user(self, package):
        return self.shell(f"pm uninstall --user 0 {package}")

    def install(self, apk):
        return self.run("install", "-r", apk, timeout=120)

    def reboot(self):
        return self.run("reboot", timeout=10)

    def screenshot(self, target):
        remote = "/sdcard/smarttv-toolkit-screen.png"
        self.shell(f"screencap -p {remote}")
        return self.run("pull", remote, str(target), timeout=30)


SAFE_ACTIONS = {
    "reduce_animations": [
        "settings put global window_animation_scale 0.5",
        "settings put global transition_animation_scale 0.5",
        "settings put global animator_duration_scale 0.5",
    ],
    "disable_animations": [
        "settings put global window_animation_scale 0",
        "settings put global transition_animation_scale 0",
        "settings put global animator_duration_scale 0",
    ],
}


class Worker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, fn):
        super().__init__()
        self.fn = fn

    @Slot()
    def run(self):
        try:
            self.finished.emit(self.fn())
        except Exception as e:
            self.failed.emit(str(e))


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        loader = QUiLoader()
        self.ui = loader.load(str(ROOT / "ui" / "main.ui"), self)
        if self.ui is None:
            raise RuntimeError("Unable to load ui/main.ui")
        self.setCentralWidget(self.ui)
        self.setWindowTitle("SmartTV Toolkit")
        self.resize(1500, 920)
        self.adb = Adb()
        self.device = None
        self.packages = []
        self.connect_signals()
        self.refresh()

    def connect_signals(self):
        u = self.ui
        u.nav.currentRowChanged.connect(self.page_changed)
        u.refreshButton.clicked.connect(self.refresh)
        u.connectButton.clicked.connect(self.refresh)
        u.turboButton.clicked.connect(self.turbo)
        u.cleanButton.clicked.connect(self.cleanup_view)
        u.analyzeButton.clicked.connect(self.analyze)
        u.backupButton.clicked.connect(self.backup)
        u.restoreButton.clicked.connect(self.restore)
        u.shellButton.clicked.connect(self.open_shell)
        u.rebootButton.clicked.connect(self.reboot)
        u.screenshotButton.clicked.connect(self.screenshot)
        u.appsButton.clicked.connect(self.show_apps)
        u.animationsButton.clicked.connect(self.animations)
        u.logButton.clicked.connect(self.show_log)

    def status(self, text, good=False):
        self.ui.statusLabel.setText(text)
        self.ui.statusDot.setProperty("good", good)
        self.ui.statusDot.style().unpolish(self.ui.statusDot)
        self.ui.statusDot.style().polish(self.ui.statusDot)

    def current_adb(self):
        devices = self.adb.devices()
        if not devices:
            raise RuntimeError("No Android TV detected. Enable USB/Wireless debugging and connect the TV.")
        self.device = devices[0]
        return devices[0]

    def refresh(self):
        try:
            self.current_adb()
            props = self.adb.props()
            self.packages = self.adb.packages()
            brand = props.get("ro.product.brand", "Unknown")
            model = props.get("ro.product.model", "Unknown")
            device = props.get("ro.product.device", "Unknown")
            android = props.get("ro.build.version.release", "Unknown")
            sdk = props.get("ro.build.version.sdk", "Unknown")
            self.ui.brandValue.setText(brand)
            self.ui.modelValue.setText(model)
            self.ui.deviceValue.setText(device)
            self.ui.androidValue.setText(android)
            self.ui.sdkValue.setText(sdk)
            self.ui.packageValue.setText(str(len(self.packages)))
            self.status(f"Connected • {self.device}", True)
            self.ui.deviceCard.setVisible(True)
            log(f"Connected: {brand} {model} / {device}")
        except Exception as e:
            self.device = None
            self.status("Not connected", False)
            self.ui.brandValue.setText("—")
            self.ui.modelValue.setText("—")
            self.ui.deviceValue.setText("—")
            self.ui.androidValue.setText("—")
            self.ui.sdkValue.setText("—")
            self.ui.packageValue.setText("—")

    def require_device(self):
        if not self.device:
            self.current_adb()

    def run_shell_commands(self, commands):
        self.require_device()
        for command in commands:
            self.adb.shell(command)
            log(f"ADB: {command}")

    def turbo(self):
        self.require_device()
        answer = QMessageBox.question(self, "Turbo Mode", "Apply the safe performance profile?\n\nAnimations will be reduced and no apps will be uninstalled.")
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.run_shell_commands(SAFE_ACTIONS["reduce_animations"])
        self.ui.turboState.setText("Turbo Mode active")
        self.status("Turbo Mode applied", True)

    def animations(self):
        self.require_device()
        self.run_shell_commands(SAFE_ACTIONS["reduce_animations"])
        self.status("Animations optimized", True)

    def cleanup_view(self):
        self.show_apps()
        QMessageBox.information(self, "Cleanup", "Review the application list first. SmartTV Toolkit never removes packages automatically.")

    def analyze(self):
        try:
            self.require_device()
            props = self.adb.props()
            packages = self.adb.packages()
            lines = [
                f"Brand: {props.get('ro.product.brand', 'Unknown')}",
                f"Model: {props.get('ro.product.model', 'Unknown')}",
                f"Android: {props.get('ro.build.version.release', 'Unknown')} (SDK {props.get('ro.build.version.sdk', 'Unknown')})",
                f"Packages: {len(packages)}",
                "",
                "Safe recommendations:",
                "• Review unused apps before disabling them.",
                "• Reduce animations for a faster interface.",
                "• Keep launcher, TV input, Wi-Fi, Bluetooth and remote-control packages protected.",
                "• Create a backup before advanced changes.",
            ]
            self.ui.output.setPlainText("\n".join(lines))
            self.status("Analysis complete", True)
            log("System analysis completed")
        except Exception as e:
            QMessageBox.warning(self, "Analysis", str(e))

    def show_apps(self):
        try:
            self.require_device()
            self.packages = self.adb.packages()
            self.ui.output.setPlainText("\n".join(self.packages))
            self.status(f"Loaded {len(self.packages)} packages", True)
        except Exception as e:
            QMessageBox.warning(self, "Apps", str(e))

    def backup(self):
        try:
            self.require_device()
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            folder = BACKUPS / stamp
            folder.mkdir(parents=True)
            props = self.adb.props()
            (folder / "getprop.json").write_text(json.dumps(props, indent=2, ensure_ascii=False), encoding="utf-8")
            (folder / "packages.txt").write_text("\n".join(self.adb.packages()), encoding="utf-8")
            self.ui.output.setPlainText(f"Backup created:\n{folder}")
            self.status("Backup created", True)
            log(f"Backup created: {folder}")
        except Exception as e:
            QMessageBox.warning(self, "Backup", str(e))

    def restore(self):
        folder = QFileDialog.getExistingDirectory(self, "Select backup")
        if not folder:
            return
        if not Path(folder).exists():
            return
        self.ui.output.setPlainText(f"Backup selected:\n{folder}\n\nRestore is intentionally limited to reversible settings. Package state is never blindly restored.")
        log(f"Restore selected: {folder}")

    def open_shell(self):
        try:
            self.require_device()
            if os.name == "nt":
                subprocess.Popen(["cmd.exe", "/k", self.adb.executable, "shell"])
            else:
                subprocess.Popen([self.adb.executable, "shell"])
        except Exception as e:
            QMessageBox.warning(self, "ADB Shell", str(e))

    def reboot(self):
        try:
            self.require_device()
            if QMessageBox.question(self, "Reboot", "Reboot the TV now?") == QMessageBox.StandardButton.Yes:
                self.adb.reboot()
                self.status("Reboot command sent", True)
        except Exception as e:
            QMessageBox.warning(self, "Reboot", str(e))

    def screenshot(self):
        try:
            self.require_device()
            target, _ = QFileDialog.getSaveFileName(self, "Save screenshot", "smarttv-screen.png", "PNG (*.png)")
            if target:
                self.adb.screenshot(target)
                self.status("Screenshot saved", True)
        except Exception as e:
            QMessageBox.warning(self, "Screenshot", str(e))

    def show_log(self):
        self.ui.output.setPlainText(LOG.read_text(encoding="utf-8") if LOG.exists() else "No operations yet.")

    def page_changed(self, row):
        names = ["Home", "Connection", "System Analysis", "Optimization", "Apps", "Themes", "Tools", "Backups", "Logs"]
        if 0 <= row < len(names):
            self.ui.pageTitle.setText(names[row])


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = Window()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
