# SmartTV Toolkit

**Make your TV faster. Make it yours.**

A Windows desktop control center for Android TV: device diagnostics, reversible performance tweaks, app review, cleanup planning, and backups.

## Current status

The first UI milestone creates the dark dashboard and navigation shell. Device-specific actions are intentionally guarded until a TV is connected and inspected. No package is removed automatically.

## Run on Windows

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python app.py
```

## Build EXE

```powershell
python -m pip install pyinstaller
pyinstaller --noconfirm --clean SmartTV-Toolkit.spec
```

The executable is created under `dist/SmartTV-Toolkit.exe`.

## Safety principles

- Inspect the device before applying changes.
- Prefer reversible settings and show the changes before applying them.
- Never disable or uninstall packages automatically.
- Keep TV input, tuners, launcher recovery, Wi-Fi, Bluetooth, audio and remote-control components protected.
- Create a local operation log and backup before advanced changes.

## License

MIT
