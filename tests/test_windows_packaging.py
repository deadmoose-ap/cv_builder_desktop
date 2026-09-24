"""Static checks for the Windows release assets."""

from pathlib import Path
import re
import struct


ROOT = Path(__file__).resolve().parents[1]


def test_windows_icon_contains_all_required_sizes():
    icon = (ROOT / "assets" / "CVBuilder.ico").read_bytes()
    reserved, icon_type, count = struct.unpack("<HHH", icon[:6])
    assert (reserved, icon_type, count) == (0, 1, 7)

    sizes = set()
    for index in range(count):
        offset = 6 + index * 16
        width, height = icon[offset], icon[offset + 1]
        sizes.add((width or 256, height or 256))

    assert sizes == {
        (16, 16),
        (24, 24),
        (32, 32),
        (48, 48),
        (64, 64),
        (128, 128),
        (256, 256),
    }


def test_windows_release_version_and_icon_are_connected():
    spec = (ROOT / "CVBuilder.spec").read_text(encoding="utf-8")
    installer = (ROOT / "packaging" / "windows-installer.iss").read_text(
        encoding="utf-8"
    )
    version_info = (
        ROOT / "packaging" / "windows-version-info.txt"
    ).read_text(encoding="utf-8")
    build_script = (ROOT / "build_windows.ps1").read_text(encoding="utf-8")

    # The macOS spec is the reference; the test pins that the three files
    # agree, not a particular number, so a version bump needs no test edit.
    version = re.search(r"'CFBundleShortVersionString': '(\d+)\.(\d+)\.(\d+)'", spec)
    build = re.search(r"'CFBundleVersion': '(\d+)'", spec)
    assert version and build
    major, minor, patch = version.groups()
    dotted = f"{major}.{minor}.{patch}"
    number = build.group(1)
    quad = f"({major}, {minor}, {patch}, {number})"

    assert f'#define MyAppVersion "{dotted}"' in installer
    assert f'#define MyAppBuildVersion "{dotted}.{number}"' in installer
    assert "SetupIconFile=..\\assets\\CVBuilder.ico" in installer
    assert f"filevers={quad}" in version_info
    assert f"prodvers={quad}" in version_info
    assert f"StringStruct('FileVersion', '{dotted}')" in version_info
    assert f"StringStruct('ProductVersion', '{dotted}')" in version_info
    assert '--icon "assets\\CVBuilder.ico"' in build_script
    assert '--version-file "packaging\\windows-version-info.txt"' in build_script
