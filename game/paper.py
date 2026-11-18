"""Cases on paper (SPOILERS inside the written files): a book of paragraphs for playing without the machine.

Every case takes two landscape A4 sheets. The first is an index: suspect x (alibi, the questions of the card,
I accuse) -> the number of a paragraph. The second holds the paragraphs in shuffled order; each is what the
machine would show, taken from Machine itself, so the book cannot disagree with the game. Nothing in a paragraph
says whose it is, and the answer to an accusation looks like any other YES or NO.

    python paper.py 3          three random cases of the usual game -> ../print/books/cases_....html
    python paper.py 3 lies     the same for the game of two false alibis
"""
import html, os, random, sys, time
from machine import Machine, NUMBER
from rules import CARDS

MOST = 10                                # cases in one file
BOOKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'print', 'books')
COLS = ['alibi'] + list(range(1, 15)) + ['accuse']

PAGE = '''<!doctype html><meta charset="utf-8"><title>Electronic Detective: cases on paper</title>
<style>
@page { size: A4 landscape; margin: 12mm }
body { font: 11pt/1.3 Georgia, serif; margin: 12mm; color: #000; background: #fff }
@media print { body { margin: 0 } }
section + section, .grid { page-break-before: always }
h1 { font-size: 16pt; margin: 0 0 1mm } p { margin: 0 0 2mm }
code { font-family: Consolas, 'Courier New', monospace }
table { border-collapse: collapse; width: 100%% }
th, td { border: 1px solid #000; padding: .85mm 1.5mm; text-align: center }
th.n { text-align: left; white-space: nowrap } td.v { font-style: italic }
.grid { columns: 6; column-gap: 5mm; font-size: 13pt }
.grid div { break-inside: avoid; border-bottom: 1px dotted #888; padding: .7mm 0; white-space: nowrap }
.grid b { display: inline-block; min-width: 11mm }
</style>
%s'''
CASE = '''<section><h1>Case %(number)d%(game)s</h1>
<p>The victim is #%(victim)d %(name)s; the body is at %(scene)s. Find the number in the table and read only that
paragraph on the other sheet. It is what the machine shows: <code>4E5</code> yes, <code>N0</code> no,
<code>00 000 00</code> don't know, a digit is an area, a letter is a place; an alibi reads side, area, place,
companion, companion. A dot is a dark digit. An empty cell: the question is not on this card.</p>
<table><tr><th></th>%(head)s</tr>
%(rows)s</table>
<div class="grid">
%(grid)s</div></section>
'''


def codes(number, lies):
    """{(suspect, column): the display} for every alibi, card question and accusation of a case; and its machine."""
    m = Machine(lies=lies, number=number)
    m.power_on(); m.level, m.left = 3, 1; m.start_case('31')
    m.over = True                        # a closed case answers without the limit of questions
    shown = {}
    for s in range(1, 21):
        if s == m.victim: continue
        m.active = False
        a = m.enter_suspect(s)
        shown[s, 'alibi'] = a[:3] + a[3:].replace('b', '6')     # the display has one glyph for 6 and b; paper has two
        for q in CARDS[s] + (13, 14):
            m.enter_question(q); shown[s, q] = m.shown
        shown[s, 'accuse'] = '  4E5  ' if s == m.murderer else '     N0'    # not the machine's show: like any answer
    return shown, m


def face(key, text):
    """The seven digits in the groups the player rules print them in; a dot for a dark digit."""
    t, (a, b) = text.replace(' ', '·'), (3, 5) if key[1] == 'alibi' else (2, 5)
    return ' '.join((t[:a], t[a:b], t[b:]))


def book(number, lies, names):
    shown, m = codes(number, lies)
    keys = sorted(shown, key=str)
    random.Random(number * 2 + lies).shuffle(keys)              # a paragraph number says nothing about what is asked
    para = {k: i + 1 for i, k in enumerate(keys)}
    rows = ''
    for s in range(1, 21):
        cells = ('<td colspan="%d" class="v">the victim</td>' % len(COLS) if s == m.victim else
                 ''.join('<td>%s</td>' % para.get((s, c), '') for c in COLS))
        rows += '<tr><th class="n">%d %s</th>%s</tr>\n' % (s, html.escape(names[s - 1]), cells)
    return CASE % {
        'number': number, 'game': ' &middot; Two False Alibis' if lies else '', 'victim': m.victim,
        'name': html.escape(names[m.victim - 1]), 'scene': m.obs['scene'], 'rows': rows,
        'head': ''.join('<th>%s</th>' % {'alibi': 'Alibi', 'accuse': 'I accuse'}.get(c, 'Q%s' % c) for c in COLS),
        'grid': ''.join('<div><b>%d</b> <code>%s</code></div>\n' % (para[k], face(k, shown[k])) for k in keys)}


def write(count, lies, names, folder=None, rng=None):
    """Writes a file of `count` random cases and returns its path. Two false alibis are checked by the solver
    as in the game, so they take seconds."""
    numbers = (rng or random.SystemRandom()).sample(range(1, 10 ** NUMBER), min(count, MOST))
    folder = folder or BOOKS
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, time.strftime('cases_%Y%m%d_%H%M%S') + ('_lies' if lies else '') + '.html')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(PAGE % ''.join(book(n, lies, names) for n in numbers))
    return path


if __name__ == '__main__':
    from elecdet_game import NAMES
    print(write(int(sys.argv[1]), sys.argv[2:] == ['lies'], NAMES))
