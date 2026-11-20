# Electronic Detective — rules for players

A retelling of Ideal's original instructions (1979) and the suspect cards. Only what a player knows, no hints.

## The idea

A murder has been committed in a big city. The victim and the place where the body was found are known. The other
19 people have scattered around the city. You question them and look for the murderer. **The goal is to be the
first to name the murderer correctly.**

1-4 players. Each has a Case Fact Sheet and a pencil. The suspect cards lie face up and everybody uses them. The turn
passes to the left.

## The suspects

Men are 1-10, women 11-20. A card shows the number, the name and the questions this suspect may be asked.

| No. | Name | Questions | | No. | Name | Questions |
|---|---|---|---|---|---|---|
| 1 | Lenny Little | 1, 2, 9 | | 11 | Ivy Little | 6, 7, 11 |
| 2 | Al Farook | 2, 3, 9 | | 12 | Lucy Tumble | 2, 6, 11 |
| 3 | Pepe Perez | 3, 4, 5 | | 13 | Piper Perez | 3, 7, 11 |
| 4 | Tony Racheti | 4, 5, 9 | | 14 | Dina Racheti | 1, 6, 11 |
| 5 | Mickey O'Malley | 1, 4, 9 | | 15 | Eileen Stellar | 4, 7, 11 |
| 6 | Max Fineflugle | 5, 6, 12 | | 16 | Joan Fineflugle | 6, 8, 10 |
| 7 | Ripp Rapp | 2, 5, 12 | | 17 | Rose Pettle | 2, 7, 10 |
| 8 | Buster Bailey | 3, 5, 12 | | 18 | Doris Dill | 1, 8, 10 |
| 9 | Rocky Roll | 1, 5, 12 | | 19 | Candy Roll | 3, 8, 10 |
| 10 | Ling Tong | 7, 8, 12 | | 20 | Sing Wong | 4, 8, 10 |

Everybody has questions 13 and 14.

## The city

Six places: **A** Art Show, **b** Theatre, **C** Card Party, **d** Docks, **E** Embassy, **F** Factory.
Each place is on a side (**1** West Side / **2** East Side) and in an area (**3** Uptown / **4** Midtown / **5** Downtown).
There are two guns in the city: a **.38** and a **.45**. One of them is the murder weapon.

## Starting a game

1. `ON` — three "bongs" sound.
2. The level (how many private questions may be asked per turn):
   `1` Master Detective — 1, `2` Sleuth — 2, `3` Gumshoe — 3.
3. The number of players: `1`-`4`.
4. `ENTER`. Silenced shots, a funeral march; the display shows the **number of the victim** (left) and the
   **place of the body** (the letter on the right). For example, `16 A` — victim No. 16, the body at the Art Show.
5. Everybody writes this down in section 1 of the sheet. Put the victim's card away. Cross out the place of the body
   in section 2: **there are neither suspects nor weapons there**.

## A turn

**One** suspect is questioned per turn.

1. **The alibi** (everybody hears it): `SUSPECT`, the number, `ENTER`. The alibi is read aloud along the line
   under the display:

   ```
   [side] [area] [place] [companion] [companion]
    1/2   3/4/5   A-F      number      number
   ```
   "I was on the … side", "I was in the … area", "I was at the …", "I was with these suspects …".
   An alibi holds 1, 2 or 3 facts; an empty position means the suspect did not say.
   Example: `1 b 11` — "I was on the West Side, at the Theatre, with No. 11".

2. **Private questions** (only the asking player sees the answer): `PRIVATE QUESTION`, the question number, `ENTER`.
   Only questions from this suspect's card may be asked, and no more than the level allows.
   Read the answer against the card: `YES` / `NO`, `3`/`4`/`5` (area), `A`-`F` (place),
   `00 000 00` — "I don't know".

3. `END TURN`. The turn passes to the player on the left.

The same suspect may be questioned again, also after other players.
The victim cannot be questioned — the display shows `00 000 00`. The turn is not used up: choose another suspect
(in the original, `1` + `ON`, it is: press `END TURN`).

## Private questions

| No. | Question | Answer |
|---|---|---|
| 1 | Did the murderer go to the EAST SIDE? | YES / NO |
| 2 | Did a MALE do it? | YES / NO |
| 3 | What AREA did the murderer go to? | 3 / 4 / 5 |
| 4 | Was the MURDER WEAPON a .38? | YES / NO |
| 5 | Where was the .38 hidden? | A-F |
| 6 | Where was the .45 hidden? | A-F |
| 7 | Which PLACE contained only 3 suspects? | A-F |
| 8 | Did the murderer go to PLACE A, B or C? | YES / NO |
| 9 | Were you on the EAST SIDE? | YES / NO |
| 10 | Which AREA were you in? | 3 / 4 / 5 |
| 11 | Were you at PLACE A, B or C? | YES / NO |
| 12 | Were you where a WEAPON was hidden? | YES / NO |
| 13 | Are an odd-numbered suspect's PRINTS on the .38? | YES / NO / `00 000 00` |
| 14 | Are an odd-numbered suspect's PRINTS on the .45? | YES / NO / `00 000 00` |

## What the machine guarantees

1. The suspects tell the truth — **with one exception** (item 4).
2. Four places hold four suspects each: always one even and one odd man, one even and one odd woman.
   So one place never has two even or two odd suspects of the same sex.
3. The fifth place holds three suspects: two men and a woman, or two women and a man. The sixth place is the place
   of the body, empty.
4. **Prints on the murder weapon.** The parity of the suspect whose prints are on the weapon is told reliably only
   by a suspect who (a) **is of the same sex as the murderer** and (b) **went where the murder weapon is**.
   Other suspects at a weapon **may lie (or may not)** about the prints — the only lie in the game.
   Where there is no weapon, questions 13 and 14 are answered "I don't know" (`00 000 00`).
5. The murderer is never at the place of the body or at a place where either gun is.

## How to solve the case

You need all the "facts of the murder" (section 1 of the sheet) — only one suspect fits them.

| What to find out | How |
|---|---|
| The murderer's sex | question 2 |
| The weapon (.38 or .45) | question 4 |
| Where the weapon is | question 5 or 6 |
| The parity of the prints on the weapon | question 13/14 to a suspect of the murderer's sex from the place where the weapon is |
| Where the murderer **could not** go | the place of the body; the places of both guns; A-C if somebody answered NO to question 8; D-F if YES |
| Where the murderer is | alibis; questions 1, 3 (about the murderer), 9, 10 (about the suspect questioned) |

You can also work by elimination: if the murderer is an odd man, and by their alibis all the odd men but one are
where the murderer cannot be, the one left is the murderer.

**The sheet:** section 1 — the facts of the murder; 2 — who was where (places, addresses, weapons); 3 — notes
(who said what); 4 — your answer. Fold the sheet between sections 2 and 3 so that the others cannot see your notes.

## The accusation

- Only **at the start of a turn**, before choosing a suspect. **One per game.** Do not show it to the others.
- `I ACCUSE`, the number, `ENTER`. The accusation ends the turn by itself.
- **Right** — a siren, the display blinks the murderer's number and `YES`. You win.
- **Wrong** — shots, a march, the display shows the real murderer; you are out.
- With several players the game goes on. If one player is left, they **must** accuse at the start of their next turn.
  If everybody has failed, the machine shows the answer itself.

## A case by its number (`9` + `ON`)

Every case has a number: it is shown in the message field at the start of the game and in the summary. To play a
particular case, press `ON` while holding `9`, type the number (1 to 9999999) and press `ENTER`. The machine
remembers the number and goes dark. Now start a game as usual (`ON` or `2` + `ON`) — it will be the chosen case;
the game after it is random again. Changed your mind — press `OFF` before the game starts: the number is forgotten.
In the two games the same number is a different case. One number is the same case on any device, so results can be
compared: tell the number to a friend, or agree to play today's date.
A case played by its number does not go to the records or the running score.

## The game of Two False Alibis (`2` + `ON`)

The shell's third game; the original cannot do this. Hold `2` and press `ON`. Everything is as in the usual game,
except one thing:

1. **Two suspects lie in their alibis**: the murderer and one more suspect who has something to hide (but not the
   murder). Each of them simply repeats somebody else's alibi: the alibi of another suspect of the same sex and the
   same parity who was at another place.
2. **Everybody answers private questions as always** — these two as well. So an alibi can be checked with a question
   about the place (9-11) to the same suspect, if their card has such a question, or by the statements of those who
   were nearby.
3. Nobody says they were where a weapon is.
4. The other 17 suspects tell the truth; the rule about prints (item 4 above) works as usual.

Catching a liar does not yet mean finding the murderer: there are two liars. Every case is checked: it can be
solved by reasoning. This game has its own records and score against par.

## The Accomplice (`3` + `ON`)

Hold `3` and press `ON`. Everything is as in the usual game, except:

1. **The murderer has an accomplice**, and the two keep to one false story: to the questions about the murderer
   (1 — east side, 2 — male, 3 — area, 8 — place A, B or C) both answer as if another suspect, an innocent one,
   had done it.
2. **Their alibis are true**, and so are all their other answers. The other 17 suspects tell the truth.
3. **Name both.** `I ACCUSE`, the number of the murderer, `ENTER` — the display shows it with `--`; then the number
   of the accomplice, `ENTER`. `YES` only if both are right, in this order. `NO` does not say which one was wrong,
   and the player is out. `END TURN` or another command key before the second `ENTER` cancels the accusation.
   At the end the display shows the murderer and the accomplice in turn.

Every case can be solved by reasoning, the pair included. This game has its own records and score against par;
the board game (`8` + `ON`) has no cases of it.

## Messages and errors

- `EE` — a wrong key sequence, a question not on the card, or an attempt to question another suspect without
  `END TURN`. Nothing can be fixed after `ENTER`, and **such an error uses up one private question of the turn**
  (checked on the ROM; the patent US 4,394,018 says the same). On the Master Detective level this is the whole turn.
- **To fix a number before `ENTER`**: type it again — the machine keeps only the last two digits — or press
  `SUSPECT` or `PRIVATE QUESTION` once more and type the number from the start. In the original (`1` + `ON`) a
  repeated `SUSPECT` shows `EE`, but the entry is not broken: what was typed is cleared, type the number and press
  `ENTER`.
- A suspect number above 20, and a question number 0 or above 14, give `EE` without losing a question.
- `END` (with a "bong") — the question limit of the turn is exceeded, or the previous player did not press
  `END TURN`. Press `END TURN`.
- Do not press `OFF` by accident — the game would be lost.
- After the right answer, the machine switches off in about 4 minutes. To look at the case some more, press
  `END TURN` (each time +4 minutes) and question the suspects as usual.
- A constant `EE` and a low buzz — the batteries are flat.
