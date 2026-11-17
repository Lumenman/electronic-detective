# Electronic Detective, playable again

A fan project around **Electronic Detective**, the 1979 handheld deduction game by Ideal: play it on a PC or an
Android phone, with a re-implementation of the machine's logic, or with the original program running in an
emulator of its TMS0980 chip.

This project is not affiliated with or endorsed by Ideal or any current owner of the game. **The original ROM is
not included** and is not needed for the default game. The suspect cards are not included either: you need the
original cards, or your own copy of them.

## What is here

| Folder | What |
|---|---|
| `game/` | The game in a window (Python + pygame-ce): our own machine by default, the original ROM on `1` + `ON`. See [`game/README.md`](game/README.md) (in Russian) |
| `android/` | Build script for the Android apk (buildozer, run in WSL/Linux) |
| `print/` | Generator for printable cards and a blank Case Fact Sheet (needs a scan of the original cards, not included) |
| `research/` | How the original works: a verified Python emulator of the TMS0980 (port of MAME), a disassembler, MAME Lua scripts, a solver, notes |
| `PLAYER_RULES.md` | The rules for players, without hints (in Russian) |

> ⚠️ **Spoilers.** `research/` (especially `RULES.md`, `SPOILERS.md` and `solver/`) and `game/rules.py` explain
> how cases are dealt and how they can be solved. Do not read them if you want to play fresh.

## Quick start (PC)

```
python -m pip install pygame-ce
python game/elecdet_game.py
```

Keys: digits, `S` Suspect, `Q` Private question, `A` I accuse, `Enter`, `T` End turn, `O`/`X` On/Off,
`M` sound, `Space` peek at a private answer, `F1` rules. `game/play.bat` starts it on Windows.

For the original program, hold `1` and press `ON`; the game then asks for the MAME romset `elecdet`
(`elecdet.zip`, or a folder with `mp6100a` and the four `.pla` files). Research scripts look for it in `elecdet/`
next to this file, or wherever the `ELECDET_ROM` environment variable points.

## Licenses

Our code is under the MIT license ([`LICENSE`](LICENSE)). The CPU core and board files ported from MAME are under
BSD-3-Clause ([`LICENSE-MAME`](LICENSE-MAME)); the Android pygame recipe is based on python-for-android (MIT).
Names, texts and rules of the original game belong to their owners.
