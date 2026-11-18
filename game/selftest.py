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
for _ in range(20): run(1 / 60); lv = b.brightness()           # steady message: lit segments full, the rest dark
assert [sum(1 << k for k in range(7) if x[k] > 0.9) for x in lv] == b.segments(), (lv, b.segments())
assert all(x < 0.1 or x > 0.9 for r in lv for x in r), lv
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

# --- a read-only folder of the program: the settings go to the user's folder, and an error only if both fail ---
saved = eg.SETTINGS, eg.FALLBACK
blocked = os.path.join(tmpdir, 'file_not_folder')
open(blocked, 'w').close()                               # a file where the folder should be: no write can succeed
eg.SETTINGS, eg.FALLBACK = os.path.join(blocked, 'settings.json'), os.path.join(tmpdir, 'user', 'settings.json')
eg.save_settings(x=1)
assert eg.SETTINGS == eg.FALLBACK and eg.load_settings() == {'x': 1} and eg.SAVE_ERROR == '', eg.SAVE_ERROR
eg.SETTINGS = eg.FALLBACK = os.path.join(blocked, 'settings.json')
eg.save_settings(x=2)
assert eg.SAVE_ERROR.startswith('Records and settings are not saved'), eg.SAVE_ERROR
assert not eg.writable(blocked) and eg.writable(os.path.join(tmpdir, 'new_folder'))
eg.SETTINGS, eg.FALLBACK = saved; eg.SAVE_ERROR = ''
print('read-only folder OK')

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
click('3'); click('1'); click('ENTER')                # typed before ON shows: neither the board nor the status line takes it
assert g.decoder.context == ('setup',) and not g.decoder.entry and g.score is None
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
from rules import CARDS, deal, deal_lies, observe
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
g.press('OFF', True); g.press('2', True); g.press('ON', True); g.press('2', False)    # 2 + ON: two false alibis
assert g.board.powered and g.board.lies and g.lies and not g.original and g.kind() == '_lies'
wait(3.5); click('3'); click('1'); click('ENTER'); wait(6)
lies = g.board.case['lies']; from rules import observe as _obs
true = _obs(dict(g.board.case, lies=[]))[0]['alibi']
assert lies[0][0] == g.board.murderer and all(g.board.obs['alibi'][s] == true[o] != true[s] for s, o in lies), lies
assert _obs(dict(g.board.case, lies=[]))[0]['ans'] == g.board.obs['ans']             # every answer stays true
g.press('OFF', True)
g.press('ON', True); assert g.board.powered and not g.original                         # ON alone: our machine
eg.save_settings(records_fair={'3': [4, 9]}, par_fair={'3': [1]})
g.press('OFF', True); g.press('0', True); g.press('ON', True); g.press('0', False)     # 0 + ON: asks first
assert g.wipe_ask and not g.wiped and eg.load_settings()['records_fair'] == {'3': [4, 9]}
click('ENDTURN'); assert not g.wipe_ask and eg.load_settings()['records_fair'] == {'3': [4, 9]}   # any other key: kept
g.press('0', True); g.press('ON', True); g.press('0', False); click('ENTER')            # ENTER: a clean sheet, still off
st = eg.load_settings()
assert not g.board.powered and g.wiped and st['records_fair'] == st['par_fair'] == st['records'] == {} and 'rom' in st
assert st['records_lies'] == st['par_lies'] == {}
g.press('ON', True); assert g.board.powered and not g.wiped
wait(3.5); click('3'); click('1'); click('ENTER'); wait(6)
s3 = 1 if g.decoder.victim != 1 else 2
click('SUSPECT'); click(str(s3)); click('ENTER'); wait(2)
click('ENDTURN'); click('SUSPECT'); click(str(s3)); click('ENTER'); wait(3)   # typed ahead into the bong of END TURN
assert g.board.display().strip() == 'EE' and g.decoder.context == ('turn',), (g.board.display(), g.decoder.context)
print('own machine OK')

# EE and END are not answers: they cost no question
import types
dq = Decoder()
for k in ['ON', '3', '1', 'ENTER', 'SUSPECT', '5', 'ENTER', 'PQ', '1', 'ENTER']: dq.key(k)
tq = types.SimpleNamespace(decoder=dq, score=Score(3, 1), counted=-1, final_seq=-1, rec='', numbered=True, note=None)
eg.Game.track(tq, '     EE')
for k in ['PQ', '2', 'ENTER']: dq.key(k)
eg.Game.track(tq, '    ENd')
for k in ['PQ', '3', 'ENTER']: dq.key(k)
eg.Game.track(tq, '      3'); eg.Game.track(tq, '      3')
assert tq.score.questions == [1], tq.score.questions

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

# --- the number of a case: 3 + ON asks for it; the same number must stay the same case on every device and Python ---
c1 = deal(random.Random(1)); o1, m1 = observe(c1)
assert (o1['victim'], o1['scene'], m1, c1['w38']) == (17, 'E', 6, False), 'a number no longer gives its case'
assert deal_lies(random.Random(171126))['lies'] == [[15, 13], [4, 2]]
g = eg.Game.__new__(eg.Game)
g.files, g.board, g.decoder, g.held, g._level, g.rom, g.original = files, None, Decoder(), {}, 0, None, False
g.keyq, g.cur_key, g.key_age, g.key_rest = [], None, 0, 0
g.score = g.note = g.final = None
g.d, g.counted = '', -1
g.press('9', True); g.press('ON', True); g.press('9', False); wait(3.5)     # 9 + ON: only to type the number
assert g.decoder.context == ('number',) and g.board.display() == '     0N'
click('SUSPECT'); assert not g.decoder.entry                       # ON is showing: the command keys say nothing
for ch in '90000001': click(ch)                                    # seven digits are kept, as on the display
wait(2); assert g.decoder.typing() == '0 0 0 0 0 0 1' and g.board.display().strip() == '1', g.board.display()
click('ENTER'); wait(1); g.update_status(); print(g.status)
assert not g.board.powered and g.pending == 1 and g.status.startswith('Case 1 is set.'), g.status
g.press('OFF', True); g.update_status()                            # OFF forgets it
assert g.pending is None and g.status.startswith('Switched off.'), g.status
g.press('9', True); g.press('ON', True); g.press('9', False); wait(3.5)
click('1'); click('ENTER'); wait(1); g.update_status(); assert g.pending == 1
g.press('ON', True); wait(3.5)                                     # the next game plays it
assert g.numbered and g.pending is None and g.decoder.context == ('setup',)
click('ENDTURN'); assert g.decoder.context == ('setup',)
click('5'); click('1'); click('ENTER'); wait(1)                    # no such level: still ON, no game yet
assert g.decoder.context == ('setup',) and g.score is None and g.board.display() == '     0N'
for ch in '731': click(ch)
wait(1); assert g.decoder.typing() == '3 1'                        # two digits, as on the display
click('ENTER'); wait(6)
assert g.board.case == c1 and g.score and g.decoder.context == ('crime',)
g.update_status(); print(g.status)
assert g.status.startswith('Case 1. The victim is #17 '), g.status
g.press('OFF', True); g.press('ON', True); wait(3.5)               # and the one after it is dealt at random again
assert not g.numbered and g.board.given is None
m = Machine(); m.power_on(); m.run(4 * SEC)                         # a game without a typed number has one all the same
for k in '31': m.key(k)
m.key('ENTER'); assert 0 < m.number < 10 ** 7 and m.case == deal(random.Random(m.number))
m = Machine(lies=True, number=1); m.power_on(); m.run(4 * SEC)      # the same number in the other game: another murder
for k in '31': m.key(k)
m.key('ENTER'); assert m.number == 1 and m.case['rows'] != c1['rows']
print('case number OK')

# --- cases on paper: 8 + ON takes how many, then ON or 2 + ON picks the game and writes the file; the machine stays off ---
import glob, paper, re, time
shown, mp, para = paper.paragraphs(1, False)
assert mp.case == c1 and len(shown) == 19 * 7 and sorted(para.values()) == list(range(1, 134))    # every paragraph once
assert [s for (s, c), v in shown.items() if c == 'accuse' and v == '  4E5  '] == [m1]
m = Machine(number=1); m.power_on(); m.run(4 * SEC)                 # the book against the keys: suspect 1 and his question 9
for k in ['3', '1', 'ENTER']: m.key(k)
m.run(8 * SEC)
for k in ['SUSPECT', '1', 'ENTER']: m.key(k)
assert m.shown == shown[1, 'alibi'], (m.shown, shown[1, 'alibi'])
for k in ['PQ', '9', 'ENTER']: m.key(k)
assert m.shown == shown[1, 9], (m.shown, shown[1, 9])
for lang in paper.TEXT:                                             # every text and glyph of the sheets is there
    assert paper.front(lang).count('<section') == 2
    page = paper.book(1, False, eg.NAMES, lang)
    assert page.count('<div><b>') == 133 and '%s 1<' % paper.TEXT[lang]['case'] in page
row = re.search(r'<th class="n"><b>%d</b>.*?</tr>' % m1, page).group()    # the last number of a row is the accusation
assert int(re.findall(r'<td>(\d+)</td>', row)[-1]) == para[m1, 'accuse']
paper.BOOKS = os.path.join(tmpdir, 'books')
eg.save_settings(help_lang='ru')                                    # the book speaks the language of the help
g.press('OFF', True)
g.press('8', True); g.press('ON', True); g.press('8', False); wait(3.5)
assert g.decoder.context == ('number', paper.MOST) and g.booking and paper.MOST == 10
click('5'); click('1'); click('ENTER'); wait(1); g.update_status()  # more than fifty: still asking
assert g.board.powered and g.count is None and g.status.startswith('Board game'), g.status
click('2'); click('ENTER'); wait(1); g.update_status(); print(g.status)
assert not g.board.powered and g.count == 2 and g.pending is None and g.status.startswith('2 cases to write'), g.status
g.press('2', True); g.press('ON', True); g.press('2', False)        # 2 + ON: two false alibis
for _ in range(1200):                                               # the par: seconds per case
    if 'written' in (g.printed or ''): break
    time.sleep(0.1)
g.update_status(); print(g.status)
book, = glob.glob(os.path.join(tmpdir, 'books', 'cases_*_lies_ru.html'))
text = open(book, encoding='utf-8').read()
assert text.count('<section class="case">') == 2 and 'КРАТКИЕ ПРАВИЛА' in text and 'ДВА ЛОЖНЫХ АЛИБИ</span>' in text
assert len(re.findall(r'<p class="par">ПАР .*?уровень 1 &mdash; \d+, уровень 2 &mdash; \d+, уровень 3 &mdash; \d+', text)) == 2
assert not g.board.powered and g.count is None and g.status.startswith('2 cases of two false alibis written to cases_'), g.status
assert g.status.endswith('in Russian. ON: a new case.'), g.status
eg.save_settings(help_lang='en')
g.press('8', True); g.press('ON', True); g.press('8', False); wait(3.5)
click('1'); click('ENTER'); wait(1); g.update_status(); assert g.count == 1
g.press('OFF', True); g.update_status()                             # OFF cancels
assert g.count is None and g.status.startswith('Switched off.'), g.status
g.press('ON', True); wait(3.5)                                      # and ON is a game again
assert g.board.powered and g.decoder.context == ('setup',) and not g.booking
print('cases on paper OK')
