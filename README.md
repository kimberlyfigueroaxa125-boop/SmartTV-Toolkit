# SmartTV Toolkit

**Make your TV faster. Make it yours.**

SmartTV Toolkit is a Windows desktop control center for Android TV devices. It combines device inspection, ADB tools, reversible performance tuning, package review, backups, screenshots and a polished dark dashboard inspired by the approved UI concept.

## Features

- ⚡ Turbo Mode with safe animation tuning
- 🔎 System analysis: brand, model, device, Android, SDK and package count
- 🔌 ADB device detection and connection refresh
- 📦 Package inspection with explicit disable/uninstall-for-user actions
- 💾 Local device-property and package backups
- 🛠️ ADB Shell, reboot and screenshot tools
- 🎨 Midnight, Ocean and Graphite toolkit themes
- 📋 Local operation log
- 🪟 Windows `.exe` build through GitHub Actions

## Safety

SmartTV Toolkit is intentionally conservative:

- No automatic package removal
- Package changes require the user to enter the package name and confirm the operation
- `pm uninstall --user 0` is used instead of deleting APK files from firmware
- Performance changes are reversible Android settings
- Launcher, TV input, Wi-Fi, Bluetooth, audio and remote-control components are not targeted by the built-in Turbo profile
- Create a backup before advanced changes

The application cannot determine that an arbitrary package is safe merely from its name. Review the package and device behaviour before changing it.

## Run on Windows

Install Android Platform Tools so `adb.exe` is available on PATH, then:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python app.py
```

Enable **USB debugging** or **Wireless debugging** on the TV and authorize the computer when prompted.

## Build EXE

```powershell
python -m pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --clean SmartTV-Toolkit.spec
```

The executable is created at:

```text
dist/SmartTV-Toolkit.exe
```

Every push to `main` also builds a Windows artifact through GitHub Actions. Pushing a tag such as `v1.0.0` creates a GitHub Release and attaches the `.exe`.

## Project structure

```text
SmartTV-Toolkit/
├─ app.py
├─ ui/
│  └─ main.ui
├─ requirements.txt
├─ SmartTV-Toolkit.spec
└─ .github/workflows/windows.yml
```

## License

MIT
