"""Real-time GUI test of private questions and the SPACE/mouse peek (2 players, level 3).
Drives the real window with posted pygame events; prints PASS/FAIL per step, never the answers.
    python test_private.py <ROM folder>"""
import os, sys, time
import pygame
import elecdet_game as g
from board import load_romset

CARDS = {1: [1, 2, 9], 2: [2, 3, 9], 3: [3, 4, 5], 4: [4, 5, 9]}
KEY = {'ON': pygame.K_o, 'ENTER': pygame.K_RETURN, 'SUSPECT': pygame.K_s, 'PQ': pygame.K_q, 'ENDTURN': pygame.K_t,
       'SPACE': pygame.K_SPACE, **{str(i): getattr(pygame, 'K_%d' % i) for i in range(10)}}
game = g.Game(load_romset(sys.argv[1]))
results, plan, covered = [], [], [False]
orig_cover, orig_draw = game.draw_cover, game.draw


def cover(sc):
    covered[0] = True; orig_cover(sc)


game.draw_cover = cover
t0 = time.time()


def at(t, fn): plan.append((t, fn))


def post(kind, key): pygame.event.post(pygame.event.Event(kind, key=key))


def tap(t, *keys):                       # keys 0.4 s apart, held 0.2 s
    for i, k in enumerate(keys):
        at(t + i * 0.4, lambda k=k: post(pygame.KEYDOWN, KEY[k]))
        at(t + i * 0.4 + 0.2, lambda k=k: post(pygame.KEYUP, KEY[k]))
    return t + len(keys) * 0.4


def check(t, name, want_cover, status_test=None):
    def fn():
        ok = covered[0] == want_cover and (status_test is None or status_test(game.status, game.d))
        results.append(ok)
        print('%s  %s  (cover=%s, display=%s)' % ('PASS' if ok else 'FAIL', name, covered[0],
                                                  'blank' if not game.d.strip() else 'lit'), flush=True)
    at(t, fn)


def mouse(t, down):
    at(t, lambda: pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN if down else pygame.MOUSEBUTTONUP,
                                                       button=1, pos=game.DISP.center)))


def turn_plan():
    """Built once the crime is shown, so the victim can be skipped."""
    v = game.decoder.victim
    s = 1 if v != 1 else 2
    s2 = 3 if v != 3 else 4
    q = CARDS[s]
    t = time.time() - t0
    t = tap(t, 'SUSPECT', *str(s), 'ENTER'); check(t + 1.5, 'alibi is public', False, lambda st, d: 'I was' in st)
    t = tap(t + 2, 'PQ', *str(q[0]), 'ENTER'); check(t + 1.2, 'private answer covered', True,
                                                     lambda st, d: bool(d.strip()))
    at(t + 1.5, lambda: post(pygame.KEYDOWN, KEY['SPACE']))
    check(t + 1.9, 'SPACE held: answer visible', False, lambda st, d: '->' in st)
    at(t + 2.3, lambda: post(pygame.KEYUP, KEY['SPACE']))
    check(t + 2.7, 'SPACE released: covered again', True)
    mouse(t + 3.0, True); check(t + 3.4, 'mouse held on display: visible', False)
    mouse(t + 3.8, False); check(t + 4.2, 'mouse released: covered again', True)
    t = tap(t + 4.5, 'PQ', *str(q[1]), 'ENTER'); check(t + 1.2, 'second question covered', True)
    t = tap(t + 1.5, 'PQ', *str(q[2]), 'ENTER'); check(t + 1.2, 'third question covered', True)
    t = tap(t + 1.5, 'PQ', *str(q[0]), 'ENTER'); check(t + 1.5, 'fourth question -> END, not covered', False,
                                                       lambda st, d: st.startswith('END'))
    t = tap(t + 2, 'ENDTURN'); check(t + 1.0, 'END TURN: nothing covered', False)
    t = tap(t + 1.5, 'SUSPECT', *str(s2), 'ENTER')
    t = tap(t + 2, 'PQ', '1', 'ENTER'); check(t + 1.2, 'question not on card -> EE, not covered', False,
                                              lambda st, d: st.startswith('EE'))
    at(t + 2, lambda: pygame.event.post(pygame.event.Event(pygame.QUIT)))


tap(0.5, 'ON')
tap(7.0, '3', '2', 'ENTER')                               # level 3 (3 questions), 2 players
check(14.0, 'crime shown, 2 players detected', False, lambda st, d: game.decoder.players == 2 and 'victim' in st)
at(66.0, turn_plan)                                       # after the funeral march


def draw():
    covered[0] = False
    orig_draw()
    now = time.time() - t0
    while plan and min(p[0] for p in plan) <= now:
        plan.sort(key=lambda p: p[0])
        plan.pop(0)[1]()


game.draw = draw
game.run()
print('%d/%d passed' % (sum(results), len(results)), flush=True)
pygame.display.quit()
os._exit(0 if all(results) and results else 1)
