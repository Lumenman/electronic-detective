#!/bin/bash
# Build the trial apk in WSL:   wsl -e bash /mnt/d/claude/GAMES/electronic_detective/android/build.sh
# Needs (once, as root): apt-get install -y git zip unzip openjdk-17-jdk python3-pip python3-venv autoconf automake
#   libtool pkg-config build-essential ccache cmake zlib1g-dev libncurses-dev libffi-dev libssl-dev
# Works in ~/elecdet_apk (the Windows disk is too slow and has no symlinks); the apk is copied back to android/bin.
set -e
here="$(cd "$(dirname "$0")" && pwd)"
work=~/elecdet_apk
mkdir -p "$work/app" "$here/bin"
[ -d "$work/venv" ] || python3 -m venv "$work/venv"
. "$work/venv/bin/activate"
pip -q install buildozer cython setuptools
rm -f "$work"/app/*.py
for f in main elecdet_game board tms0980 machine rules sounds help_text paper; do cp "$here/../game/$f.py" "$work/app/"; done
cp /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf "$work/app/"   # the phone has no Arial
cp "$here/../research/solver/par.py" "$here/../research/solver/solver.py" "$work/app/"      # par is counted on the phone too
cp "$here/buildozer.spec" "$work/"
cp "$here/../game/icon.png" "$work/icon.png"
cp "$here/presplash.png" "$work/presplash.png"
rm -rf "$work/recipes"; cp -r "$here/recipes" "$work/"
cd "$work"
export MAKEFLAGS=-j2 CMAKE_BUILD_PARALLEL_LEVEL=2        # leave half of the cores free
buildozer android debug
cp "$(ls -t bin/*.apk | head -1)" "$here/bin/"        # only the apk just built (older versions stay in bin/ here)
ls -l "$here/bin"
