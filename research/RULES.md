# Electronic Detective (Ideal, 1979): the full rules and logic of the original

> ⚠️ **Spoilers.** All the logic of the game is here, including undocumented patterns that make the deduction
> easier. There are no solutions of particular games. A short list of only what is "useful to a player" is in
> `SPOILERS.md`.

Sources: the instructions and the cards (not included), 300 games in MAME (`data/h_*.tsv`, level 3, 1 player), the
emulator (`emu/`). Marks: **[i]** — from the instructions, not checked on the machine; **[d]** — from the data, no
exceptions; **[c]** — traced in the code/RAM. State as of 2026-11-13.

---

## 1. The world of the game

**Suspects** — 20 people: men 1-10, women 11-20. Two properties matter: sex and parity.
That gives 4 categories of 5 people (they are also the columns of the table in RAM):

| Column | Category | Numbers |
|---|---|---|
| 0 | even man | 2, 4, 6, 8, 10 |
| 1 | odd man | 1, 3, 5, 7, 9 |
| 2 | even woman | 12, 14, 16, 18, 20 |
| 3 | odd woman | 11, 13, 15, 17, 19 |

**Places** — 6: A Art Show, B Theatre, C Card Party, D Docks, E Embassy, F Factory.
Every place has an address: a side (1 West / 2 East) and an area (3 Uptown / 4 Midtown / 5 Downtown).
6 addresses = all 6 combinations, each at exactly one place **[d]**.

**Weapons** — a .38 and a .45; one of them is the murder weapon.

## 2. Keys and display

Keys: digits, `ON`, `OFF`, `SUSPECT`, `PRIVATE QUESTION`, `I ACCUSE`, `ENTER`, `END TURN`.
The display has 7 digits, read along the line under the screen.

| What is shown | Meaning |
|---|---|
| `NNp` after ENTER at the start | victim NN, place of the body p |
| alibi `[s][a][p][nn][nn]` | side 1/2, area 3/4/5, place A-F, up to two companion numbers; empty positions — not said |
| `4E5` / `N0` | YES / NO |
| `3`/`4`/`5`, `A`…`F` | an area / a place as the answer |
| `0000000` | "I don't know" (and the victim's alibi) |
| `EE` | an entry error, a question not on the card, another suspect without END TURN **[d]/[i]**; it uses up one question of the turn (emulator, `game/probe_patent.py`; the patent US 4,394,018 says the same) |
| `END` | the question limit of the turn is exceeded **[i]** |
| `NNd1d` | the accusation is wrong, NN is the real murderer **[d]** |
| `NN4E5` | the accusation is right **[d]** |

`b` and `6` look alike on the display; whether it is a letter or a digit is clear from the position **[i]**.

## 3. The course of a game

1. `ON` → three "bongs"; while they sound (~6 s) keys are ignored **[c]**.
2. Level: `1` Master Detective (1 private question per turn), `2` Sleuth (2), `3` Gumshoe (3) **[i]**.
3. The number of players `1`-`4`, then `ENTER`. Shots, a funeral march, the display shows the victim and the place
   of the body. The place of the body is empty: neither suspects nor weapons are there.
4. A player's turn: `SUSPECT` number `ENTER` → the alibi (everybody sees it); then up to N times `PRIVATE QUESTION`
   number `ENTER` (only the asking player sees it); `END TURN`. A question can be asked only if it is on the
   suspect's card. A suspect can be questioned any number of times; the answers do not change **[d]**.
5. Accusation: `I ACCUSE` number `ENTER`. Right — a siren, the player has won. Wrong — shots, a march, the player
   is out, the real murderer is shown. With several players the game goes on until somebody guesses or everybody is
   out **[i]**.

## 4. How a game is generated

### 4.1 The "who was where" table (RAM, rows 0-5) [c]

| Row | Role (fixed) |
|---|---|
| 0 | the murderer's place |
| 1 | the place of the .38 |
| 2 | the place of the .45 |
| 3 | the second place of four |
| 4 | the place of three (it also holds the victim's "slot") |
| 5 | the scene of the crime (empty) |

Columns 0-3 — the suspects' numbers by category (rows 0-4), 4 — the address, 5 — the letter of the place,
6 — the number of the alibi template (see 5.1), 9 — flags. `4:C` — the victim's category, `4:D` — the murderer's
category.

**The murderer** is the suspect in row 0 of column `4:D`. **The victim** is in row 4 of column `4:C`.
Hence every place of four has one person of each category, the place of three lacks the victim's category,
and the murderer is never at a weapon, at the place of three or at the scene of the crime — these simply follow
from the roles of the rows.

### 4.2 Where the randomness comes from [c]/[d]

There is no separate generator. While the game waits, the main loop "rolls" the table: it shifts the columns over
the rows in circles. A base-6 counter: column 0 shifts almost every tick, 1 and 5 once in 6, 2 and 4 once in 36,
3 and 6 once in 216. The result depends on the moment `ENTER` is pressed.

The cycles of the columns (order over rows 0→4, shifting round):

| Column | Cycle |
|---|---|
| 0 | 10 → 4 → 6 → 8 → 2 |
| 1 | 9 → 3 → 7 → 1 → 5 |
| 2 | 6 → 2 → 8 → 4 → 10 |
| 3 | 1 → 5 → 9 → 3 → 7 (i.e. 11, 15, 19, 13, 17) |
| 6 | templates 1 → 2 → 3 → 4 → 5 over rows 0-3 and 5; row 4 always has 6 |

Columns 3 and 6 rotate together: the alibi template of a place is tied to the odd woman in it (5.1).

The addresses (column 4) and the letters of the places (5) are pure circular shifts over all 6 rows while idle [c]:

| Column | Cycle over rows 0→5 |
|---|---|
| 4 (address) | 5 → 2 → 7 → 1 → 6 → 3 |
| 5 (letter) | A → D → B → C → E → F |

During generation, right before page 5, one permutation of rows is added to the shift; it depends on `4:D`
(the murderer's sex) and `4:C` (the parity of the victim's category) [c] (`1:24`-`1:5B`, `5:0F`-`5:48`; 400 of 400
games, `perm45.py`):

| Murderer | Letters | Addresses |
|---|---|---|
| a man | rows 0 ↔ 5 | no permutation |
| a woman, even victim | rows 0 ↔ 4 | rows 0 ↔ 4 |
| a woman, odd victim | rows 0 ↔ 4 | rows 0 ↔ 2 |

That gives 6 × 2 = 12 variants of letters and 6 × 3 = 18 variants of addresses. What it means for a player —
`SPOILERS.md` item 9.

**Who is the murderer and the victim by category** — from how long `ENTER` is held: while the key is down, `4:D`
works as a counter; during generation bits 0-1 → the murderer's category, bits 2-3 → the victim's category [c].

**The murder weapon** is set by the odd man at the .38 (row 1, column 1) [d]:
1, 5, 9 → the weapon is the .38; 3, 7 → the .45.

**Forbidden numbers** [c]: after generation column 0 is shifted only by 0, 2 or 4, so 6 and 10 are never the
victim, 4 and 8 never the murderer. The reason (found 2026-11-14, `emu/col0_parity.py`):

- In one pass of the main loop the display scan counter `7:7` makes a step (8 states, 7→0), and so does the low
  digit of the rolling counter `0:C` (6 states, 10→15). GCD(8, 6) = 2, so the parity of their sum does not change
  while idle.
- Column 0 shifts on every step of `0:C` except the carry, so its shift = `0:C` − 10 (5 ≡ 0).
- A key press is taken only on the pass where `7:7` goes 7→6 (`0:1E`…`0:69` → `1:39`), and on that pass the rolling
  is skipped: every key taken flips the parity.
- The rolling stops while handling `ENTER`, always at the same phase of the scan. After the usual start (level,
  players, `ENTER` — two keys before `ENTER`) `0:C` ∈ {10, 12, 14}: a shift of 0, 2 or 4.
- If one more key is taken before `ENTER` (for example `END TURN` before the level, or a third digit),
  `0:C` ∈ {11, 13, 15}: a shift of 1, 3 or 0. Then the ban is different: 2 and 4 are never the victim, 6 and 10
  never the murderer (60 games per variant: `31E`, `32E`, `34E` against `311E`, `T31E`, no exceptions).

### 4.2a How many games are possible [c]

Enumerated on the emulator (`emu/count_games.py`): the rolling returns to its starting state after 7776 passes
(about 9 s); within a period the table takes 5250 different states. Of them, 3150 are reachable with the usual
start (parity, see above). Every state combines with 16 pairs "murderer's category × victim's category" (how long
`ENTER` is held), and all pairs give different games:

| Start | Tables | Games |
|---|---|---|
| usual (level, players, `ENTER`) | 3150 | 50,400 |
| with an extra key before `ENTER` | 3150 | 50,400 |
| both together (1050 tables shared) | 5250 | 84,000 |

The instructions say "more than 130,000" — the machine does not give that many. A caveat: that every table meets
all 16 pairs was not enumerated in full; 400 games met all 48 combinations "pair × phase of `0:C`", and all 400
games lie within the set above.

### 4.3 Summary of invariants [d]

- Sizes of the places: 4, 4, 4, 4, 3, 0 (the empty one is the place of the body).
- A place of four has one of each category; the place of three has all but the victim's category.
- The weapons are at different places, not at the place of the body, not at the place of three, and not where the
  murderer is.
- The murderer is not at the place of three.
- The victim and the murderer can be of the same sex (157 of 300) or not.

## 5. The suspects' answers

### 5.1 Alibis [d]

An alibi is always true and does not change during a game. Which fields it reveals and which companions it names is
set by the **template of the place**; within the template, the position is given by the suspect's category.
Notation: `s` — side, `a` — area, `p` — place; "→ X" — names companions from columns X.

A place of four: the template is set by the odd woman at that place.

| odd woman (template) | column 0 | column 1 | column 2 | column 3 |
|---|---|---|---|---|
| 11 (1) | s → 1,3 | p | a → 0 | a |
| 15 (2) | p → 3 | a p | s a | s → 1,2 |
| 19 (3) | p → 1 | → 2,3 | s | a |
| 13 (4) | s a | p | → 1,3 | → 0,2 |
| 17 (5) | s p | a → 0 | → 0,1 | → 1,2 |

The place of three (template 6): positions 0 / 1 / 2 = `a p` / `s a → position 2` / `s → position 0`.
The position is the column, except that the position of the victim's category is taken by the odd woman
(unless she is the victim herself).

The two companions on the display always come in increasing column order: even man, odd man, even woman, odd woman
(1642 alibis from 300 games, no exceptions; `alibi_order.py`). At the place of three two companions are not named.

**How it works in the code [c]** (`emu/codepath.py` → `emu/codepath.txt`). Page 9 looks the number up in the table,
writes the column of the questioned suspect into cell 7 of its row and copies the row into row 6. Page B takes the
column (`6:7`) and the template (`6:6`) and through a jump table calls ready-made pieces: side (`C:60`, bit 2 of the
address `6:4`), area (`B:11`, low bits of `6:4`), place (`B:52`, letter `6:5`), a companion from column 0/1/2/3
(`B:27`, `B:0E`, `C:3D`, `C:7A`). Each companion is written to its own place in the display buffer, hence the order
by column. All 20 combinations "template × column" and all 12 for the place of three (by putting the template and the
victim into RAM) gave exactly the tables above.

### 5.2 Private questions 1-12 [d]

All answers are true. "Murderer" — about the murderer, "I" — about the suspect questioned.

| No. | Question (from the card) | Answer | On whose cards |
|---|---|---|---|
| 1 | Did the murderer go to the EAST SIDE? | YES/NO — side of the murderer's place | 1, 5, 9, 14, 18 |
| 2 | Did a MALE do it? | YES/NO — the murderer's sex | 1, 2, 7, 12, 17 |
| 3 | What AREA did the murderer go to? | 3/4/5 — area of the murderer's place | 2, 3, 8, 13, 19 |
| 4 | Was the MURDER WEAPON a .38? | YES/NO | 3, 4, 5, 15, 20 |
| 5 | Where was the .38 hidden? | A-F | 3, 4, 6, 7, 8, 9 |
| 6 | Where was the .45 hidden? | A-F | 6, 11, 12, 14, 16 |
| 7 | Which PLACE contained only 3 suspects? | A-F | 10, 11, 13, 15, 17 |
| 8 | Did the murderer go to PLACE A, B or C? | YES/NO | 10, 16, 18, 19, 20 |
| 9 | Were you on the EAST SIDE? | YES/NO — I | 1, 2, 4, 5 |
| 10 | Which AREA were you in? | 3/4/5 — I | 16, 17, 18, 19, 20 |
| 11 | Were you at PLACE A, B or C? | YES/NO — I | 11, 12, 13, 14, 15 |
| 12 | Were you where a WEAPON was hidden? | YES/NO — I | 6, 7, 8, 9, 10 |

Everybody has questions 13 and 14. A question not on the card → `EE` (the exception is the victim, see 5.4).

Which cells the handler of each question reads [c] (`emu/codepath.txt`; the working cells `5:0`, `5:1`, `5:B`,
`6:9`-`6:C` and the cell `6:N` with the question number are left out):

| Question | Reads | Meaning |
|---|---|---|
| 1, 3 | `0:4` | address of the murderer's row: side / area |
| 2 | `0:9` | the murderer's sex flag |
| 4 | `1:9` | the "weapon is the .38" flag |
| 5 | `1:5` | letter of the .38 row |
| 6 | `2:5` | letter of the .45 row |
| 7 | `4:5` | letter of the place of three |
| 8 | `0:5` | letter of the murderer's row |
| 9, 10 | `6:4` | own address: side / area |
| 11 | `6:5` | own letter |
| 12 | `6:5`, `1:5`, `2:5` | own letter against the letters of both guns |

The card check is on pages 7 (Nos. 1-9) and 8 (Nos. 10-20): the entry depends on the suspect's number in `5:0`/`5:1`.

### 5.3 Prints: questions 13 (.38) and 14 (.45) [d]

"Are an odd-numbered suspect's PRINTS on the .38 / .45?" The answer depends on where the suspect questioned is.
"Same sex" — the same sex as the murderer.

| Where the suspect is | Question | Answer |
|---|---|---|
| not at this gun | 13 or 14 | `0000000` |
| at the .45 (the weapon or not) | 14 | same sex: the murderer's parity; opposite sex: always NO |
| at the .38, the .38 is the weapon | 13 | same sex: the murderer's parity; opposite sex: always YES |
| at the .38, the .38 is not the weapon | 13 | the parity of the suspect themself: even → YES, odd → NO |

In the code [c]: question 13 compares `6:5` with `1:5`, question 14 with `2:5`; no match → `0000000`. On a match
it reads the weapon flag (`1:9` / `2:9`), the murderer's sex flag `0:9` and the working flag `5:9` (purpose not
worked out; probably the sex of the suspect questioned); only a witness of the same sex gets as far as reading `0:A`
(the low digit of the murderer's number) — hence their true answer; the others answer without `0:A`, i.e. with a
constant. The ".38 not the weapon" branch reads `1:9` and `1:0` and does not touch `0:9`/`0:A`
(games seed 1 and seed 9, `emu/codepath_prints9.txt`).

There is no lie flag in RAM: the "lie" of the opposite sex is a constant that matches the truth in about half of the
games. Hence the appearance of "a decision for the whole game". The instructions honestly speak only of a witness of
the same sex at the murder weapon (rule 4 on p. 8).

### 5.4 The victim

The alibi is `0000000` [i]/[d]. The machine does answer private questions, including questions not on the victim's
card.

The reason [c] (2026-11-14, `emu/codepath.txt`, block `victim`): having recognised the victim's number (a comparison
with `4:A`/`4:B` on page 3), the machine shows `0000000` and leaves **without updating** either the working row 6 or
the number of the questioned suspect in `5:0`/`5:1`. Private questions after that run on the old data, i.e. the victim
answers **for the previously questioned suspect**: the same card and the same answers (after No. 1 — questions 1, 2,
9 with No. 1's answers; after No. 17 — questions 2, 7, 10 with No. 17's answers). If nobody was questioned before
the victim, row 6 is empty and the number is 0: the card is like No. 20's (questions 4, 8, 10), and question 10 gives
the area of a zero address. This is a bug of the original, not a rule of its own.

## 6. Not worked out

1. ~~Permutations of the addresses and letters of places~~ — closed 2026-11-14, see 4.2.
2. ~~Why column 0 cannot shift by 1 or 3~~ — closed 2026-11-14, see 4.2.
3. ~~How many games are reachable~~ — closed 2026-11-14, see 4.2a: 50,400 with the usual start.
4. ~~The order of companions in an alibi~~ — closed 2026-11-14, see 5.1. (`EE`/`END` during a turn were checked
   2026-11-13: once the limit is used up, everything gives `END`; before that, `EE` and one question lost.)
5. ~~The rules of section 5 in the code~~ — closed 2026-11-14: alibis, questions 1-14 and the victim were checked
   against the code by RAM reads and execution paths (`emu/codepath.py`). Pages 6-8 and A were not commented line
   by line.
