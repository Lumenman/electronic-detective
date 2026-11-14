@echo off
rem Electronic Detective: double-click to play.
cd /d "%~dp0"
python -c "import pygame" >nul 2>&1 || (
  echo pygame-ce is not installed. Install it with:  python -m pip install pygame-ce
  pause
  exit /b 1
)
start "" pythonw elecdet_game.py
