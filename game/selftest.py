"""Headless self-check: ROM loading (folder + zip) and status decoding over a real emulated game.
    python selftest.py <ROM folder>"""
import io, os, sys, tempfile, zipfile
from board import ElecDet, IPS, load_romset
from elecdet_game import Decoder

rom = sys.argv[1]
files = load_romset(rom)
with tempfile.TemporaryDirectory() as tmp:
    z = os.path.join(tmp, 'elecdet.zip')
    with zipfile.ZipFile(z, 'w') as f:
        for n, b in files.items():
            f.writestr(n, b)
    assert load_romset(z) == files
    with zipfile.ZipFile(z, 'w') as f:
        for n, b in files.items():
            f.writestr(n, b'x' + b[1:] if n == 'mp6100a' else b)
    try:
        load_romset(z); raise AssertionError('broken zip accepted')
    except ValueError as e:
        print('broken zip ->', e)

b, d = ElecDet(files), Decoder()


def run(s): b.run(int(s * IPS))


def press(k, hold=0.15):
    d.key(k); b.set_key(k, True); run(hold); b.set_key(k, False); run(0.3)


def keys(*ks):
    for k in ks: press(k)


d.key('ON'); b.power_on(); run(6.3)
keys('3', '1'); press('ENTER', 0.3); run(5)
crime = d.status(b.display()); print(repr(b.display()), crime)
assert crime.startswith('The victim is #'), crime
run(52)                                           # funeral march
victim = d.victim
s = 1 if victim != 1 else 2
keys('SUSPECT', *str(s), 'ENTER'); run(1.5)
alibi = d.status(b.display()); print(repr(b.display()), alibi)
assert alibi.startswith('#%d ' % s) and 'I was' in alibi, alibi
keys('PQ', '2', 'ENTER'); run(1.0)
q = d.status(b.display()); print(repr(b.display()), q)
assert q.endswith('YES') or q.endswith('NO'), q
keys('PQ', '5', 'ENTER'); run(1.0)              # #1 has no question 5 -> EE (#2 neither)
ee = d.status(b.display()); print(repr(b.display()), ee)
assert ee.startswith('EE'), ee
print('sound events so far:', len(b.sound_events))
assert b.sound_events
assert d.players == 1 and not d.is_private(b.display())
d2 = Decoder()
for k in ('ON', '3', '2', 'ENTER', 'SUSPECT', '7', 'ENTER', 'PQ', '5', 'ENTER'): d2.key(k)
assert d2.players == 2 and d2.is_private('    A  ') and not d2.is_private('     EE') and not d2.is_private('')
d2.key('ENDTURN'); assert not d2.is_private('    A  ')
print('OK')

# --- score and records (pure logic) ---
from elecdet_game import Score
s1 = Score(3, 1)
assert s1.end_turn() is None                         # END TURN without questioning: not a turn
s1.suspect(); s1.question(); s1.question()
assert s1.end_turn() == 'After turn 1: 2 questions so far'
s1.suspect(); s1.question(); s1.end_turn()
s1.accused(True)
assert s1.over and s1.summary() == 'Solved after 2 turns, 3 questions.'
rec = {}
assert s1.record(rec) == 'First record for level 3.' and rec == {'3': [2, 3]}
assert s1.record({'3': [2, 4]}).startswith('New record') and s1.record({'3': [1, 9]}).startswith('Best on level 3')
s3 = Score(2, 3)
s3.suspect(); s3.question(); assert s3.end_turn() == 'Player 1 - after turn 1: 1 question so far'
s3.accused(False)                                    # player 2 accuses wrongly -> out
assert s3.cur == 2 and s3.out == [False, True, False]
s3.suspect(); s3.end_turn(); assert s3.cur == 0       # player 3 done, player 2 skipped
s3.accused(True)
assert s3.summary() == 'Case solved by Player 1: 1 turn, 1 question. Player 2: out. Player 3: 1 turn, 0 questions.'
assert s3.record({}) == ''                           # records are solo only
print('score OK')

# --- ROM selection logic (dialog replaced by a script of answers) ---
import tempfile as _tf
import elecdet_game as eg
tmpdir = _tf.mkdtemp()
eg.SETTINGS = os.path.join(tmpdir, 'settings.json')
eg.save_settings(rom=os.path.join(tmpdir, 'gone.zip'), records={'3': [4, 9]})
bad = os.path.join(tmpdir, 'bad.zip')
with zipfile.ZipFile(bad, 'w') as f:
    f.writestr('readme.txt', 'not a rom')
answers, errors = [bad, rom], []
eg.ask_rom = lambda error=None: (errors.append(error), answers.pop(0))[1]
assert eg.find_rom(None) == files
assert 'Not a folder or zip file' in errors[0] and 'Missing ROM file(s)' in errors[1], errors
assert eg.load_settings() == {'rom': rom, 'records': {'3': [4, 9]}}, eg.load_settings()
eg.save_settings(rom=os.path.join(tmpdir, 'gone.zip'))
eg.ask_rom = lambda error=None: None
try:
    eg.find_rom(None); raise AssertionError('cancel did not exit')
except SystemExit as e:
    assert 'No ROM selected' in str(e)
print('rom selection OK')

# --- key queue: instant clicks and overlapping keys must still reach the ROM ---
g = eg.Game.__new__(eg.Game)
g.files, g.board, g.decoder, g.held, g._level = files, None, Decoder(), {}, 0
g.keyq, g.cur_key, g.key_age, g.key_rest = [], None, 0, 0
g.dealer = None
g.score = g.bottom = g.final = None


def wait(s):
    for _ in range(int(s * 60)): g.emulate(1 / 60)


def click(k): g.press(k, True); g.press(k, False)     # down and up in the same frame


g.press('ON', True); wait(6.3)
click('3'); click('1'); click('ENTER'); wait(58)      # typed with no pause at all
g.press('SUSPECT', True); g.press('1', True); g.press('SUSPECT', False); g.press('1', False)   # rollover
click('2'); click('ENTER'); wait(2)
shown = g.decoder.status(g.board.display()); print(repr(g.board.display()), shown)
assert shown.startswith('#12 ') and 'I was' in shown, shown   # could be the victim: then rerun
print('key queue OK')

# --- 'no patterns' mode (Shift+ON): the shell deals the case, the ROM plays it ---
import random
from dealer import Dealer
g.press('OFF', True); g.press('ON', True, fair=True)
assert isinstance(g.dealer, Dealer)
g.dealer = Dealer(random.Random(5)); wait(6.3)
click('3'); click('1'); click('ENTER'); wait(58)
ram = g.board.cpu.ram
cols = [''.join('%x' % ram[r * 16 + c] for r in range(6)) for c in range(7)]
print('dealt table columns:', cols)
assert sorted(cols[4]) == sorted('123567') and sorted(cols[5]) == sorted('6acdef') and sorted(cols[6]) == sorted('123456')
rot = lambda t: {t[i:] + t[:i] for i in range(6)}
sw = lambda t, i, j: ''.join(t[j] if k == i else t[i] if k == j else ch for k, ch in enumerate(t))
orig = {sw(t, 0, j) for t in rot('ad6cef') for j in (0, 4, 5)}          # every letter order the ROM alone can make
assert cols[5] not in orig, 'dealer did not run'
crime = g.decoder.status(g.board.display()); print(repr(g.board.display()), crime)
v = g.decoder.victim; s2 = 1 if v != 1 else 2
click('SUSPECT'); click(str(s2)); click('ENTER'); wait(2)
shown = g.decoder.status(g.board.display()); print(repr(g.board.display()), shown)
assert shown.startswith('#%d ' % s2) and 'I was' in shown, shown
g.press('OFF', True); g.press('ON', True)
assert g.dealer is None
print('no-patterns mode OK')
