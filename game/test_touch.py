"""Touch screen path (as on Android) on the desktop: the picture is laid out for the window, each finger is a key.
    python test_touch.py"""
import os, tempfile
os.environ['ANDROID_ARGUMENT'] = os.environ['ANDROID_PRIVATE'] = tempfile.mkdtemp()
import pygame
import elecdet_game as g

_mode = pygame.display.set_mode
pygame.display.set_mode = lambda *a, **k: _mode((405, 880))     # an upright phone screen, small enough for any desktop
game = g.Game()
ww, wh = game.window.get_size()
rect = {k: r for r, _, k in game.buttons}


def finger(kind, fid, key):
    x, y = rect[key].center
    pygame.event.post(pygame.event.Event(kind, finger_id=fid, x=x / ww,
                                         y=y / wh))


steps = [lambda: (finger(pygame.FINGERDOWN, 1, '1'), finger(pygame.FINGERDOWN, 2, 'ON')),
         lambda: check('two fingers held at once', game.held.get('1') == 1 and len(game.fingers) == 2),
         lambda: check('1 + ON without a ROM: stays off', game.board is None),
         lambda: (finger(pygame.FINGERUP, 1, '1'), finger(pygame.FINGERUP, 2, 'ON')),
         lambda: finger(pygame.FINGERDOWN, 3, 'ON'),
         lambda: check('ON alone: our machine is on', game.board is not None and game.board.powered and not game.original),
         lambda: finger(pygame.FINGERUP, 3, 'ON'),
         lambda: check('all keys released', not any(game.held.values()) and not game.fingers),
         lambda: check('picture fills the window', wh - 6 <= game.buttons[-1][0].bottom + game.M <= wh and game.buttons[2][0].right + game.M >= ww - 3),
         lambda: pygame.event.post(pygame.event.Event(pygame.QUIT))]
results, frame, orig_draw = [], [0], game.draw


def check(name, ok):
    results.append(bool(ok)); print('%s  %s' % ('PASS' if ok else 'FAIL', name), flush=True)


def draw():
    orig_draw()
    frame[0] += 1
    if frame[0] % 10 == 0 and steps:
        steps.pop(0)()


game.draw = draw
game.run()
print('%d/%d passed' % (sum(results), len(results)), flush=True)
pygame.display.quit()
os._exit(0 if results and all(results) else 1)
