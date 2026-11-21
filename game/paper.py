"""Case materials on paper (SPOILERS inside the written files): a book of paragraphs for playing without the machine.

The file opens with two sheets for any number of cases - how to read the display, and the rules in brief - and then
has two portrait A4 sheets per case. The first is an index: suspect x (SUSPECT, the private questions of the card,
I ACCUSE) -> the number of a paragraph. The second holds the paragraphs in shuffled order; each is the seven digits
the machine would show, taken from Machine itself and drawn in its segments, so the book cannot disagree with the
game. Nothing in a paragraph says whose it is, and the answer to an accusation looks like any other YES or NO.
The look follows the program's window in black and white: the display in a frame, the keys as boxes.

    python paper.py 3 [lies] [en|ru]     three random cases -> cases_....html beside this file
                                         (lies or another name in machine.VARIANTS: two false alibis; the language: by default that of the help)
"""
import html, json, os, random, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from help_text import QUESTIONS_EN, QUESTIONS_RU
from machine import GLYPH, MASK, NUMBER, VARIANTS, Machine, digits
from rules import CARDS

GAMES = ('fair', 'lies', 'frame', 'liar')        # the games with a book
MOST = 10                                # cases in one file: 22 sheets; the par takes seconds per case
FROZEN = getattr(sys, 'frozen', False)       # built into one file by desktop/build.py
BOOKS = os.path.dirname(sys.executable if FROZEN else os.path.abspath(__file__))   # beside the program: the place a player looks first
PAR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'research', 'solver', 'par.py')
SOLVE = [sys.executable] if FROZEN else [sys.executable, PAR]   # + 'case', case, level: the built program is its own solver
COLS = ['alibi'] + list(range(1, 15)) + ['accuse']
PLACES = dict(zip('AbCdEF', ['Art Show', 'Theatre', 'Card Party', 'Docks', 'Embassy', 'Factory']))

STYLE = '''<!doctype html><meta charset="utf-8"><title>Electronic Detective: case materials</title>
<style>
@page { size: A4 portrait; margin: 12mm }
body { font: 10.5pt/1.3 Arial, Helvetica, sans-serif; margin: 12mm; color: #000; background: #fff }
@media print { body { margin: 0 } }
section + section, .answers { page-break-before: always }
.top { display: flex; align-items: center; justify-content: space-between; border-bottom: 1.5pt solid #000;
       padding: 0 0 3mm; margin: 0 0 4mm }
.top h1 { font-size: 15pt; margin: 0; letter-spacing: .5pt } .top small { display: block; font-size: 9pt; font-weight: normal }
.game { font-size: 13pt; font-weight: bold; border: 1.5pt solid #000; border-radius: 1.5mm; padding: 1.2mm 3mm; white-space: nowrap }
h2 { font-size: 12pt; margin: 6mm 0 2.5mm } p { margin: 0 0 3mm }
.s { width: 2.5mm; height: 4.5mm; margin-right: .75mm; vertical-align: middle }
.disp, .panel { white-space: nowrap }
.panel { display: inline-block; border: 1.5pt solid #000; border-radius: 2mm; padding: 2mm 2.5mm 2mm 3.2mm; line-height: 0 }
.panel .s { width: 4.2mm; height: 7.6mm; margin-right: 1.3mm }
.status { border: 1px solid #000; border-radius: 2mm; padding: 2mm 3mm; margin: 0 0 4mm; display: flex; align-items: center; gap: 4mm }
.key { display: inline-block; border: 1pt solid #000; font-weight: bold; border-radius: 1.2mm; padding: .4mm 1.4mm;
       font-size: 9pt; white-space: nowrap }
.key.d { min-width: 3.2mm; text-align: center }
table { border-collapse: collapse; width: 100% }
th, td { border: 1px solid #000; padding: 1.75mm 1mm; text-align: center }
thead th { border: 0; padding: 0 .4mm 1.2mm } thead .key { display: block }
th.n { text-align: left; white-space: nowrap; font-weight: normal } th.n b { display: inline-block; min-width: 5.5mm }
td.v { font-style: italic }
.grid { columns: 4; column-gap: 6mm; font-size: 12.5pt }
.grid div { break-inside: avoid; border-bottom: 1px solid #aaa; padding: .55mm 0; white-space: nowrap }
.grid b { display: inline-block; min-width: 11mm }
.k th { white-space: nowrap; width: 1%; text-align: left } .k td { text-align: left } .k .s { width: 3.2mm; height: 5.8mm; margin-right: 1mm }
.big.panel { padding: 3mm 3mm 3mm 5mm } .big .s { width: 7mm; height: 12.6mm; margin-right: 2mm }
.pos { margin: 1mm 0 3mm 5mm } .pos span { display: inline-block; width: 7mm; margin-right: 2mm; text-align: center; font-size: 9pt }
.rules .cols, .rules .box { font-size: 9.5pt } .rules .cols { display: flex; gap: 8mm } .rules .cols > div { flex: 1 }
.rules .cols > div > div { margin: 0 0 3.5mm } .rules h2 { margin: 0 0 1.5mm; font-size: 11.5pt } .rules p { margin: 0 0 1.5mm }
.rules ol { margin: 0; padding-left: 5mm } .rules li { margin: 0 0 1mm } .rules table { font-size: 9pt }
.rules td, .rules th { padding: .7mm 1.2mm; text-align: left } .rules td.a { white-space: nowrap; text-align: center; width: 1% }
.par { margin: 4mm 0 0; font-weight: bold }
.grid.small { columns: 5; column-gap: 5mm; font-size: 10pt } .grid.small div { padding: .3mm 0 }
.grid.small b { min-width: 9.5mm } .grid.small .s { width: 2.2mm; height: 4mm; margin-right: .6mm }
table.pairs { font-size: 8.5pt } .pairs th, .pairs td { padding: .9mm .3mm }
td.x { background: #ccc; -webkit-print-color-adjust: exact; print-color-adjust: exact }   /* printers drop backgrounds otherwise */
col.q { width: 8.5mm } .notes col.c { width: 8.5mm }   /* columns of one kind, one width */
table.notes { font-size: 11pt } .notes th, .notes td { padding: 1.5mm .5mm } table.notes th.n { font-size: 11pt }
.pairs .corner { text-align: left; font-size: 8pt; font-weight: normal; white-space: nowrap } .pairs th.n { font-size: 8.5pt }
.howto { font-size: 9.5pt; margin: 2mm 0 3mm }
.tips { margin-top: 3mm; font-size: 9.5pt; border: 1.5pt solid #000; border-radius: 2mm; padding: 3mm } .tips h2 { margin: 0 0 1.5mm; font-size: 11.5pt } .tips p { margin: 0 0 1.5mm }
.rules .s { width: 1.9mm; height: 3.4mm; margin-right: .5mm } .rules .box { border: 1.5pt solid #000; border-radius: 2mm; padding: 3mm }
</style>
'''

# the texts of the sheets; names of people, places and keys stay as the cards and the machine have them
TEXT = {'en': {
    'sub': 'Case Materials', 'case': 'CASE', 'index': 'Index', 'answers': 'Answers', 'victim_row': 'the victim',
    'game': ('THE USUAL GAME', 'TWO FALSE ALIBIS', 'THE ACCOMPLICE', 'EVERYBODY LIES'), 'accusation': 'Accusation',
    'notes': 'Notes', 'par23': 'PAR &mdash; the turns a methodical detective needs: levels 2 &mdash; %s, 3 &mdash; %s.',
    'notes_howto': 'Cross out what an alibi or an answer rules out. Above: where each suspect was not (place, side, '
                   'area); a true answer may also leave one cell. Companions named go to &ldquo;not with&rdquo;: they '
                   'were elsewhere. Below: the address of each place. The place of the body is shaded: nobody was there.',
    'notes_groups': ('place', 'side', 'area', 'not with'), 'notes_corner': 'suspect', 'notes_addr': 'place &darr; &nbsp; side, area &rarr;',
    'to_accuse': 'To accuse, use the last sheet of the case, %s.',
    'pairs_howto': 'Find the row of the one you accuse of the murder and the column of the accomplice: the number in '
                   'that cell is a paragraph of the answers. YES only if both are right; NO does not say which one is wrong.',
    'pairs_corner': '&darr; murderer &nbsp; accomplice &rarr;', 'victim': 'The victim is #%d %s. The body was found at the %s.',
    'par': 'PAR &mdash; the turns a methodical detective needs: levels 1 &mdash; %s, 2 &mdash; %s, 3 &mdash; %s.',
    'levels': {'fair': '''<p>Agree on the level &mdash; how many private questions a turn has: <b>1</b> Master Detective
&mdash; one, <b>2</b> Sleuth &mdash; two, <b>3</b> Gumshoe &mdash; three.</p>''',
               'liar': '''<p>Agree on the level &mdash; how many private questions a turn has: <b>2</b> Sleuth &mdash; two,
<b>3</b> Gumshoe &mdash; three. (Level 1 is too long for this game.)</p>'''},
    'truth': {'fair': 'The suspects tell the truth, with one exception (item 4).',
              'lies': 'The suspects tell the truth, except item 4 and two false alibis (below).',
              'frame': 'The suspects tell the truth, except item 4 and one false story (below).',
              'liar': 'Every alibi is false (below); answers are true, except item 4.'},
    'questions': QUESTIONS_EN, 'yes_no': 'YES / NO', 'key_title': 'READING THE DISPLAY', 'rules_title': 'RULES IN BRIEF',
    'key': '''<p>Every paragraph of the book is the seven digits of the machine's display. A dot is a dark digit: nothing is shown there.</p>
<h2>%(suspect)s &nbsp;An alibi</h2>
<div>%(example)s</div>
<div class="pos">%(positions)s</div>
<p>This one reads: &ldquo;I was on the West Side, at the Theatre, with No. 16.&rdquo; A dark digit: the suspect did not say.</p>
<table class="k">
<tr><th>1st digit</th><td><b>Side</b> &mdash; %(d1)s &ldquo;I was on the West Side&rdquo;, %(d2)s &ldquo;I was on the East Side&rdquo;</td></tr>
<tr><th>2nd digit</th><td><b>Area</b> &mdash; %(d3)s &ldquo;I was Uptown&rdquo;, %(d4)s &ldquo;I was Midtown&rdquo;, %(d5)s &ldquo;I was Downtown&rdquo;</td></tr>
<tr><th>3rd digit</th><td><b>Place</b>, &ldquo;I was at the &hellip;&rdquo; &mdash; %(places)s</td></tr>
<tr><th>4th&ndash;7th digits</th><td><b>Companions</b>, &ldquo;I was with these suspects&rdquo; &mdash; one or two numbers of suspects.
A six is shown as %(six)s, the same sign as the Theatre.</td></tr>
</table>
<h2>%(pq)s %(accuse)s &nbsp;An answer</h2>
<table class="k">
<tr><th>%(yes)s</th><td>YES</td></tr>
<tr><th>%(no)s</th><td>NO</td></tr>
<tr><th>%(unknown)s</th><td>&ldquo;I don't know&rdquo; (questions 13 and 14)</td></tr>
</table>
<p style="margin-top: 3mm">An area or a place is shown in the same digit as in an alibi: an area in the 2nd, a place in the 3rd.</p>
<h2>Playing from the book</h2>
<p>On the index sheet of the case find the row of the suspect and the column: %(suspect)s for the alibi, the number of a
%(pq)s, or %(accuse)s. The cell gives the number of a paragraph. Read that paragraph on the answers sheet &mdash;
and no other. An empty cell: the question is not on this suspect's card.</p>''',
    'rules': '''<div class="cols"><div>
<div><h2>The case</h2>
<p>A murder has been committed in a big city. The victim and the place where the body was found are known. The other
19 people have scattered around the city. Question them and name the murderer. Men are 1&ndash;10, women 11&ndash;20.</p></div>
<div><h2>The city</h2>
<p>Six places: %(places)s. Each place is on a side (1 West Side, 2 East Side) and in an area (3 Uptown, 4 Midtown,
5 Downtown). Two guns are hidden in the city, a .38 and a .45, at two different places. One of them is the murder weapon.</p></div>
<div><h2>Before you start</h2>
%(levels)s
<p>Take the index sheet of a case. The display at its top shows the number of the victim and the place of the body.
Put the victim's card away. At the place of the body there are neither suspects nor guns.</p></div>
<div><h2>A turn: one suspect</h2>
<p>%(suspect)s The alibi. Find its paragraph and read it aloud: everybody hears an alibi.</p>
<p>%(pq)s Up to as many as the level allows (fewer is fine), and only those on this suspect's card (the filled cells of the row).
The answer is for your eyes only.</p>
<p>%(end)s The turn passes to the left. The same suspect may be questioned again in a later turn.</p></div>
<div><h2>%(accuse)s</h2>
<p>Only at the start of a turn, instead of questioning, and once per game. Read the paragraph of the accused:
YES &mdash; you have solved the case; NO &mdash; you are out. Playing alone, a wrong accusation loses the case.</p>
<p>Count your turns: the par of every level is at the bottom of the answers sheet.</p></div>
</div><div>
<div><h2>What is always true</h2>
<ol><li>%(truth)s</li>
<li>Four places hold four suspects each: an even and an odd man, an even and an odd woman.</li>
<li>The fifth place holds three: two men and a woman, or two women and a man. The sixth, the place of the body, is empty.</li>
<li>The prints on the murder weapon: whether they are an odd-numbered suspect's is told reliably only by a suspect
of the murderer's sex who went where that weapon is. The others at a gun may lie about the prints, or may not.
Where there is no gun, questions 13 and 14 are answered &ldquo;I don't know&rdquo;.</li>
<li>The murderer is never at the place of the body, nor at a place where a gun is.</li></ol></div>
<div><h2>The private questions</h2>
<table>%(questions)s</table>
<p style="margin-top: 1.5mm">Everybody has questions 13 and 14; they may also be answered &ldquo;I don't know&rdquo;.</p></div>
</div></div>''', 'box_lies': '''
<div class="box"><h2>The game of Two False Alibis</h2>
<p>Everything is as above, except:</p>
<ol><li>Two suspects lie in their alibis: the murderer and one more. Each repeats the alibi of another suspect of the
same sex and the same parity who was at another place.</li>
<li>Private questions are answered truly by everybody, these two as well.</li>
<li>Nobody says they were where a gun is.</li>
<li>The other 17 tell the truth; the rule about the prints works as usual.</li></ol></div>''',
    'box_frame': '''
<div class="box"><h2>The Accomplice</h2>
<p>Everything is as above, except:</p>
<ol><li>The murderer has an accomplice, and the two keep to one false story: to questions 1, 2, 3 and 8 (about the
murderer) both answer as if another suspect, an innocent one, had done it.</li>
<li>Their alibis are true, and so are their other answers. The other 17 tell the truth.</li>
<li>Name both. The index has no %(accuse)s column: on the last sheet of the case, <b>Accusation</b>, find the row of
the murderer and the column of the accomplice, and read that paragraph. YES only if both are right; NO does not say
which one is wrong, and you are out.</li></ol></div>''',
    'tips_liar': '''
<div class="box tips"><h2>Reading an alibi in this game</h2>
<p><b>Example.</b> No. 4 says: side 1, the Card Party, with No. 15. Read it: 4 was on the East
Side, not at the Card Party; 15 was not where 4 was (4's true companion is another odd woman). Cross out side 1 and the
Card Party for 4; write 15 under &ldquo;not with&rdquo; for 4, and 4 for 15.</p>
<p><b>Count the kinds.</b> A place of four holds one suspect of each kind (sex and parity), so the place of three has
nobody of the victim's kind. When a suspect has one place left, it is closed to the others of their kind.</p>
<p><b>Suppose and check.</b> Say No. 10 can only be at A or F, and of the odd men only No. 5 can still be at F. 10 named 5
as a companion, so they were apart: were 10 at F, F would have no odd man. So 10 was at A.</p></div>''',
    'box_liar': '''
<div class="box"><h2>Everybody Lies</h2>
<p>Everything is as above, except:</p>
<ol><li>Every alibi is false &mdash; everybody's, the murderer's too &mdash; in every field it shows. The suspect was
not on the side named, not in the area named, not at the place named (and the place named is never that of the body).
Each companion named is a suspect of the same sex and parity as a true companion, who was somewhere else. Which
fields an alibi shows is as in the usual game.</li>
<li>Private questions are answered truly by everybody; the rule about the prints works as usual. An alibi says NOT,
an answer says YES. Grids for crossing out are on the last sheet of the case, <b>Notes</b>.</li></ol>
</div>'''}, 'ru': {
    'sub': 'Материалы дела', 'case': 'ДЕЛО', 'index': 'Указатель', 'answers': 'Ответы', 'victim_row': 'жертва',
    'game': ('ОБЫЧНАЯ ИГРА', 'ДВА ЛОЖНЫХ АЛИБИ', 'СООБЩНИК', 'ВСЕ ВРУТ'), 'accusation': 'Обвинение',
    'notes': 'Записи', 'par23': 'ПАР &mdash; столько ходов нужно методичному сыщику: уровни 2 &mdash; %s, 3 &mdash; %s.',
    'notes_howto': 'Зачёркивайте то, что исключает алиби или ответ. Вверху &mdash; где каждый подозреваемый не был '
                   '(место, сторона, район); правдивый ответ может оставить и одну клетку. Названных спутников пишите в '
                   '&laquo;не вместе с&raquo;: они были в другом месте. Внизу &mdash; адрес каждого места. Место тела '
                   'затенено: там никого не было.',
    'notes_groups': ('место', 'сторона', 'район', 'не вместе с'), 'notes_corner': 'подозреваемый', 'notes_addr': 'место &darr; &nbsp; сторона, район &rarr;',
    'to_accuse': 'Чтобы обвинить, откройте последний лист дела, &laquo;%s&raquo;.',
    'pairs_howto': 'Найдите строку того, кого обвиняете в убийстве, и столбец сообщника: число в клетке &mdash; номер '
                   'параграфа ответов. YES &mdash; только если верны оба; NO не говорит, кто из двоих назван неверно.',
    'pairs_corner': '&darr; убийца &nbsp; сообщник &rarr;', 'victim': 'Жертва &mdash; №&nbsp;%d %s. Тело найдено в %s.',
    'par': 'ПАР &mdash; столько ходов нужно методичному сыщику: уровни 1 &mdash; %s, 2 &mdash; %s, 3 &mdash; %s.',
    'levels': {'fair': '''<p>Договоритесь об уровне &mdash; сколько частных вопросов в одном ходе: <b>1</b> Master
Detective &mdash; один, <b>2</b> Sleuth &mdash; два, <b>3</b> Gumshoe &mdash; три.</p>''',
               'liar': '''<p>Договоритесь об уровне &mdash; сколько частных вопросов в одном ходе: <b>2</b> Sleuth &mdash; два,
<b>3</b> Gumshoe &mdash; три. (Уровень 1 для этой игры слишком долгий.)</p>'''},
    'truth': {'fair': 'Подозреваемые говорят правду &mdash; с одним исключением (п.&nbsp;4).',
              'lies': 'Подозреваемые говорят правду, кроме п.&nbsp;4 и двух ложных алиби (ниже).',
              'frame': 'Подозреваемые говорят правду, кроме п.&nbsp;4 и одной ложной версии (ниже).',
              'liar': 'Все алиби ложны (ниже); ответы правдивы, кроме п.&nbsp;4.'},
    'questions': QUESTIONS_RU, 'yes_no': 'YES / NO', 'key_title': 'КАК ЧИТАТЬ ТАБЛО', 'rules_title': 'КРАТКИЕ ПРАВИЛА',
    'key': '''<p>Каждый параграф книги &mdash; семь разрядов табло машины. Точка &mdash; погасший разряд: там ничего не показано.</p>
<h2>%(suspect)s &nbsp;Алиби</h2>
<div>%(example)s</div>
<div class="pos">%(positions)s</div>
<p>Здесь сказано: &laquo;Я был на West Side, в Theatre, с №&nbsp;16&raquo;. Погасший разряд &mdash; подозреваемый об этом не сказал.</p>
<table class="k">
<tr><th>1-й разряд</th><td><b>Сторона</b> &mdash; %(d1)s &laquo;Я был на West Side&raquo;, %(d2)s &laquo;Я был на East Side&raquo;</td></tr>
<tr><th>2-й разряд</th><td><b>Район</b> &mdash; %(d3)s &laquo;Я был в Uptown&raquo;, %(d4)s &laquo;Я был в Midtown&raquo;, %(d5)s &laquo;Я был в Downtown&raquo;</td></tr>
<tr><th>3-й разряд</th><td><b>Место</b>, &laquo;Я был в &hellip;&raquo; &mdash; %(places)s</td></tr>
<tr><th>4&ndash;7-й разряды</th><td><b>Спутники</b>, &laquo;Я был с этими подозреваемыми&raquo; &mdash; один или два номера.
Шестёрка показывается как %(six)s &mdash; тем же знаком, что Theatre.</td></tr>
</table>
<h2>%(pq)s %(accuse)s &nbsp;Ответ</h2>
<table class="k">
<tr><th>%(yes)s</th><td>YES &mdash; да</td></tr>
<tr><th>%(no)s</th><td>NO &mdash; нет</td></tr>
<tr><th>%(unknown)s</th><td>&laquo;не знаю&raquo; (вопросы 13 и 14)</td></tr>
</table>
<p style="margin-top: 3mm">Район или место показаны в том же разряде, что и в алиби: район во 2-м, место в 3-м.</p>
<h2>Как играть по книге</h2>
<p>На листе-указателе дела найдите строку подозреваемого и столбец: %(suspect)s &mdash; алиби, номер под
%(pq)s &mdash; вопрос, или %(accuse)s &mdash; обвинение. В клетке номер параграфа. Прочтите этот параграф на листе
ответов &mdash; и только его. Пустая клетка: такого вопроса нет на карточке подозреваемого.</p>''',
    'rules': '''<div class="cols"><div>
<div><h2>Дело</h2>
<p>В большом городе совершено убийство. Жертва и место, где найдено тело, известны. Остальные 19 человек разъехались
по городу. Допрашивайте их и назовите убийцу. Мужчины &mdash; №&nbsp;1&ndash;10, женщины &mdash; №&nbsp;11&ndash;20.</p></div>
<div><h2>Город</h2>
<p>Шесть мест: %(places)s. Каждое место &mdash; на стороне (1 West Side, 2 East Side) и в районе (3 Uptown, 4 Midtown,
5 Downtown). В городе спрятаны два пистолета, .38 и .45, в двух разных местах. Один из них &mdash; орудие убийства.</p></div>
<div><h2>Перед игрой</h2>
%(levels)s
<p>Возьмите лист-указатель дела. Табло вверху показывает номер жертвы и место тела. Карточку жертвы уберите.
На месте тела нет ни подозреваемых, ни оружия.</p></div>
<div><h2>Ход: один подозреваемый</h2>
<p>%(suspect)s Алиби. Найдите его параграф и прочтите вслух: алиби слышат все.</p>
<p>%(pq)s Не больше, чем разрешает уровень (можно меньше), и только с карточки этого подозреваемого (заполненные клетки строки).
Ответ &mdash; только для ваших глаз.</p>
<p>%(end)s Ход переходит к игроку слева. Того же подозреваемого можно допросить снова в другой ход.</p></div>
<div><h2>%(accuse)s</h2>
<p>Только в начале хода, вместо допроса, и один раз за игру. Прочтите параграф обвиняемого: YES &mdash; дело раскрыто;
NO &mdash; вы выбыли. В одиночной игре неверное обвинение &mdash; дело проиграно.</p>
<p>Считайте свои ходы: пар для каждого уровня &mdash; внизу листа ответов.</p></div>
</div><div>
<div><h2>Что верно всегда</h2>
<ol><li>%(truth)s</li>
<li>В четырёх местах &mdash; по четыре подозреваемых: чётный и нечётный мужчина, чётная и нечётная женщина.</li>
<li>В пятом месте &mdash; трое: двое мужчин и женщина или две женщины и мужчина. Шестое, место тела, пустое.</li>
<li>Отпечатки на орудии убийства: нечётного ли они подозреваемого, надёжно скажет только подозреваемый того же пола,
что убийца, скрывшийся туда, где лежит это оружие. Остальные у оружия могут солгать про отпечатки, а могут и нет.
Там, где оружия нет, на вопросы 13 и 14 отвечают &laquo;не знаю&raquo;.</li>
<li>Убийцы никогда нет на месте тела и там, где лежит любой из пистолетов.</li></ol></div>
<div><h2>Частные вопросы</h2>
<table>%(questions)s</table>
<p style="margin-top: 1.5mm">Вопросы 13 и 14 есть у всех; на них могут ответить и &laquo;не знаю&raquo;.</p></div>
</div></div>''', 'box_lies': '''
<div class="box"><h2>Игра &laquo;Два ложных алиби&raquo;</h2>
<p>Всё как выше, кроме:</p>
<ol><li>Двое лгут в алиби: убийца и ещё один подозреваемый. Каждый повторяет алиби другого подозреваемого того же пола
и той же чётности, который был в другом месте.</li>
<li>На частные вопросы все отвечают правду &mdash; и эти двое тоже.</li>
<li>Никто не говорит, что был там, где лежит оружие.</li>
<li>Остальные 17 говорят правду; правило об отпечатках действует как обычно.</li></ol></div>''',
    'box_frame': '''
<div class="box"><h2>Игра &laquo;Сообщник&raquo;</h2>
<p>Всё как выше, кроме:</p>
<ol><li>У убийцы есть сообщник, и они держатся одной ложной версии: на вопросы 1, 2, 3 и 8 (об убийце) оба отвечают
так, будто это сделал другой подозреваемый, невиновный.</li>
<li>Их алиби правдивы, остальные их ответы тоже. Прочие 17 говорят правду.</li>
<li>Назовите обоих. Колонки %(accuse)s в указателе нет: на последнем листе дела, &laquo;Обвинение&raquo;, найдите
строку убийцы и столбец сообщника и прочтите этот параграф. YES &mdash; только если верны оба; NO не говорит, кто
назван неверно, и вы выбываете.</li></ol></div>''',
    'tips_liar': '''
<div class="box tips"><h2>Как читать алиби в этой игре</h2>
<p><b>Пример.</b> №&nbsp;4 говорит: сторона 1, Card Party, с №&nbsp;15. Читаем: 4 был на East
Side, не в Card Party; 15 был не там, где 4 (настоящий спутник 4 &mdash; другая нечётная женщина). Зачеркните у 4
сторону 1 и Card Party; в &laquo;не вместе с&raquo; запишите 15 у 4 и 4 у 15.</p>
<p><b>Считайте роды.</b> В месте на четверых &mdash; по одному каждого рода (пол и чётность), поэтому в месте на
троих нет рода жертвы. Если у подозреваемого осталось одно место, оно закрыто для остальных его рода.</p>
<p><b>Предположите и проверьте.</b> Пусть №&nbsp;10 может быть только в A или F, а из нечётных мужчин в F может быть
только №&nbsp;5. 10 назвал 5 спутником, значит, они были порознь: будь 10 в F, в F не нашлось бы нечётного мужчины.
Значит, 10 был в A.</p></div>''',
    'box_liar': '''
<div class="box"><h2>Игра &laquo;Все врут&raquo;</h2>
<p>Всё как выше, кроме:</p>
<ol><li>Все алиби ложны &mdash; у всех, и у убийцы тоже, &mdash; в каждом показанном поле. Подозреваемый был не на
названной стороне, не в названном районе, не в названном месте (и названное место &mdash; никогда не место тела).
Каждый названный спутник &mdash; подозреваемый того же пола и чётности, что настоящий спутник, бывший в другом месте.
Какие поля есть в алиби &mdash; как в обычной игре.</li>
<li>На частные вопросы все отвечают правду; правило об отпечатках действует как обычно. Алиби говорит НЕ, ответ
говорит ДА. Сетки для вычёркивания &mdash; на последнем листе дела, &laquo;Записи&raquo;.</li></ol>
</div>'''}}

# --- the display: seven segments a..g of a digit, as lines in a 10 x 18 box ---
LINES = [(2, 1, 8, 1), (9, 2, 9, 8), (9, 10, 9, 16), (2, 17, 8, 17), (1, 10, 1, 16), (1, 2, 1, 8), (2, 9, 8, 9)]


def symbol(mask, panel):
    """A glyph of the display. In a paragraph: black segments, a dot for a dark digit. In a framed display: the dark
    segments stay as a pale ghost, as on the real thing."""
    line = lambda i, colour: '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s"/>' % (LINES[i] + (colour,))
    if panel:
        body = ''.join(line(i, '#000' if mask >> i & 1 else '#dadada') for i in range(7))
    else:
        body = ''.join(line(i, '#000') for i in range(7) if mask >> i & 1) or '<circle cx="5" cy="9" r="1"/>'
    return '<symbol id="%s%d" viewBox="0 0 10 18" stroke-width="1.7" stroke-linecap="round">%s</symbol>' % ('pf'[panel], mask, body)


DEFS = '<svg width="0" height="0" style="position:absolute"><defs>%s</defs></svg>\n' % ''.join(
    symbol(m, p) for m in sorted(set(MASK.values())) for p in (False, True))


def seg(text, panel=False, cls=''):
    """The display showing `text`: bare (a paragraph) or framed."""
    return '<span class="%s">%s</span>' % (('panel ' + cls).strip() if panel else 'disp', ''.join(
        '<svg class="s"><use href="#%s%d"/></svg>' % ('pf'[panel], MASK[c]) for c in text))


def key(label, cls=''):
    return '<span class="%s">%s</span>' % (('key ' + cls).strip(), label)


def top(title, note, right=''):
    return '<div class="top"><h1>%s<small>%s</small></h1>%s</div>\n' % (title, note, right)


# --- the sheets ---
def front(lang, variant='fair'):
    """The two sheets that go with any number of cases: how to read the display, and the rules of this game in brief
    (a book holds one game: its levels and truth line, and its own box; the usual game has none)."""
    t = TEXT[lang]
    keys = {'suspect': key('SUSPECT'), 'pq': key('PRIVATE QUESTION'), 'accuse': key('I ACCUSE'), 'end': key('END TURN'),
            'places': ', '.join('%s&nbsp;%s' % (seg(g), name) for g, name in PLACES.items())}
    questions = ''
    for q in t['questions']:             # '3  What area did the murderer go to?  3 / 4 / 5'
        n, text, answer = (q.split('  ') + [t['yes_no']])[:3]
        questions += '<tr><th>%s</th><td>%s</td><td class="a">%s</td></tr>' % (n, html.escape(text), answer.replace('-', '&ndash;'))
    game = {'levels': t['levels'].get(variant, t['levels']['fair']), 'truth': t['truth'][variant]}
    reading = t['key'] % dict(keys, example=seg('1 b1b  ', True, 'big'), positions=''.join('<span>%d</span>' % n for n in range(1, 8)),
                              six=seg('b'), yes=seg('  4E5  '), no=seg('     N0'), unknown=seg('0000000'),
                              **{'d%d' % n: seg(str(n)) for n in range(1, 6)})
    return ('<section class="rules">%s%s</section>\n<section>%s%s</section>\n' % (      # the rules first, then the display
        top(t['rules_title'], t['sub'], '<span class="game">%s</span>' % t['game'][VARIANTS[variant][0]]),
        (t['rules'] + t.get('box_' + variant, '')) % dict(keys, **game, questions=questions),
        top(t['key_title'], t['sub']), reading + t.get('tips_' + variant, '')))


def codes(number, variant):
    """{(suspect, column): the display} for every alibi, card question and accusation of a case; and its machine."""
    m = Machine(variant=variant, number=number)
    m.power_on(); m.level, m.left = 3, 1; m.start_case('31')
    m.over = True                        # a closed case answers without the limit of questions
    shown = {}
    for s in range(1, 21):
        if s == m.victim: continue
        m.active = False
        shown[s, 'alibi'] = m.enter_suspect(s)
        for q in CARDS[s] + (13, 14):
            m.enter_question(q); shown[s, q] = m.shown
        if not m.pair:
            shown[s, 'accuse'] = '  4E5  ' if s == m.murderer else '     N0'    # not the machine's show: like any answer
    people = [s for s in range(1, 21) if s != m.victim]
    for a, b in ((a, b) for a in people for b in people if m.pair and a != b):   # the accomplice: every pair its paragraph
        shown[a, ('pair', b)] = '  4E5  ' if (a, b) == (m.murderer, m.pair) else '     N0'
    return shown, m


def paragraphs(number, variant):
    """The displays of a case, its machine, and {(suspect, column): the number of the paragraph}."""
    shown, m = codes(number, variant)
    keys = sorted(shown, key=str)
    random.Random(number * 2 + VARIANTS[variant][0]).shuffle(keys)              # a paragraph number says nothing about what is asked
    return shown, m, {k: i + 1 for i, k in enumerate(keys)}


def pars(cases):
    """Par of each case on levels 1, 2, 3, as the game counts it (research/solver/par.py, the methodical detective):
    seconds per case, so in processes on half of the cores. None where the solver is not here or gives up."""
    if not FROZEN and not os.path.exists(PAR):
        return [[None] * 3 for _ in cases]

    def one(job):
        if job[1] == 1 and job[0].get('inverted'): return None     # everybody lies has no level 1: not counted
        try:
            out = subprocess.run(SOLVE + ['case', json.dumps(job[0]), str(job[1])], capture_output=True,
                                 text=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)).stdout.strip()
        except OSError:
            return None
        return int(out) if out.isdigit() else None
    with ThreadPoolExecutor(max(1, (os.cpu_count() or 2) // 2)) as pool:
        got = list(pool.map(one, [(case, level) for case in cases for level in (1, 2, 3)]))
    return [got[i:i + 3] for i in range(0, len(got), 3)]


def book(number, variant, names, lang='en', par=None):
    """The two sheets of a case: the index and the answers (with the par of each level at the bottom, if given)."""
    t = TEXT[lang]
    shown, m, para = paragraphs(number, variant)
    right = '<span class="game">%s</span>%s' % (t['game'][VARIANTS[variant][0]], seg(digits(number, NUMBER), True))
    scene = GLYPH[m.obs['scene']]
    cols = COLS[:-1] if m.pair else COLS              # the accomplice: accused in pairs, on the last sheet
    rows = ''
    for s in range(1, 21):
        cells = ('<td colspan="%d" class="v">%s</td>' % (len(cols), t['victim_row']) if s == m.victim else
                 ''.join('<td>%s</td>' % para.get((s, c), '') for c in cols))
        rows += '<tr><th class="n"><b>%d</b> %s</th>%s</tr>\n' % (s, html.escape(names[s - 1]), cells)
    if m.pair:
        return accomplice_book(t, number, m, shown, para, rows, right, names, par)
    return ''.join((
        '<section class="case">', top('%s %d' % (t['case'], number), t['index'], right),
        '<div class="status">%s<span>%s</span></div>\n' % (
            seg(digits(m.victim) + scene + '    ', True), t['victim'] % (m.victim, html.escape(names[m.victim - 1]), PLACES[scene])),
        '<table><colgroup><col><col>%s<col></colgroup>' % ('<col class="q">' * 14),
        '<thead><tr><th></th><th>%s</th><th colspan="14">%s</th><th>%s</th></tr>\n' % (
            key('SUSPECT'), key('PRIVATE QUESTION'), key('I ACCUSE')),
        '<tr><th></th><th></th>%s<th></th></tr></thead>\n' % ''.join('<th>%s</th>' % key(q, 'd') for q in range(1, 15)),
        rows, '</table>\n<div class="answers">', top('%s %d' % (t['case'], number), t['answers'], right), '<div class="grid">\n',
        ''.join('<div><b>%d</b> %s</div>\n' % (n, seg(shown[k])) for k, n in sorted(para.items(), key=lambda kn: kn[1])),
        '</div>', '<p class="par">%s</p>' % (
            t['par23'] % tuple(p or '&ndash;' for p in par[1:]) if m.variant == 'liar' else
            t['par'] % tuple(p or '&ndash;' for p in par)) if par and any(par) else '',
        '</div>', notes(t, number, m, right, names) if m.variant == 'liar' else '', '</section>\n'))


def notes(t, number, m, right, names):
    """Everybody lies: a last sheet to cross out on - suspect x (place, side, area), and place x (side, area)."""
    cols = list('ABCDEF') + ['1', '2', '3', '4', '5']
    head = lambda c: '<th>%s</th>' % seg(GLYPH.get(c, c))
    cell = lambda c: '<td class="x"></td>' if c == m.obs['scene'] else '<td></td>'
    who = ''.join('<tr><th class="n"><b>%d</b> %s</th>%s<td style="width: 22%%"></td></tr>\n' % (
        s, html.escape(names[s - 1]), ''.join(map(cell, cols))) for s in range(1, 21) if s != m.victim)
    groups = '<tr><th></th>%s</tr>' % ''.join(      # named groups: a companion's number is not a side or an area
        '<th colspan="%d">%s</th>' % (n, g) for n, g in zip((6, 2, 3, 1), t['notes_groups']))
    addr = ''.join('<tr><th class="n">%s %s</th>%s</tr>\n' % (seg(GLYPH[l]), PLACES[GLYPH[l]], '<td></td>' * 5) for l in 'ABCDEF')
    table = '<table class="pairs notes"%s><thead><tr><th class="corner">%s</th>%s</tr></thead>\n'
    return ''.join((
        '<div class="answers">', top('%s %d' % (t['case'], number), t['notes'], right),
        '<p class="howto">%s</p>' % t['notes_howto'],
        (table % ('', t['notes_corner'], ''.join(map(head, cols)) + '<th></th>')).replace(
            '<thead>', '<colgroup><col>%s<col></colgroup><thead>%s' % ('<col class="c">' * 11, groups)),
        who, '</table>\n',
        (table % (' style="width: 60%; margin-top: 5mm"', t['notes_addr'], ''.join(map(head, cols[6:])))).replace(
            '<thead>', '<colgroup><col>%s</colgroup><thead>' % ('<col class="c">' * 5)), addr,
        '</table></div>'))


def accomplice_book(t, number, m, shown, para, rows, right, names, par):
    """The sheets of an accomplice case: the index (no I ACCUSE), the answers (the accusations of pairs mixed in,
    smaller), and last, so that it is not leafed through on the way, the grid of pairs."""
    people = [s for s in range(1, 21) if s != m.victim]
    scene = GLYPH[m.obs['scene']]
    grid = ''.join('<tr><th class="n"><b>%d</b> %s</th>%s</tr>\n' % (a, html.escape(names[a - 1]), ''.join(
        '<td class="x"></td>' if a == b else '<td>%d</td>' % para[a, ('pair', b)] for b in people)) for a in people)
    return ''.join((
        '<section class="case">', top('%s %d' % (t['case'], number), t['index'], right),
        '<div class="status">%s<span>%s</span></div>\n' % (
            seg(digits(m.victim) + scene + '    ', True), t['victim'] % (m.victim, html.escape(names[m.victim - 1]), PLACES[scene])),
        '<table><colgroup><col><col>%s</colgroup>' % ('<col class="q">' * 14),
        '<thead><tr><th></th><th>%s</th><th colspan="14">%s</th></tr>\n' % (key('SUSPECT'), key('PRIVATE QUESTION')),
        '<tr><th></th><th></th>%s</tr></thead>\n' % ''.join('<th>%s</th>' % key(q, 'd') for q in range(1, 15)),
        rows, '</table>\n<p class="howto">%s</p>' % (t['to_accuse'] % t['accusation']),
        '<div class="answers">', top('%s %d' % (t['case'], number), t['answers'], right), '<div class="grid small">\n',
        ''.join('<div><b>%d</b> %s</div>\n' % (n, seg(shown[k])) for k, n in sorted(para.items(), key=lambda kn: kn[1])),
        '</div>', '<p class="par">%s</p>' % (t['par'] % tuple(p or '&ndash;' for p in par)) if par and any(par) else '',
        '</div><div class="answers">', top('%s %d' % (t['case'], number), t['accusation'], right),
        '<p class="howto">%s</p>' % t['pairs_howto'],
        '<table class="pairs"><thead><tr><th class="corner">%s<br>%s</th>%s</tr></thead>\n' % (
            key('I ACCUSE'), t['pairs_corner'], ''.join('<th>%d</th>' % b for b in people)),
        grid, '</table></div></section>\n'))


def write(count, variant, names, lang='en', folder=None, rng=None, numbers=None):
    """Writes a file of `count` random cases (or of the given numbers) and returns its path. The par takes seconds
    per case, and so does checking a deal by the solver in the games that need it, as in the game."""
    lang = lang if lang in TEXT else 'en'
    numbers = numbers or (rng or random.SystemRandom()).sample(range(1, 10 ** NUMBER), min(count, MOST))
    par = pars([codes(n, variant)[1].case for n in numbers])
    folder = folder or BOOKS
    os.makedirs(folder, exist_ok=True)
    name = time.strftime('cases_%Y%m%d_%H%M%S') + ('_' + variant) * (variant != 'fair') + ('_' + lang) * (lang != 'en') + '.html'
    with open(os.path.join(folder, name), 'w', encoding='utf-8') as f:
        f.write(STYLE + DEFS + front(lang, variant) + ''.join(book(n, variant, names, lang, p) for n, p in zip(numbers, par)))
    return os.path.join(folder, name)


if __name__ == '__main__':
    from elecdet_game import NAMES, load_settings
    given = [a for a in sys.argv[2:] if a in TEXT]
    print(write(int(sys.argv[1]), next((a for a in sys.argv[2:] if a in VARIANTS), 'fair'), NAMES, given[0] if given else load_settings().get('help_lang', 'en')))
