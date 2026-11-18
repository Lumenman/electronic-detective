# Electronic Detective — the game shell

Ideal's game (1979) in a window. By default it is run by our own program (`machine.py`): the same rules, display
and sounds as the original, but the case is dealt truly at random and no ROM is needed. Switched on while `1` is
held, it runs the original: the TMS0980 emulator executes the real ROM.
Rules for players: `../PLAYER_RULES.md`. Suspect cards: paper or PDF (they are not on the screen).

## Running

1. Python 3 and `pygame-ce`: `python -m pip install pygame-ce`.
2. Double-click `play.bat` (or `python elecdet_game.py [path to the ROM]`).
3. The ROM is needed for the original only (`1` + `ON`). The first time, the program asks for MAME's
   `elecdet.zip` or a folder with `mp6100a`, `tms0980_common1_instr.pla`, `tms0980_common1_micro.pla`,
   `tms0980_common1_segment.pla`, `tms0980_elecdet_output.pla`. The files are checked against MAME's SHA1.
   The ROM is not included. The path is kept in `settings.json`; to choose another one, delete the `rom` line there.

One file without Python: `python desktop/build.py` (needs `pyinstaller`) gives `desktop/dist/ElectronicDetective.exe`
on Windows; run it in Linux (WSL will do) for a Linux binary, with `python3-tk` for the ROM dialog. The program
keeps `settings.json` and the written cases beside itself; if that folder is read-only, in `ElectronicDetective`
of the user's AppData (Windows) or `~/.config` (Linux). The build ends with a self-check: the built program must
count par like `par.py`.

## Controls

| Key | Button |
|---|---|
| `0`-`9` (and the numeric keypad) | digits |
| `S` | SUSPECT |
| `Q` | PRIVATE QUESTION |
| `A` | I ACCUSE |
| `Enter` | ENTER |
| `T` | END TURN |
| `O` / `X` | ON / OFF |
| hold `1` and press `O` (or click ON) | the original game (the ROM deals the case) |
| hold `2` and press `O` | the game of Two False Alibis |
| hold `8` and press `O` | write cases for the board game (PC only) |
| hold `9` and press `O` | choose a case by its number |
| hold `0` and press `O` (machine off) | clear the records and the running score: `ENTER` confirms, any other key cancels |
| `Space` | peek at a covered private answer |
| `M` (or the speaker icon) | sound off / on |
| `F1` (or the `?` icon) | rules |

The buttons on the screen can be clicked too. The real device misses presses shorter than ~40 ms and gets
confused if a key is pressed before the previous one is released; the shell smooths this out: every press is
held for at least 0.1 s, and keys reach the machine one at a time.

## Two modes: our own machine (default) and the original

A plain `ON` starts our own machine. To play the original, switch on while holding `1` (the `O` key or a click on
`ON`). Both choices are listed in the status line while the machine is off; during a game the mode is not shown.
To change the mode, switch off and on again.

The original has no random number generator: a deal comes from rolling a table, and that leaves patterns a player
can use (described in `../research/SPOILERS.md`). Our machine deals the case at random (`rules.py`) and runs the
game the way the original does: entry, `EE` and `END`, the question limit, the accusation, the display.

- Gone: the "forbidden" numbers of the victim and the murderer, the link between the letters and addresses of places
  and the roles, the link between the weapon or the kind of alibi and particular people, the dependence of the case
  on how long `ENTER` is held.
- Kept (these are the rules of the game): the place with three suspects and neither the murderer nor a gun,
  the rules of the answers about fingerprints.

In the original the case is fixed by the moment `ENTER` is pressed at the start and by how long it is held. The shell
passes the real hold to the ROM (at least 0.1 s, in steps of 1/60 s), so every outcome of the device stays
reachable. Held for longer than about 0.8 s, the machine goes on by itself, as the device does.
- Differences from the original (on purpose; the original itself is on `1` + `ON`):
  - `SUSPECT` pressed again before `ENTER` clears the display (the original shows `EE`, though the entry still works);
  - a rejected mode key cancels the entry: the next `ENTER` gives `EE` and costs nothing. In the original the
    previous mode stays on, and the number of the "second suspect" is read as a question number;
  - the `I ACCUSE` key does not "forget" the suspect of the turn (in the original, another one can be chosen after it
    without `END TURN`);
  - a private question can be asked only of the suspect chosen this turn; the victim cannot be questioned
    (the original answers for the previous suspect);
  - `ENTER` pressed again after an answer costs nothing (the original reads the question number from the right end
    of the display: after `YES`, a letter or a digit it is blank there, which counts as an empty question — one
    question lost);
  - questions are taken strictly from the cards (the original accepts one extra for some suspects);
  - a game does not switch itself off (the original does, about 4 minutes after the end);
  - keys are always taken (the original skips short presses while the display blinks).
- The sounds are the original's tones: measured and written down as notes in `sounds.py`.
- The records of the modes are kept apart (`records_fair` — our machine, `records` — the original).
- **`2` + `ON` — the game of Two False Alibis** (rules: `../PLAYER_RULES.md`). The same machine of ours, but the
  murderer and one more suspect lie in their alibis; everybody answers questions truthfully. The case is dealt while
  the power-on tune plays and checked by the solver (`../research/solver`): about 1 deal in 25 cannot be solved by
  reasoning and is dealt again. Without the solver the case is not checked. Records and par: `records_lies`,
  `par_lies`.
- Verification: `../research/emu/diff_machine.py` gives our machine and the ROM the same case and the same random
  keys and compares the displays after each key; for this, our machine runs in `rom_like` mode, where the
  differences above are switched off.

## What the shell adds

- **The status line** under the display — the display spelled out in English: names, places, the text of the question.
- **The cover** (2-4 players): the answer to a private question is covered; hold Space or the mouse button on the display.
- **Score**: after `END TURN` the status line shows the result of the turn with the prompt for the next player
  (or the next turn); at the end, the result of the game. The bottom of the window always shows the keys.
  A turn counts if somebody was questioned in it; a question counts if the machine answered it (not `EE`/`END`).
  A turn in which a suspect was questioned and then accused counts too.
- **Par**: at the end of a game, won or lost, the summary adds how many turns a "methodical detective" needs for this
  case (`../research/solver/par.py`; it sees only what the player sees and does not count the accusation), and for a
  solo win how many turns you are over or under it. It is counted by a separate process from the first questioning
  (a few seconds), in both modes. On the phone it takes longer: the par line joins the summary a bit later.
- **Score against par**: the difference "your turns − par" of every solo win is kept (the last 10 per level, per mode;
  `par_fair` and `par` in `settings.json`); from the second case on, the summary shows the total:
  `Your last 3 solved cases on level 3: 1 under par in total.` Lost cases are not in the total.
- **Records** (solo games, per level): fewer turns, then fewer questions; kept in `settings.json`.
- **Final summary**: hidden while you type and back after `END TURN`; it goes away with `ON` or `OFF`.
- **Help**: the `?` icon at the bottom right of the message field (also `F1` on a PC) — the rules in several pages,
  in English or Russian (`help_text.py`; turn pages with the buttons below or the arrows, language `L`, close `Esc`).
- **Two False Alibis cases are dealt ahead**: while the program is open and the machine is silent, a background thread
  deals and checks cases and keeps the next three in `settings.json` (`lies_dealt`) — a case number and how many deals
  to skip; `2` + `ON` starts a game without waiting.
- **Case number**: every case of our machine has a number (1-9999999), shown at the start (`Case 1234567. The victim
  is…`) and in the summary. Hold `9`, press `ON`, type the number, `ENTER`: the machine remembers it and goes dark, and
  the next game (`ON` or `2` + `ON`) plays that case; after that cases are random again. The number is kept while the
  program is open; `OFF` before the game forgets it. The number seeds the deal (`machine.number_rng`; the two games
  deal differently), so it is the same case on a PC and a phone; in Two False Alibis the first solvable deal of that
  seed is taken (for a typed number it is checked on the spot — the machine waits). A case chosen by its number does
  not go to the records or the running score; par is shown. For a "case of the day", agree to type the date.
  `selftest.py` keeps samples: number 1 must give the same case under any Python version.
- **Board game** (PC only): hold `8`, press `ON`, type how many cases to write (1-10), `ENTER`: the machine goes
  dark; then `ON` (the usual game) or `2` + `ON` (Two False Alibis) writes that many random cases to
  `cases_<date>_<time>.html` beside the program and stays off; `OFF` cancels. Nothing of the cases is shown on the screen.
  Open the file in a browser and print it on portrait A4 (untick "Headers and footers"); it is black and white, in
  the look of the window: the display in a frame, the keys as boxes. First come two sheets for any number of cases —
  how to read the display, and the rules in brief — then two sheets per case. The first is an index — suspect ×
  `SUSPECT`, the private questions of the card, `I ACCUSE` → the number of a paragraph; the second holds the 133
  paragraphs in shuffled order, each drawn in the seven segments exactly as the machine shows it (a dot is a dark
  digit). A paragraph does not say whose it is, and the answer to an accusation looks like any other YES or NO. The
  questions-per-turn limit is on the player's honour. The answers sheet ends with the par of the case on each level
  (counted by `..\research\solver\par.py` on half of the cores: seconds per case, under a minute for 10 cases). The case number is on both sheets, so the same case can be
  played on the machine (`9` + `ON`). The sheets are written in the language of the help (`F1`, the `RU`/`EN`
  button): names of people, places and keys stay English; a Russian file ends in `_ru`. Without the window:
  `python paper.py 3 [lies] [en|ru]`.
- **Reset**: hold `0` and press `ON` on a switched-off machine — the program asks whether to clear the records and
  the running score of all games; `ENTER` clears them, any other key cancels (the machine does not switch on).
- **Sound** off and on: the speaker icon above the `?` (also `M`); kept in `settings.json`.

## How the machine behaves (checked on the emulator)

- After `ON` the "bongs" sound for ~6 s; keys do not work meanwhile.
- One private question beyond the level → `END`; a question not on the card → `EE`.
- A wrong accusation while others are still in the game: `N0` blinks, the player is out, and the next one must press
  `END TURN` first. When everybody has failed, the machine shows the murderer (`NNd1d`).
- After the case is solved, questioning can go on; the machine switches itself off after ~4 min, `END TURN` extends it.

## Files

| File | What |
|---|---|
| `elecdet_game.py` | window, sound, reading the display, score |
| `board.py` | the board of the device and loading the ROM (for the original) |
| `machine.py` | our own machine: entry, turns, display, sound (no ROM) |
| `rules.py` | the rules: dealing a case, alibis and answers (spoilers) |
| `paper.py` | the board game: the book of paragraphs written after `8` + `ON` |
| `sounds.py` | the sounds as notes of square-wave tones (obtained with `research/emu/sounds.py`) |
| `tms0980.py` | the CPU core (a copy of `research/emu/tms0980.py` with lookup tables for speed) |
| `selftest.py` | headless check: ROM, status line, score, choosing the ROM — `python selftest.py <ROM>` |
| `test_private.py`, `test_score.py`, `test_multi.py` | checks in a window on a real game (~1.5 min each) |
| `main.py`, `test_touch.py` | the Android entry point (built by `../android/build.sh` in WSL) and a touch check on a PC |
| `probe_multi.py`, `probe_poweroff.py` | probing the machine's behaviour (several players, automatic power-off) |
| `probe_patent.py` | checking the patent's claims: `EE` (a question not on the card) uses up a question of the turn; without `END TURN` → `END`/`EE` |
