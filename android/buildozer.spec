# Trial Android package: our own machine only (no ROM, no par). Built by build.sh in WSL.
[app]
title = Electronic Detective
package.name = elecdet
package.domain = local.games
source.dir = app
source.include_exts = py
version = 0.1
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
