# Electronic Detective, playable again

A fan project around **Electronic Detective**, the 1979 handheld deduction game by Ideal: a murder has been
committed, twenty suspects were at six places around town, and each player questions them one per turn,
collects alibis and private answers on a Case Fact Sheet, and accuses the murderer.

Here it runs on a PC or an Android phone, in two ways:

- **our own machine** (default) — a re-implementation of the device's behaviour: the same keys, display, sounds,
  questions and answers, compared key by key with the original program, but with cases dealt fairly at random;
- **the original program** — the real ROM, executed instruction by instruction by an emulator of its
  TMS0980 chip (a Python port of MAME's).

This project is not affiliated with or endorsed by Ideal or any current owner of the game. **The original ROM is
not included** and is not needed for the default game. The suspect cards are not included either: you need the
original cards or your own copy of them (the help screen lists who answers which questions).

## Features

- The keypad and the seven-digit display of the device, with its sounds; mouse, keyboard or touch.
- A status line that reads the display for you: names, places and the text of each question.
- 1-4 players; a private answer is covered until its player looks (hold `Space`, or touch the display).
- Score per turn and per game, records per level, and **par**: how many turns a methodical detective that sees
  only what you see needs for the same case.
- **Case numbers**: every case of our machine has a number; type it (`9` + `ON`) to replay a case or to give
  the same case to a friend, on any device.
- **Two False Alibis** (`2` + `ON`): a variant where the murderer and one more suspect lie about where they were;
  every case is checked by the solver to be solvable by reasoning.
- The rules in several pages, in English and Russian (`?` or `F1`).
- The original ROM on `1` + `ON`, with the display drawn by how long each segment was really lit.

## Quick start (PC)

```
python -m pip install pygame-ce
python game/elecdet_game.py
```

`game/play.bat` starts it on Windows. Press `ON`, then enter the level (1 Master Detective, 2 Sleuth,
3 Gumshoe) and the number of players, e.g. `3` `1` `ENTER`.

| Key | Button |
|---|---|
| `0`-`9` | digits |
| `S` / `Q` / `A` | SUSPECT / PRIVATE QUESTION / I ACCUSE |
| `Enter` / `T` | ENTER / END TURN |
| `O` / `X` | ON / OFF |
| `M` | sound off/on |
| `Space` | peek at a private answer |
| `F1` | rules |

For the original program, hold `1` and press `ON`; the game then asks for the MAME romset `elecdet`
(`elecdet.zip`, or a folder with `mp6100a` and the four `.pla` files, checked by their SHA1).

## Android

`android/build.sh` builds a debug apk with buildozer in WSL or Linux (see the comments in it for the packages it
needs). The phone version has our own machine only; the original ROM is not offered there.

## How the original works

`research/` is where the original's logic was recovered:

- `emu/` — the TMS0980 emulator and the board, checked against MAME traces over more than a million
  instructions, plus tools to trace, probe RAM and compare our machine with the ROM key by key;
- `dasm/` — a disassembler for the ROM (its output is not published: it is the ROM's program);
- `solver/` — the deduction solver behind par and the Two False Alibis check;
- MAME Lua scripts and the notes (`NOTES.md`, `RULES.md`, `SPOILERS.md`, in Russian).

Research scripts look for the romset in `elecdet/` next to this file, or wherever `ELECDET_ROM` points.

> ⚠️ **Spoilers.** `research/` (especially `RULES.md`, `SPOILERS.md` and `solver/`) and `game/rules.py` explain
> how cases are dealt and how they can be solved. Do not read them if you want to play fresh.

## Tests

```
cd game
python selftest.py <romset>     # headless: ROM loading, status line, score, our machine vs the rules
python test_score.py <romset>   # in a window, about 1.5 minutes each: score, multiplayer, private answers
python test_multi.py <romset>
python test_private.py <romset>
python test_touch.py            # touch layout of the phone, on a PC
```

## Folders

| Folder | What |
|---|---|
| `game/` | The game (Python + pygame-ce). Details in [`game/README.md`](game/README.md) (in Russian) |
| `android/` | Build script for the apk |
| `print/` | Generator for printable cards and a blank Case Fact Sheet (the cards need a scan of the originals, not included) |
| `research/` | Emulator, disassembler, solver, notes |
| `PLAYER_RULES.md` | The rules for players, without hints (in Russian) |

## Licenses

Our code is under the MIT license ([`LICENSE`](LICENSE)). The CPU core and board files ported from MAME are under
BSD-3-Clause ([`LICENSE-MAME`](LICENSE-MAME)); the Android pygame recipe is based on python-for-android (MIT).
Names, texts and rules of the original game belong to their owners.
