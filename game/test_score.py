"""Real-time GUI test of the per-turn score line, final summary and records (1 player, level 3).
The murderer is read from emulator RAM and never printed. Records go to a temporary settings file.
    python test_score.py <ROM folder>"""
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
            print('      (status hidden: may contain the solution) bottom=%r' % game.note)
    at(t, fn)


def murderer():
    if hasattr(game.board, 'murderer'): return game.board.murderer      # our own machine
    R = [game.board.cpu.ram[i * 16:(i + 1) * 16] for i in range(8)]
    c = R[4][0xd]; v = R[0][c]
    return [v or 10, v, (v or 10) + 10, v + 10][c]


def turn_plan():
    v = game.decoder.victim
    s, s2 = (1, 2) if v not in (1, 2) else (3, 3 if v != 3 else 1)
    t = time.time() - t0
    t = tap(t, 'SUSPECT', *str(s), 'ENTER')
    t = tap(t + 1.5, 'PQ', *str(CARDS[s][0]), 'ENTER')
    t = tap(t + 1.0, 'PQ', *str(CARDS[s][1]), 'ENTER')
    t = tap(t + 1.0, 'ENDTURN')
    check(t + 0.6, 'after END TURN: status shows "After turn 1: 2 questions so far" and the prompt',
          lambda: game.status == 'After turn 1: 2 questions so far. Next player: SUSPECT, number, ENTER.')
    t = tap(t + 1.0, 'SUSPECT')
    check(t + 0.3, 'first key of the next turn: the summary is gone', lambda: game.note is None and 'turn' not in game.status)
    t = tap(t + 0.2, *str(s2), 'ENTER')
    t = tap(t + 1.5, 'PQ', *str(CARDS[s2][0]), 'ENTER')
    t = tap(t + 1.0, 'ENDTURN')
    check(t + 0.6, 'second turn counted', lambda: game.status.startswith('After turn 2: 3 questions so far. '))
    t = tap(t + 1.0, 'ACCUSE', *str(murderer()), 'ENTER')
    check(t + 10.0, 'final summary in the status line',
          lambda: 'Solved after 2 turns, 3 questions.' in game.status and 'First record for level 3.' in game.status)
    check(t + 10.1, 'record saved', lambda: g.load_settings().get('records_fair') == {'3': [2, 3]})   # default mode: no patterns
    at(t + 11, lambda: pygame.event.post(pygame.event.Event(pygame.QUIT)))


tap(0.5, 'ON')
tap(7.0, '3', '1', 'ENTER')
check(14.0, 'score created for level 3, 1 player', lambda: game.score and (game.score.level, game.score.n) == (3, 1))
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
