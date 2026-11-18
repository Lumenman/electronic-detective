"""Entry point of the one-file build: the game, or (started by itself with 'case', the case, the level) the par solver."""
import sys

if sys.argv[1:2] == ['case']:
    import par
    print(par.case_par(__import__('json').loads(sys.argv[2]), int(sys.argv[3])))
    sys.exit()

from elecdet_game import main

main()
