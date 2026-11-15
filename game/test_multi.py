"""Real-time GUI test of a 2-player game: wrong accusations, skipping eliminated players, final summary.
Suspect numbers come from emulator RAM and are never printed. Uses a temporary settings file.
    python test_multi.py <ROM folder>"""
import os, sys, tempfile, time
import pygame
import elecdet_game as g
from board import load_romset

g.SETTINGS = os.path.join(tempfile.mkdtemp(), 'settings.json')
CARDS = {1: [1, 2, 9], 2: [2, 3, 9], 3: [3, 4, 5]}
KEY = {'ON': pygame.K_o, 'ENTER': pygame.K_RETURN, 'SUSPECT': pygame.K_s, 'PQ': pygame.K_q, 'ENDTURN': pygame.K_t,
       'ACCUSE': pygame.K_a, **{str(i): getattr(pygame, 'K_%d' % i) for i in range(10)}}
game = g.Game(load_romset(sys.argv[1]))
results, plan, t0 = [], [], time.time()


def at(t, fn): plan.append((t, fn))


def tap(t, *keys):
    for i, k in enumerate(keys):
        at(t + i * 0.4, lambda k=k: pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=KEY[k])))
        at(t + i * 0.4 + 0.2, lambda k=k: pygame.event.post(pygame.event.Event(pygame.KEYUP, key=KEY[k])))
    return t + len(keys) * 0.4


def check(t, name, test):
    def fn():
        ok = bool(test())
        results.append(ok)
        print('%s  %s' % ('PASS' if ok else 'FAIL', name), flush=True)
        if not ok:
            print('      (status hidden: may contain the solution) bottom=%r' % game.bottom)
    at(t, fn)


def people():
    if hasattr(game.board, 'murderer'): return game.board.murderer, game.board.victim   # our own machine
    R = [game.board.cpu.ram[i * 16:(i + 1) * 16] for i in range(8)]
    who = lambda r, c: [R[r][c] or 10, R[r][c], (R[r][c] or 10) + 10, R[r][c] + 10][c]
    return who(0, R[4][0xd]), who(4, R[4][0xc])        # murderer, victim


def turn_plan():
    M, V = people()
    s = [x for x in (1, 2, 3) if x != V][:2]
    wrong = [x for x in range(1, 21) if x not in (M, V)]
    t = time.time() - t0
    t = tap(t, 'SUSPECT', str(s[0]), 'ENTER')                       # player 1
    t = tap(t + 1.5, 'PQ', str(CARDS[s[0]][0]), 'ENTER')
    t = tap(t + 1.0, 'ENDTURN')
    check(t + 0.6, 'P1 turn summary', lambda: game.bottom == 'Player 1 - after turn 1: 1 question so far')
    check(t + 0.7, 'status names Player 2', lambda: game.status == 'Player 2: SUSPECT, number, ENTER.')
    t = tap(t + 1.0, 'ACCUSE', *str(wrong[0]), 'ENTER')            # player 2, wrong
    check(t + 2.0, 'P2 wrong accusation: out, told to press END TURN',
          lambda: game.bottom == 'Player 2 is out - 0 turns, 0 questions' and game.status.startswith('NO!'))
    t = tap(t + 3.0, 'ENDTURN')
    check(t + 0.6, 'next is Player 1 (Player 2 skipped)', lambda: game.status == 'Player 1: SUSPECT, number, ENTER.')
    t = tap(t + 1.0, 'SUSPECT', str(s[1]), 'ENTER')
    check(t + 1.5, 'P1 can question after that (no EE)', lambda: 'I was' in game.status)
    t = tap(t + 1.5, 'PQ', str(CARDS[s[1]][0]), 'ENTER')
    t = tap(t + 1.0, 'ENDTURN')
    check(t + 0.6, 'P1 second turn summary', lambda: game.bottom == 'Player 1 - after turn 2: 2 questions so far')
    t = tap(t + 1.0, 'ACCUSE', *str(wrong[1]), 'ENTER')            # player 1, wrong -> all out
    summary = 'All detectives are out. Player 1: out. Player 2: out.'
    check(t + 6.0, 'all out: murderer shown and summary',
          lambda: game.status.startswith('The murderer was #') and summary in game.status and game.bottom == summary)
    check(t + 6.1, 'no record for multiplayer', lambda: 'records' not in g.load_settings() and 'records_fair' not in g.load_settings())
    at(t + 7, lambda: pygame.event.post(pygame.event.Event(pygame.QUIT)))


tap(0.5, 'ON')
tap(7.0, '3', '2', 'ENTER')
check(14.0, 'score created for level 3, 2 players', lambda: game.score and (game.score.level, game.score.n) == (3, 2))
at(66.0, turn_plan)
orig_draw = game.draw


def draw():
    orig_draw()
    now = time.time() - t0
    while plan and min(p[0] for p in plan) <= now:
        plan.sort(key=lambda p: p[0])
        plan.pop(0)[1]()


game.draw = draw
game.run()
print('%d/%d passed' % (sum(results), len(results)), flush=True)
pygame.display.quit()
os._exit(0 if results and all(results) else 1)
