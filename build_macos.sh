#!/bin/sh
set -eu

cd "$(dirname "$0")"
DMG_NAME="${DMG_NAME:-CVBuilder-macOS.dmg}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
rm -rf build dist dmg-root "$DMG_NAME"
"$PYTHON_BIN" -c 'import tkinter as tk; assert tk.TkVersion >= 8.6, "CV Builder requires Tk 8.6 or newer for macOS packaging"'
"$PYTHON_BIN" -m PyInstaller --noconfirm --clean CVBuilder.spec

if [ -n "${APPLE_SIGN_IDENTITY:-}" ]; then
  codesign --deep --force --options runtime --timestamp --sign "$APPLE_SIGN_IDENTITY" dist/CVBuilder.app
  codesign --verify --deep --strict --verbose=2 dist/CVBuilder.app
else
  codesign --deep --force --sign - dist/CVBuilder.app
fi

mkdir dmg-root
cp -R dist/CVBuilder.app dmg-root/
ln -s /Applications dmg-root/Applications
hdiutil create -volname "CV Builder" -srcfolder dmg-root -ov -format UDZO "$DMG_NAME"

if [ -n "${APPLE_ID:-}" ] && [ -n "${APPLE_TEAM_ID:-}" ] && [ -n "${APPLE_APP_PASSWORD:-}" ]; then
  xcrun notarytool submit "$DMG_NAME" --apple-id "$APPLE_ID" --team-id "$APPLE_TEAM_ID" --password "$APPLE_APP_PASSWORD" --wait
  xcrun stapler staple "$DMG_NAME"
fi

echo "Created: $(pwd)/$DMG_NAME"
