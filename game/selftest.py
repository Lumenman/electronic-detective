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
g.rom, g.original = None, False
g.keyq, g.cur_key, g.key_age, g.key_rest = [], None, 0, 0
g.score = g.note = g.final = None


def wait(s):
    for _ in range(int(s * 60)): g.emulate(1 / 60)


def click(k): g.press(k, True); g.press(k, False)     # down and up in the same frame


g.press('1', True); g.press('ON', True); g.press('1', False); wait(6.3)   # the ROM's own deal: the same case every run
click('3'); click('1'); click('ENTER'); wait(58)      # typed with no pause at all
g.press('SUSPECT', True); g.press('1', True); g.press('SUSPECT', False); g.press('1', False)   # rollover
click('2'); click('ENTER'); wait(2)
shown = g.decoder.status(g.board.display()); print(repr(g.board.display()), shown)
assert shown.startswith('#12 ') and 'I was' in shown, shown   # could be the victim: then rerun
print('key queue OK')

# --- default mode: our own machine (no ROM), cases dealt at random ---
from machine import Machine
g.press('OFF', True); g.press('ON', True)
assert isinstance(g.board, Machine) and not g.original
wait(3.5); assert g.board.display() == '     0N', g.board.display()
click('3'); click('1'); click('ENTER'); wait(6)
crime = g.decoder.status(g.board.display()); print(repr(g.board.display()), crime)
assert crime.startswith('The victim is #'), crime
v = g.decoder.victim; s2 = 1 if v != 1 else 2
click('SUSPECT'); click(str(s2)); click('ENTER'); wait(2)
shown = g.decoder.status(g.board.display()); print(repr(g.board.display()), shown)
assert shown.startswith('#%d ' % s2) and 'I was' in shown, shown
click('ACCUSE')
for ch in str(g.board.murderer): click(ch)
click('ENTER')
loud = sum(1 for _ in range(300) if any(g.emulate(1 / 60)))           # 5 s: the siren lasts 3.7 s
assert g.board.shown.strip().endswith('4E5'), g.board.shown
assert 180 < loud < 260, loud
# the four oddities of the original that our machine leaves out
import random
from machine import SEC
from rules import CARDS, deal, observe
def play(keys, case):
    m = Machine(case=case); m.power_on(); m.run(4 * SEC)
    for k in ['3', '1', 'ENTER']: m.key(k)
    m.run(6 * SEC); out = []
    for k in keys.split():
        if k[0] == 'w': m.run(int(k[1:]) * SEC)
        else: m.key({'S': 'SUSPECT', 'Q': 'PQ', 'A': 'ACCUSE', 'E': 'ENTER', 'T': 'ENDTURN'}.get(k, k)); m.run(SEC)
        out.append(m.display().strip() if m.powered else 'off')
    return out
case = deal(random.Random(3)); obs, murderer = observe(case)
a, b = [s for s in (11, 12, 13, 14, 15, 1, 2) if s != obs['victim']][:2]
r = play('S 9 S %s E' % ' '.join(str(a)), case)
assert r[2] == '' and r[-1] not in ('EE', ''), r                       # SUSPECT again: clean screen, then the alibi
r = play('S %s E A S %s E' % (' '.join(str(a)), ' '.join(str(b))), case)
assert r[-4] == 'EE' and r[-1] == 'EE', r                              # I ACCUSE does not free another suspect
r = play('S %s E S %s E Q %d E' % (' '.join(str(a)), ' '.join(str(b)), CARDS[a][0]), case)
n = len(str(a)) + 2                                                    # keys up to the first ENTER
assert r[n] == 'EE' and r[-3 - len(str(CARDS[a][0]))] == 'EE' and r[-1] != 'EE', r   # a second suspect: refused, costs nothing
v = ' '.join(str(obs['victim']))
r = play('S %s E Q 1 3 E' % v, case)
assert r[len(v.split()) + 1] == '0000000' and r[-1] == 'EE', r         # the victim cannot be questioned
r = play('S %s E Q 1 2 E' % ' '.join(str(a)), case)
assert r[-1] == 'EE', r                                                # question 12 is not on the card of 11-15
r = play('A %s E w600 T' % ' '.join(str(murderer)), case)
assert r[-1] != 'off', r                                               # no batteries to save
print('oddities left out OK')
g.press('OFF', True); g.press('1', True); g.press('ON', True); g.press('1', False)    # 1 + ON: the ROM
assert g.original and not isinstance(g.board, Machine)
g.press('OFF', True); g.press('2', True); g.press('ON', True); g.press('2', False)    # 2 + ON: nothing yet
assert not g.board.powered
g.press('ON', True); assert g.board.powered and not g.original                         # ON alone: our machine
print('own machine OK')

# running score against par: the last differences are kept per level and summed in the final line
import types
eg.save_settings(par_fair={'3': [1, -3]})
g = eg.Game.__new__(eg.Game); g.original = False
g.score = Score(3, 1); g.score.turns[0] = 8; g.score.winner = 0
g.par = types.SimpleNamespace(poll=lambda: 0, stdout=types.SimpleNamespace(read=lambda: '7'))
assert g.par_text() == g.par_text() == (' Par for this case: 7 turns - you are 1 over par.'
                                        ' Your last 3 solved cases on level 3: 1 under par in total.')
assert eg.load_settings()['par_fair'] == {'3': [1, -3, 1]}
print('par tally OK')
