# research/solver

SPOILERS: everything here is playing logic.

Only `solver.py` and `par.py` are part of the game: the window and the phone build use them to check Two False
Alibis deals and to count par. Everything else is an experiment. It reads the game's rules (`../../game/rules.py`)
and the solver, and the game uses none of it. Each script's docstring says how to run it. Each result is in the
`*_stats.txt` file of the same name.

| File | What it checks | Result |
|---|---|---|
| `solver.py` | **game**: is a case solvable, who can still be the murderer (`suspects`, `lie_suspects`) | |
| `par.py` | **game**: turns the methodical player needs (par) | `par_stats.txt` |
| `alibi.py`, `frame.py`, `hard.py` | drafts of a third game: false alibis, a shared false story, a harder game without lies | `alibi*_stats.txt`, `frame_stats.txt`, `hard_stats.txt` |
| `lies_unsolvable.py` | Two False Alibis: which deals cannot be solved, and why | `lies_unsolvable_stats.txt` |
| `lies_twin.py` | the twin rule (a liar repeats an honest alibi of his kind), since moved into `solver.py` | `lies_twin_stats.txt` |
| `lies_par.py` | par of Two False Alibis before and after the twin rule | `lies_par_stats.txt` |
| `lies_built.py` | Two False Alibis dealt solvable by construction instead of dealt and checked | `lies_built_stats.txt` |
| `affine.py`, `affine_known.py` | paper version: columns laid out by row = (a*k + b) mod 5, with a player who knows it | `affine*_stats.txt` |
| `lcg.py` | paper version: deals from a generator that can be worked out on a 12-digit calculator | `lcg_stats.txt` |
| `depth.py`, `direct.py` | depth of deduction: which cases need trying of arrangements, not forced steps only | `depth_stats.txt`, `direct_stats.txt`, `direct_cases.json` |

`report.txt` is an old output of the fingerprint analysis.
