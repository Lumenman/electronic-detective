# Undocumented behaviour of the original (MAME, ROM mp6100a, 300 games)

Read only if you do not mind hints for the deduction.

1. **The murderer is never at the place with three suspects** (0 of 300).
2. **A weapon is never at the place with three suspects** (0 of 300).
   So the "place of three" is always "clean".
3. **Nos. 6 and 10 are never the victim; Nos. 4 and 8 are never the murderer** (0 of 300, ~15 expected).
   The reason was found in the code (`RULES.md` 4.2): the counter that rolls the table is tied by parity to the
   display scan. The ban holds for the usual start (level, players, `ENTER`). If one more key is pressed before
   `ENTER` (for example `END TURN` before the level), the ban changes: Nos. 2 and 4 are never the victim, Nos. 6
   and 10 never the murderer.
   In all, the machine can produce 50,400 different games with the usual start (84,000 counting the other variant),
   not "more than 130,000".
4. **Prints (questions 13/14) — the exact rules** (300 games, no exceptions; "same sex" = the murderer's sex):
   - Question 14 at the .45 (murder weapon or not): a witness of the same sex tells the murderer's parity,
     one of the opposite sex always says `NO`.
   - Question 13 at the .38, if the .38 is the murder weapon: a witness of the same sex tells the truth, one of the
     opposite sex always says `YES`.
   - Question 13 at the .38, if the .38 is **not** the murder weapon: the answer is about the witness themself —
     even → `YES`, odd → `NO`; it says nothing about the murderer.
   Hence "a lie in 50% of games, one per game": the opposite sex answers with a constant.
   There is no lie flag in RAM (checked by flipping every bit of the working cells).
5. **What it means for play**: an answer from the opposite sex is useless; `NO` to question 13 at the .38
   or `YES` to question 14 at the .45 always comes from a witness of the murderer's sex, i.e. it is the truth about
   the parity (except question 13 at a .38 that is not the weapon). At the .45, question 14 is informative even if
   the .45 is not the weapon.
6. **The victim**: the alibi is `0000000`, but the computer does answer private questions. Traced in the code: the
   victim answers **for the previously questioned suspect** (their card, their answers), because the machine does not
   update its working data. No use to the player: questions are spent and nothing new is learnt.
7. **The alibi algorithm is fully deterministic** (300 games, no exceptions; checked by `alibi_rows.py`).
   The fields of an alibi are always true. Which fields are shown and which companions are named is set by the
   **template of the place**.
   Notation: `s` — side, `a` — area, `p` — place; "→ X" — names companions from columns X;
   columns: 0 even man, 1 odd man, 2 even woman, 3 odd woman.
   - A place of four: the template is set by **which odd woman** is there:

     | odd woman | column 0 | column 1 | column 2 | column 3 |
     |---|---|---|---|---|
     | 11 | s → 1,3 | p | a → 0 | a |
     | 13 | s a | p | → 1,3 | → 0,2 |
     | 15 | p → 3 | a p | s a | s → 1,2 |
     | 17 | s p | a → 0 | → 0,1 | → 1,2 |
     | 19 | p → 1 | → 2,3 | s | a |

   - The place of three: positions 0/1/2 = `a p` / `s a → position 2` / `s → position 0`; the victim's column is
     empty, and its position is taken by the odd woman (unless she is the victim).
   - In RAM: `5:6` (1-5) — the shift of the templates over the rows, it rotates together with column 3.
   - The two companions on the display come in increasing column order (1642 alibis, no exceptions) — the order
     tells nothing.
8. **The murder weapon** is set by the odd man at the .38: 1, 5, 9 → .38; 3, 7 → .45 (300 of 300).
9. **The letters and addresses of the places are not random** (ROM code + 400 emulator games, no exceptions;
   `perm45.py`). ⚠️ The strongest spoiler.
   The letters go round `A → D → B → C → E → F`, the addresses round `5 → 2 → 7 → 1 → 6 → 3`
   (address code: 1-3 West, 5-7 East; Uptown/Midtown/Downtown in that order).
   - **The murderer is a man.** From the letter of the place of the body, going round: the next one is the place of
     the .38, then the .45, then the second place of four, then the place of three, then the murderer's place.
   - **The murderer is a woman.** From the letter of the place of the body, going round: the next one is the place
     of three, then the .38, the .45, the second place of four, then the murderer's place.
   - So the place of the body (seen at once) and the murderer's sex (question 2) give all five roles of the places.
   - Addresses: in the same order of roles (murderer, .38, .45, the four, the three, the body) they follow each other
     round the circle of addresses; with a woman murderer, the address of the murderer's place swaps with that of the
     place of three (even victim) or of the .45 (odd victim). One known address with a known role is enough to
     recover the rest.
10. **Question 12 is accepted not only by those who have it on their card** (found 2026-11-15 by comparing our
    machine with the ROM, `emu/cards_probe.py`: all 20 suspects × 14 questions). Nos. 11-15 answer question 12
    ("Were you where a WEAPON was hidden?") although their cards do not have it; the answer is true. There are no
    other differences between the cards and the program.
