# Electronic Detective (Ideal, 1979): recovering the logic of the original

> ⚠️ The "Mechanics" sections contain spoilers to the rules. There are no solutions of particular games here.
> Undocumented tricks for players are collected separately in `SPOILERS.md`.

A working notebook: state as of 2026-11-13 (evening), with later additions dated in the text.
Paths like `D:\claude\GAMES\...` are the author's machine. Files marked *(not published)* are kept out of the
repository: they print the ROM's program or come from material that is not ours to share.

Background jobs: no more than 2 processes on 4 cores.

## 1. What there is

| What | Where |
|---|---|
| MAME 0.289 (official build, SHA256 checked) | `D:\claude\GAMES\mame\mame.exe` (shared with another project) |
| The ROM (`mp6100a` + 4 PLAs) | `../elecdet/` *(not published)*, a copy in MAME's `roms/elecdet/` |
| Collecting statistics in MAME with Lua | `ed2.lua` (a driver with timing within a frame), `game3.lua`, `run.sh` |
| Data of 300 games from MAME (correct timing) | `data/h_*.tsv` (`data/f_*`, `g_*` — early, biased, not fit for distributions) |
| Analysis and summary | `analyze.py` → `report.txt`; `prints38.py`, `alibi_rows.py` |
| **The full rules of the original** (spoilers) | `RULES.md` |
| Rules for players (from the instructions, no spoilers) | `../PLAYER_RULES.md` |
| **Disassembler** for the TMS0980 | `dasm/tms0980_dasm.py` → `dasm/listing.txt` *(not published)* (by pages, in LFSR order) |
| Map of the code by phase | `dasm/annotated.txt` *(not published)* (I = idle, S = generation, A = alibi, Q = prints question) |
| **Emulator in Python** (an exact copy of MAME's core) | `emu/tms0980.py` (core), `emu/elecdet.py` (board: keys, display) |
| Checking the emulator against MAME | `emu/compare_trace.py`, `emu/compare_keys.py`, traces in `emu/ref/` *(not published)* |
| Analysis tools on the emulator | `emu/tracer.py` (trace with registers and RAM writes), `probe_reads.py`, `probe_writes.py`, `who_writes.py`, `sweep.py` (running games in bulk), `flipbits.py` |

### How to run
- Emulator: `cd emu; python smoke.py` (power on → 3 → 1 → ENTER → display → alibi of No. 7).
- API: `ed = ElecDet(rom_dir); ed.power_on(); ed.run_seconds(6.3); ed.keys('31'); ed.press('E'); ...; ed.display(); ed.ram()`.
  Keys: digits, `S` (Suspect), `Q` (Private Question), `A` (I Accuse), `E` (Enter), `T` (End Turn).
- Speed ≈ 1.9× real time. Generating the crime ends ~4.8 s after ENTER, then only sound (the funeral march, ~55 s).
- Important: after power-on, wait ≥ 6 s (while the "bongs" sound, keys are ignored).

### How exact the emulator is
- From reset: 225,000 instructions matched the MAME trace (A, X, Y, address).
- With key presses: 1,065,000 instructions matched (generation, alibi, question). A detail: Lua in MAME feeds key
  presses at a frame boundary (1250 instructions, phase 1246) — taken into account in `compare_keys.py`.

## 2. Mechanics (spoilers to the rules)

### Hardware
- TMS0980: ROM 2048×9 bits (16 pages × 128, the PC is a 7-bit LFSR), RAM 144 nibbles (8 rows × 16 + 16 "DAM" at `0x80-0x8F`).
- Display of 7 digits (digit0 on the right). It is scanned **by segments**: TDO outputs a segment, SETR picks the
  digits through the PLA.
- Display format: start `VVp` (victim, place); alibi `[side][area][place][companion][companion]`; YES = `4E5`,
  NO = `n0`, don't know = `0000000`, error = `EE`; accusation `N d1d` (wrong) / `N 4E5` (right).

### The "who was where" table in RAM (rows 0-5, columns 0-15)
- Columns: 0 even man (0 = 10), 1 odd man, 2 even woman (+10, 0 = 20), 3 odd woman (+10), 4 address (W: 1-3, E: 5-7;
  area 1/2/3 = Up/Mid/Down), 5 code of the place (A = 10, B = 6, C = 12, D = 13, E = 14, F = 15), 9 row flags.
- **The roles of the rows are fixed**: 0 — the murderer's place; 1 — where the .38 is; 2 — where the .45 is; 3 — the
  second place of four; 4 — the place of three (it holds the victim's "slot"); 5 — the scene of the crime.
- `4:C` — the column (category) of the victim, `4:D` — the column of the murderer. Victim = row 4 in its column,
  murderer = row 0.
- `1:9` = 2 ⇔ the murder weapon is the .38 (otherwise the .45). `0:9` — used by question 2 (the murderer's sex).
- Row 6 — the working copy of the questioned suspect's row; row 7 — the display buffer and working cells.

### "Randomness"
- There is no separate RNG. While idle, the main loop rolls the table (`1:1E`): a base-6 counter `M(0,12..15)`
  (values 10-15); column 0 shifts almost every tick, 1 and 5 once in 6, 2 and 4 once in 36, 3 and 6 once in 216.
  Columns 4/5 roll over 6 rows (including the row of the scene of the crime).
- The "who was where" deal = the moment ENTER is pressed.
- `4:D` while any key is held is a hold counter (code `0:25-0:29`). During generation (page 5, ~4.8 s after ENTER):
  bits 0-1 → the murderer's category, bits 2-3 → the victim's category. That is, **who killed whom is set by how
  long ENTER is held**.
- After generation column 0 is shifted only by 0, 2 or 4 (never 1 or 3) → Nos. 6 and 10 are never the victim, Nos. 4
  and 8 never the murderer (checked: 300 MAME games + 400 emulator games). Presumably the press is recognised only in
  some phases of the counter; the exact reason was not looked up in the code at the time (see open question 4).

### Confirmed rules (300 games, all "always")
- 4 places of 4 (one of each category), one of three (without the victim's category), the scene of the crime empty.
- Weapons at different places, not at the scene of the crime, not where the murderer is, and not at the place of three.
- The murderer is never at the place of three.
- Alibis are true and constant; 1-3 facts, no more than 2 companions.
- Questions 1-12 are true; a question not on the card → `EE`.
- Prints: a witness of the same sex at the weapon tells the truth; one of the opposite sex gives a constant
  (details in `SPOILERS.md`).
- The victim: alibi `0000000`, but answers private questions with garbage (looks like a bug).

## 3. Open questions
1. ~~The prints lie flag~~ — **closed 2026-11-13**: there is no flag, the opposite sex answers with a constant
   (13 → YES, 14 → NO). Rules in `SPOILERS.md` item 4. Check: `prints38.py`, the prints section in `report.txt`
   (`analyze.py` now prints the raw answers by question and the murderer's parity). Bit flipping:
   `emu/flipbits.py 1 rows04` → `emu/flip_rows04.txt` (nothing); `emu/permute_prints.py`, `emu/transplant.py` —
   dead ends (they compared with `n0` instead of `N0`).
2. ~~Prints on the second gun~~ — **closed**: see `SPOILERS.md` item 4 (for a .38 that is not the weapon, the answer
   depends on the witness's own parity). Where exactly this branches in the code was not looked up; a candidate is
   the read of `5:1` at `6:1B` (1 for the opposite sex, 2 for the same).
3. ~~The alibi algorithm~~ — **closed 2026-11-13**: the template of a place is set by the odd woman in it (or fixed
   for the place of three); table in `SPOILERS.md` item 7, check `alibi_rows.py`. Not traced in the code at the time
   (pages 2, 9, B).
4. ~~Why column 0 cannot shift by 1 or 3~~ — **closed 2026-11-14**: the parity of the scan counter `7:7` (8 phases)
   and of the low digit of the rolling `0:C` (6 phases) are linked; every key taken flips it. `RULES.md` 4.2,
   `emu/col0_parity.py`.
5. ~~The full space of games~~ — **closed 2026-11-14**: the rolling has a period of 7776 passes, 5250 tables,
   50,400 games with the usual start, 84,000 in all. `RULES.md` 4.2a, `emu/count_games.py`.
6. ~~Permutations of columns 4-5~~ — **closed 2026-11-14**: a circular shift + one permutation of rows during
   generation (by `4:D` and `4:C`), traced in the code (`1:24`-`1:5B`, `5:0F`-`5:48`); `RULES.md` 4.2,
   `SPOILERS.md` item 9, check `perm45.py`.
8. ~~The answer rules in the code, the victim's answers~~ — **closed 2026-11-14**: `emu/codepath.py` (RAM reads and
   handler entries for all alibi templates and questions 1-14) → `emu/codepath.txt`, `emu/codepath_prints9.txt`;
   `RULES.md` 5.1-5.4. The victim answers with the data of the previously questioned suspect (row 6 and `5:0`/`5:1`
   are not updated).
7. ~~The order of companions in an alibi~~ — **closed 2026-11-14**: by increasing column (`alibi_order.py`).

## 4. Plans
1. ~~Close open questions 1-3~~ (done 2026-11-13, from MAME statistics) with the emulator: bit flipping
   (`flipbits.py`), a trace with registers (`tracer.py`), reading the listing of the pages that matter.
2. ~~Write down the full rules~~ — **done 2026-11-13**: `RULES.md` (with spoilers). New: what sets the murder weapon
   was found (`SPOILERS.md` item 8).
3. **The shell: "Classic" ready 2026-11-13** (see `../game/README.md`; checked: several players, automatic power-off,
   choosing the ROM, play.bat). `../game/elecdet_game.py` (pygame-ce, no cards: display, a status line in English,
   keypad, sound; the ROM is a folder or elecdet.zip, checked by MAME's SHA1, the path in `game/settings.json`;
   `selftest.py` — a check without a window). The core in `game/` is a copy of `emu/tms0980.py` with LFSR/rev tables
   (checked against the original, ~2.6× real time). The original idea of the shell: a window of 4 areas — suspect
   cards; display + label sheet; keys; logo at the top right. Options: a `.lay` layout for MAME (no code) or our own
   interface over the emulator (the emulator is ~300 lines and ports easily). The ROM is not to be distributed.
4. If needed, speed up the emulator (now 1.9× real time): precompute the opcode handlers or move it to another language.

5. **"Classic without patterns" — prototype checked 2026-11-14**: `emu/fair.py`. The shell shuffles the table in RAM
   before generation (page D, `3:C` bit 0 still 0) and sets the weapon flag `1:9` at random after it; the ROM is not
   changed. Self-check `python fair.py 16`: 16 full games (19 alibis, all questions from the cards, 13/14,
   accusation) — 0 differences. What stays are properties of the program itself: the "clean" place of three, the
   rules of prints, the victim's answers. Built into `game/` in the `fair-mode` branch (Shift+ON, `game/dealer.py`).

6. **Solver — done 2026-11-15** (`solver/`, spoilers). `engine.py` — the rules of the original as code: from a table
   it gives all alibis and answers; checked against 300 MAME games (`python engine.py`: 0 differences). `solver.py` —
   the set of possible murderers from the observations, using only what the instructions tell the player (without
   `SPOILERS.md`).
   Result with full information (everybody questioned, every question asked): "Classic" — 400 of 400 deals are
   unambiguous; "without patterns" — 20,000 of 20,000 random deals are unambiguous, no redeal needed.
   Control: with 8 of 19 questioned, in 25 cases of 40 there are 2-5 candidates left, and the real murderer is always
   among them.
   **Estimate of the number of turns — 2026-11-15** (`solver/par.py`, results in `solver/par_stats.txt`; the
   accusation is not counted). A "methodical detective" (sees only what the player sees), 100 deals each: level 3 —
   median 7 (4-22), "Classic" the same (median 7, 4-13); level 2 — median 8 (5-28); level 1 — median 12 (9-80).
   "Ideal" (choosing with the answers known, 16 deals, level 3): median 6 (4-10). Tails of 20+ turns are a weakness of
   the procedure (it chooses badly whom to go back to), not a property of the deal; the median will do as "par", for a
   single case the procedure needs improving. Slow: ~5 s per case (level 3), "ideal" ~1.5 min.
   Not done: our own engine as a game mode, new rules (waiting for discussion).
   **The procedure improved 2026-11-16**: each turn goes to the suspect whose alibi and questions can still tell
   something; what is known is not asked; questions are chosen after the alibi; `solver.suspects(worlds=...)` returns
   one possible arrangement per remaining candidate, and witnesses on whom these arrangements differ are preferred.
   The same 100 deals: level 3 — median 7, maximum 14 (was 22); "Classic" — 7, maximum 11 (13); level 2 — 8,
   maximum 13 (28); level 1 — median 10, mean 10.6, maximum 16 (was 12 / 21.6 / 80). No more tails of 20+.

7. **Our own machine (branch `own-engine`, 2026-11-15)**: `game/machine.py` + `game/rules.py` + `game/sounds.py`; the
   original stays on `Shift+ON`. Checking against the ROM: `emu/diff_machine.py` (random keys, one case, comparing
   the displays), step by step — `emu/step.py`, a timeline of display and sound — `emu/transcript.py`, the notes of
   the sounds — `emu/sounds.py`, which questions are taken — `emu/cards_probe.py`.
   What was found about the ROM's behaviour on entry (all repeated in `machine.py`):
   - a mode key is checked when pressed: `SUSPECT` is rejected (`EE`) if somebody was already entered this turn;
     `PQ` — if `SUSPECT` was not pressed this turn; `I ACCUSE` is always taken; a rejected key does not change the
     mode, so a "second suspect" after a question is read as a question number;
   - a question number above 14 — `EE` without losing a question; with the limit used up — `END`; a question not on
     the card — `EE` and one question lost;
   - accusing any number but the murderer is wrong (including 0 and 21); an accusation resets the choice of suspect
     but not the question counter; when the case is closed (solved or everybody out), there is no question limit and
     no ban on a second suspect;
   - `SUSPECT` marks the turn when pressed (a repeated `SUSPECT` gives `EE` at once), `I ACCUSE` when pressed forgets
     the suspect of the turn (a loophole: after it another one can be chosen without `END TURN`); `PQ` is taken only
     after `SUSPECT` in this turn;
   - `ENTER` without new digits: right after a mode key — `EE` and one question lost (if any); repeated — `EE` for
     free, but `END` if the limit is used up and the display does not show `EE`; Nos. 11-15 accept question 12 beyond
     their card (`SPOILERS.md` item 10);
   - result of the check (2026-11-15): 60 of 60 new sessions of 70 keys matched; of the 44 that ever differed, 43
     matched (`emu/diff_regress.py`). The rest — seed 225 — **worked out 2026-11-16**: on `ENTER` without new digits
     the ROM takes the question number from the two rightmost positions of the display (the counter of questions
     left — `6:C`, the number taken — `6:9`; see `emu/ramstep.py`). Blank (after a mode key, `YES`, a letter, a digit,
     `END`) — an empty question: `END` if the limit is used up, otherwise `EE` and one question lost. Not a number
     (`N0`, `EE`) or `00` — `EE` for free. This replaces the rule about `ENTER` above. After the fix: 44 of 44 that
     ever differed and 120 of 120 new sessions matched.
     Our machine took one thing from this: `PQ`, `ENTER` without a number with the limit used up gives `END` (was `EE`).
     Known differences: the victim questioned before anybody else (the ROM answers garbage, the model `EE`; the
     check skips such sessions);
   - while the display blinks after an accusation, the ROM skips short presses (our machine always takes keys);
   - automatic power-off: 245 s after a right accusation with `END TURN` at the 68th second, 377 s with `END TURN` at
     the 200th (in the model: 240 s after the end of the game, `END TURN` gives another 177 s);
   - sounds: one speaker, square-wave tones; the start of a game 4.9 s (shots + march), the siren 3.7 s, a "bong" 0.36 s.

## 5. Ideas for the future: how to make the game more interesting (discussion 2026-11-13)

**An assessment of the original.** A puzzle with one solving algorithm (sex and weapon → where the weapon is → prints
from a witness of the same sex → address of the murderer's place). The difficulty comes from the question limit per
turn, incomplete cards and the race against the others. Played alone it gets boring after 5-10 games; in company it
lasts longer thanks to the race and the "noise" in the answers about the guns.

**Principle.** Keep the original untouched as the "Classic" mode (the ROM through the emulator). Build new modes on
our own implementation of the logic (that is what decoding it is for).

With almost no change to the rules:
1. A score for efficiency: the number of questionings/questions until the right accusation, a "par" per game, records.
2. A common budget of questions per game instead of a limit per turn (or a penalty for each question).
3. "Case of the day": one game (seed) for everybody, comparing results.

An "Extended" mode (changes the logic):
4. Remove the predictability of the original: a fair RNG instead of rolling the table, no "forbidden" numbers and no
   "clean" places (see `SPOILERS.md`).
5. Random cards: the set of questions of the suspects changes from game to game.
6. More lies and uncertainty: the murderer sometimes distorts the alibi, an accomplice covers up, unreliable
   witnesses mix up facts.
7. More world: more places and suspects, a third weapon, a timeline, a second murder during the game.
8. A puzzle generator: a solution exists, is unique and needs a given length of reasoning → real difficulty levels.
9. For several players: exchanging information and bluffing, an accusation costs turns, planted false evidence.

**Priority.** First 1 and 4 (cheap, and they extend solo play the most), then 5-6 (they change the character of the
deduction and need balancing; the generator of item 8 will help check solvability).

**A score for efficiency (item 1) — par done 2026-11-16**: par in turns, shown after a loss too (the author's
decision); see `../game/README.md`. The running score against par (the last 10 wins per level) — done at the same time.

**Note 2026-11-16 (preliminary, the rules still to be discussed).** A third mode with its own rules is possible:
by default — the corrected original, `Shift+ON` — the original (ROM), `Alt+ON` (say) — another game.
**Done 2026-11-16:** the mode is chosen by a held digit: `ON` — the corrected original, `1` + `ON` — the original (ROM),
`2` + `ON` — room for our own game (for now the machine does not switch on).
**The third game done 2026-11-16: `2` + `ON` — "Two False Alibis"** (the author's decision after runs on a draft).
Tried: a conspiracy with a false version in questions 1, 2, 3, 8 (`solver/frame.py`: a weak lie, 143 of 200 games do
not notice it); two false alibis with answers to match the alibis (`solver/alibi.py`: 14 turns at any level, going
round almost everybody); the same, but the answers to questions are true (`alibi.py check`: 9/10/13 turns against
7/8/10, 4% of deals redealt) — chosen; one false alibi (`one check`: a weak lie, 140 of 200). Without lies
(`solver/hard.py`): "one questioning per suspect" changes nothing at level 3 and breaks a quarter of the cases at
level 1; question use 21/16/10 — a budget of about 12 per game is possible as a hard level (not done). Figures:
`solver/*_stats.txt`. In the game: `rules.deal_lies`, `solver.lie_suspects`, `par.case_par`, `Machine(lies=True)`.
`Shift+ON` was removed (earlier in the text it is mentioned as it was).
Reason: a touch screen has no Shift (the Android apk was discussed; not started then).

**Android — done 2026-11-16, checked by the author on a phone.** Build: `wsl -e bash /mnt/d/claude/GAMES/electronic_detective/android/build.sh`
(buildozer + python-for-android in WSL, `~/elecdet_apk`), the apk goes to `android/bin` (not in git). Our own recipe
for pygame-ce 2.5.8 (`android/recipes`): the standard one takes pygame 2.1.0, which does not build with Python 3.14;
the finished package is copied by hand — a fragile spot when the build tools are updated. Sound: Android has one
output device, and pygame's mixer took it — we close it before opening our own.
The phone layout (`Game.fit`): the layout fills the screen at its resolution, keys 3 × 6 (ON/OFF/I ACCUSE on top), the
score of the game in the bottom line of the message field. Not on the phone: the ROM (`1 + ON`). Par and the running
score are counted on the phone by a thread (`ParThread`; the solver goes into the apk).
`0 + ON` on a switched-off machine clears the records and the running score (the author's decision 2026-11-16; since
2026-11-17 it asks for `ENTER` first).
Not checked: a screen with a camera cutout, a tablet / landscape screen.
**The apk signing key**: a debug key, WSL `~/.android/debug.keystore`; a copy — `android/keys/debug.keystore` (not
in git). Android updates an app only with a build of the same signature: if WSL is reinstalled, put the copy back
before building (`cp /mnt/d/claude/GAMES/electronic_detective/android/keys/debug.keystore ~/.android/`), otherwise
the app has to be removed from the phone together with its records.
**Case number — done 2026-11-17 (branch `seed`)**: every case of our machine has a number 1-9999999 = the seed of the
deal (`machine.number_rng`, the two games deal differently), shown at the start and in the summary. Entry, as the
author suggested: `9` + `ON`, the number, `ENTER` — the machine goes dark, the window keeps the number
(`Game.pending`) until the next game (`ON` or `2` + `ON`). "Case of the day" = type the date, no separate mode. A
typed number does not write records or the running score. The Two False Alibis stock is now `lies_dealt`:
`[number, deals to skip]`; the old `lies_stock` in the settings is not read. Also: while the display shows `ON`, the
message field does not react to `SUSPECT`/`PQ`/`I ACCUSE`/`END TURN` or to a wrong level (the program behaves the
same — checked); "Entering:" keeps the last 2 digits, like the display.
Random questions on the cards (item 5) can be skipped; better to change the mechanics — add lies (item 6).
The cards and the sheet are the same so far. The shell: the author gave up the window of 4 areas; the "original" look
stays.

---
The author wants to play the game themself: do not show solutions of particular games; keep the undocumented in
`SPOILERS.md`.
