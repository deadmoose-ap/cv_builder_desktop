# dmgbuild settings for the macOS installer window.
#
# Usage (see build_macos.sh):
#   dmgbuild -s packaging/dmg_settings.py -D app=dist/CVBuilder.app "CV Builder" out.dmg
#
# dmgbuild writes the Finder layout (.DS_Store) directly, without driving
# Finder through AppleScript, so it also works on headless CI runners.
# Window size and icon centres must match tools/build_dmg_background.py.
# dmgbuild exec()s this file without __file__, so paths are relative to the
# app root, which build_macos.sh makes the working directory.

import os.path

application = defines.get("app", "dist/CVBuilder.app")  # noqa: F821
appname = os.path.basename(application)

format = "UDZO"
filesystem = "HFS+"
size = None

files = [application]
symlinks = {"Applications": "/Applications"}
icon = "assets/CVBuilder.icns"
background = "assets/dmg/background.png"

# The height includes the title bar (32 pt on macOS 26, 28 pt earlier), so
# the content area is ~420 pt; background.png is 460 pt tall to cover both.
window_rect = ((200, 160), (660, 452))
default_view = "icon-view"
show_status_bar = False
show_tab_view = False
show_toolbar = False
show_pathbar = False
show_sidebar = False
include_icon_view_settings = True

icon_size = 112
text_size = 13
label_pos = "bottom"
arrange_by = None
# Dot files are invisible by default, but show up for anyone who toggled
# hidden files in Finder (Cmd+Shift+.); park them below the visible area.
icon_locations = {
    appname: (170, 236),
    "Applications": (490, 236),
    ".background.png": (110, 620),
    ".VolumeIcon.icns": (250, 620),
    ".DS_Store": (390, 620),
    ".fseventsd": (530, 620),
}
