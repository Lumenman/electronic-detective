# Trial Android package: our own machine only (no ROM). Built by build.sh in WSL.
[app]
title = Electronic Detective
package.name = elecdet
package.domain = local.games
source.dir = app
source.include_exts = py,ttf
icon.filename = icon.png
# the start screen: like the default one (512 x 256, "Loading..."), with our icon on the colour of the game
presplash.filename = presplash.png
android.presplash_color = #ECE8DE
# the version is VERSION in game/elecdet_game.py (also shown in the window title and at the end of the help)
version.regex = VERSION = '(.*)'
version.filename = %(source.dir)s/elecdet_game.py
requirements = python3,pygame
orientation = portrait
fullscreen = 1
android.archs = arm64-v8a
# the build downloads Google's Android SDK and NDK and accepts their licence without asking
android.accept_sdk_license = True
p4a.bootstrap = sdl2
# pygame-ce instead of the toolchain's old pygame
p4a.local_recipes = recipes

[buildozer]
log_level = 2
warn_on_root = 1
