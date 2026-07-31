# Platform packaging

## Required macOS iconset

```text
icon_16x16.png          16×16
icon_16x16@2x.png       32×32
icon_32x32.png          32×32
icon_32x32@2x.png       64×64
icon_128x128.png        128×128
icon_128x128@2x.png     256×256
icon_256x256.png        256×256
icon_256x256@2x.png     512×512
icon_512x512.png        512×512
icon_512x512@2x.png     1024×1024
```

Build ICNS deterministically with `scripts/build_icon_assets.py`. This avoids depending on
`iconutil`, which can reject otherwise valid iconsets on some macOS versions.

For PyInstaller macOS bundles, point `BUNDLE(icon=...)` to the ICNS file and verify:

```bash
plutil -p App.app/Contents/Info.plist
shasum -a 256 source.icns App.app/Contents/Resources/AppIcon.icns
codesign --verify --deep --strict App.app
```

Mount the DMG read-only and repeat the hash/version check inside it.

## Required Windows ICO

Include PNG-backed ICO frames:

```text
16, 24, 32, 48, 64, 128, 256 px
```

Pass the ICO to both:

- PyInstaller `--icon`;
- Inno Setup `SetupIconFile`.

Add Windows version resources with PyInstaller `--version-file`. Keep EXE and installer versions
synchronized.

## Cache and version behavior

Finder, Dock, Explorer, and shortcuts can cache icons. When replacing a released icon:

1. increase the application build number;
2. rebuild cleanly;
3. uninstall or replace the previous app;
4. relaunch Finder/Dock only if normal reinstall still shows the cached icon.

Do not use cache-clearing commands as a substitute for checking that the package contains the new
asset.

## Release verification

- Confirm target architecture: arm64, x64, or both.
- Confirm code signing status.
- Confirm macOS notarization status.
- Confirm all icon representations exist.
- Confirm installer contains the same version and icon as the app bundle.
- Record checksums for distributable DMG/EXE files.

