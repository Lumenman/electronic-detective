"""Electronic Detective (Ideal, 1979) in a window.

    python elecdet_game.py [path to ROM folder or elecdet.zip]      (the ROM is needed only for 1 + ON)

Keys: 0-9, S = Suspect, Q = Private Question, A = I Accuse, Enter, T = End Turn, O = On, X = Off,
M = sound off/on, Space = peek at a private answer, F1 = rules.
ON starts our own machine (machine.py: same rules and behaviour, cases dealt at random, no ROM needed).
ON pressed while 1 is held runs the original ROM in the emulator, with the regularities of its deals;
2 + ON is the game of two false alibis. 9 + ON asks for the number of a case and switches off again: the next game
(ON or 2 + ON) plays that case - the same number is the same case on any device.
Suspect cards are not shown: use the paper cards or the PDF.
"""
import array, json, os, random, re, subprocess, sys, threading, time
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')   # no pygame banner in the terminal
import pygame
from board import ElecDet, IPS, SEG, load_romset
import paper
from machine import Machine, NUMBER, number_rng
from rules import CARDS, deal_lies, from_ram, observe
from help_text import HELP

VERSION = '0.3'                          # of the builds (buildozer.spec reads it from here)
STOCK = 3                                # cases of the game of two false alibis kept dealt ahead
TALLY = 10                               # solved cases kept for the running score against par
PAR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'research', 'solver', 'par.py')

HERE = paper.BOOKS                      # beside the program (the built one: beside the exe, not in its unpacked copy)
ANDROID = 'ANDROID_ARGUMENT' in os.environ      # packed by android/build.sh: touch screen, no ROM (see there)
SETTINGS = os.path.join(os.environ.get('ANDROID_PRIVATE', HERE), 'settings.json')   # the app folder is replaced on update
FALLBACK = os.path.join(os.environ.get('APPDATA') or os.path.join(os.path.expanduser('~'), '.config'),
                        'ElectronicDetective', 'settings.json')    # when the folder of the program is read-only
if not ANDROID and not os.path.exists(SETTINGS) and os.path.exists(FALLBACK):
    SETTINGS = FALLBACK
RATE = 24000                        # 400 samples per 1/60 s; SDL resamples for the device
CHUNK = 1 / 60                      # seconds of emulation per step
AHEAD = 0.1                         # seconds of audio kept buffered (also how far the display runs ahead)
HOLD, GAP_CHUNKS = 6, 2             # the ROM drops presses under ~40 ms and overlapping keys: hold 0.1 s, 33 ms apart

NAMES = ['Lenny Little', 'Al Farook', 'Pepe Perez', 'Tony Racheti', "Mickey O'Malley", 'Max Fineflugle',
         'Ripp Rapp', 'Buster Bailey', 'Rocky Roll', 'Ling Tong', 'Ivy Little', 'Lucy Tumble', 'Piper Perez',
         'Dina Racheti', 'Eileen Stellar', 'Joan Fineflugle', 'Rose Pettle', 'Doris Dill', 'Candy Roll', 'Sing Wong']
PLACES = {'A': 'the Art Show', 'b': 'the Theatre', 'C': 'the Card Party', 'd': 'the Docks', 'E': 'the Embassy',
          'F': 'the Factory'}
SIDES = {'1': 'West Side', '2': 'East Side'}
AREAS = {'3': 'Uptown', '4': 'Midtown', '5': 'Downtown'}
QUESTIONS = {1: 'Did the murderer go to the EAST SIDE?', 2: 'Did a MALE do it?', 3: 'What AREA did the murderer go to?',
             4: 'Was the MURDER WEAPON a .38?', 5: 'Where was the .38 hidden?', 6: 'Where was the .45 hidden?',
             7: 'Which PLACE contained only 3 suspects?', 8: 'Did the murderer go to PLACE A, B or C?',
             9: 'Were you on the EAST SIDE?', 10: 'Which AREA were you in?', 11: 'Were you at PLACE A, B or C?',
             12: 'Were you where a WEAPON was hidden?', 13: "Are an odd-numbered suspect's PRINTS on the .38?",
             14: "Are an odd-numbered suspect's PRINTS on the .45?"}

# on-screen keypad: (label, board key, pc key, column, row, width)
PAD = [('1', '1', pygame.K_1, 0, 0, 1), ('2', '2', pygame.K_2, 1, 0, 1), ('3', '3', pygame.K_3, 2, 0, 1),
       ('4', '4', pygame.K_4, 0, 1, 1), ('5', '5', pygame.K_5, 1, 1, 1), ('6', '6', pygame.K_6, 2, 1, 1),
       ('7', '7', pygame.K_7, 0, 2, 1), ('8', '8', pygame.K_8, 1, 2, 1), ('9', '9', pygame.K_9, 2, 2, 1),
       ('0', '0', pygame.K_0, 2, 3, 1),
       ('ON', 'ON', pygame.K_o, 0, 4, 1), ('OFF', 'OFF', pygame.K_x, 1, 4, 1),
       ('SUSPECT', 'SUSPECT', pygame.K_s, 3, 0, 2), ('PRIVATE QUESTION', 'PQ', pygame.K_q, 3, 1, 2),
       ('I ACCUSE', 'ACCUSE', pygame.K_a, 3, 2, 2), ('ENTER', 'ENTER', pygame.K_RETURN, 3, 3, 2),
       ('END TURN', 'ENDTURN', pygame.K_t, 3, 4, 2)]   # layout of the original: 5 columns x 5 rows
# the phone's keypad: 3 columns x 6 rows; the rarely used keys on top, the digits in the middle
TALL = {'ON': (0, 0, 1), 'OFF': (1, 0, 1), 'ACCUSE': (2, 0, 1),
        '1': (0, 1, 1), '2': (1, 1, 1), '3': (2, 1, 1), '4': (0, 2, 1), '5': (1, 2, 1), '6': (2, 2, 1),
        '7': (0, 3, 1), '8': (1, 3, 1), '9': (2, 3, 1), 'SUSPECT': (0, 4, 1), 'PQ': (1, 4, 1), '0': (2, 4, 1),
        'ENTER': (0, 5, 2), 'ENDTURN': (2, 5, 1)}
NUMPAD = {getattr(pygame, 'K_KP%d' % i): str(i) for i in range(10)}
NUMPAD[pygame.K_KP_ENTER] = 'ENTER'
OFF_HINT = ('ON: a new case. Hold a key, press ON: 1 the original, 2 two false alibis, '              # two lines:
            '8 board game, 9 by number.')                                                       # longer is cut
if 'ANDROID_ARGUMENT' in os.environ:      # no ROM on the phone
    OFF_HINT = 'ON: a new case. Hold a key and press ON: 2 two false alibis, 9 a case by its number.'


def num(s):
    s = s.replace('b', '6').strip()
    return int(s) if s.isdigit() else None


def who(n):
    return '#%d %s' % (n, NAMES[n - 1]) if n and 1 <= n <= 20 else '#%s' % n


class Decoder:
    """Turns the display into an English status line, using the keys the player typed. Reads only the display."""

    def __init__(self):
        self.entry = []          # keys since the last ENTER
        self.context = ('off',)
        self.victim = None
        self.players, self.level = 1, 0
        self.seq = 0             # ENTER counter: one answer per ENTER

    def key(self, k):
        before = self.context[0] in ('number', 'setup')      # the machine shows ON and takes digits and ENTER only
        if k == 'ON':
            self.entry, self.context, self.victim = [], ('setup',), None
        elif before and k in ('SUSPECT', 'PQ', 'ACCUSE', 'ENDTURN'):
            self.entry = []                                  # it drops what was typed
        elif k == 'ENTER':
            e, self.entry = self.entry, []
            digits = ''.join(x for x in e if x.isdigit())
            n = int(digits) if digits else None
            self.seq += 1
            if self.context[0] == 'number':
                if n and n <= (self.context + (10 ** NUMBER,))[1]:      # ('number', most) after 8 + ON
                    self.context = ('off',)                  # remembered for the next game: the machine goes dark
            elif self.context[0] == 'setup':
                if len(digits) == 2 and digits[0] in '123' and digits[1] in '1234':   # anything else: ON again
                    self.context = ('crime',)
                    self.level, self.players = int(digits[0]), int(digits[1])
            elif e[:1] == ['SUSPECT']:
                self.context = ('alibi', n)
            elif e[:1] == ['PQ']:
                self.context = ('question', n, self.suspect())
            elif e[:1] == ['ACCUSE']:
                self.context = ('accuse', n)
        elif k == 'ENDTURN':
            self.entry, self.context = [], ('turn',)
        elif k != 'OFF':
            if k in ('SUSPECT', 'PQ', 'ACCUSE'):
                self.entry = []
            at = [i for i, x in enumerate(self.entry) if x.isdigit()]
            if k.isdigit() and len(at) >= (NUMBER if self.context[0] == 'number' else 2):
                del self.entry[at[0]]            # the display keeps the last two digits (six of a case number)
            self.entry.append(k)

    def is_private(self, d):
        """A private-question answer that other players must not see (2+ players only)."""
        t = d.replace(' ', '')
        return (self.players > 1 and self.context[0] == 'question' and not self.entry
                and bool(t) and t not in ('EE', 'ENd'))

    def suspect(self):
        c = self.context
        return c[1] if c[0] == 'alibi' else c[2] if c[0] == 'question' else None

    def typing(self):
        names = {'SUSPECT': 'Suspect', 'PQ': 'Private question', 'ACCUSE': 'I accuse'}
        return ' '.join(names.get(x, x) for x in self.entry)

    def status(self, d):
        c, t = self.context, d.replace(' ', '')
        if c[0] == 'off':
            return OFF_HINT
        if t == 'EE':
            return 'EE: wrong key sequence or a question not on this card. Start the entry again.'
        if t == 'ENd':
            return 'END: no more questions this turn. Press END TURN.'
        if c[0] == 'number' and c[1:]:
            return 'Board game: enter how many cases to write (1-%d), then ENTER.' % c[1]
        if c[0] == 'number':
            return'Enter the number of the case (1-%d), then ENTER.' % (10 ** NUMBER - 1)
        if c[0] == 'setup':
            return 'Enter level (1 Master Detective, 2 Sleuth, 3 Gumshoe), number of players (1-4), then ENTER.'
        if c[0] == 'crime':
            v = num(d[0:2])
            if v and d[2] in PLACES:
                self.victim = v
                return 'The victim is %s. The body was found at %s.' % (who(v), PLACES[d[2]])
            return 'BANG! BANG! A murder has been committed...'
        if c[0] == 'alibi':
            s = c[1]
            if t == '0000000':
                return '%s: no answer (the victim cannot be questioned).' % who(s)
            parts = []
            if d[0] in SIDES: parts.append('on the ' + SIDES[d[0]])
            if d[1] in AREAS: parts.append(AREAS[d[1]])
            if d[2] in PLACES: parts.append('at ' + PLACES[d[2]])
            mates = [num(d[3:5]), num(d[5:7])]
            mates = [who(m) for m in mates if m]
            if mates: parts.append('with ' + ' and '.join(mates))
            card = ' Questions: %s, 13, 14.' % ', '.join(map(str, CARDS[s])) if s in CARDS else ''   # no card at hand
            return '%s: "I was %s."%s' % (who(s), ', '.join(parts), card) if parts else ''
        if c[0] == 'question':
            q, s = c[1], c[2]
            ans = {'4E5': 'YES', 'N0': 'NO', '0000000': "I don't know"}.get(t)
            if ans is None and t in PLACES: ans = PLACES[t][4:].title() if t else t
            if ans is None and t in AREAS: ans = AREAS[t]
            if ans is None: return ''
            return '%sQ%s %s  ->  %s' % (who(s) + ', ' if s else '', q, QUESTIONS.get(q, ''), ans)
        if c[0] == 'accuse':
            m = re.match(r'^([0-9b]+)(4E5|d1d)$', t)
            if m:
                n = num(m.group(1))
                if m.group(2) == '4E5':
                    return 'YES! %s is the murderer. Case solved!' % who(n)
                return 'WRONG. The murderer was %s. You are out of the game.' % who(n)
            if t == 'N0':
                return 'NO! Wrong accusation - out of the game. Next player: press END TURN first.'
            return 'Accusing %s...' % who(c[1])
        return ''


class Score:
    """Turns and private questions per player, eliminations, winner. Pure logic, no drawing."""

    def __init__(self, level, players):
        self.level, self.n = level, max(1, players)
        self.turns, self.questions, self.out = [0] * self.n, [0] * self.n, [False] * self.n
        self.cur, self.winner, self.acted = 0, None, False

    @property
    def over(self):
        return self.winner is not None or all(self.out)

    def name(self, p):
        return 'Player %d' % (p + 1)

    def stats(self, p):
        return '%d turn%s, %d question%s' % (self.turns[p], '' if self.turns[p] == 1 else 's',
                                             self.questions[p], '' if self.questions[p] == 1 else 's')

    def _next(self):
        if not self.over:
            self.cur = (self.cur + 1) % self.n
            while self.out[self.cur]:
                self.cur = (self.cur + 1) % self.n

    def suspect(self):
        self.acted = True

    def question(self):
        if not self.over:
            self.questions[self.cur] += 1

    def end_turn(self):
        """Returns the line for the player who just finished, or None if nothing to count."""
        if self.over or not self.acted:
            return None
        p, self.acted = self.cur, False
        self.turns[p] += 1
        self._next()
        q = self.questions[p]
        line = 'after turn %d: %d question%s so far' % (self.turns[p], q, '' if q == 1 else 's')
        return ('%s - %s' % (self.name(p), line)) if self.n > 1 else line[0].upper() + line[1:]

    def accused(self, correct):
        p = self.cur
        if self.acted:                       # accusing right after questioning: that turn counts too
            self.turns[p] += 1; self.acted = False
        if correct:
            self.winner = p
        else:
            self.out[p] = True
        self._next()
        return p

    def summary(self):
        if self.n == 1:
            return ('Solved after %s.' if self.winner == 0 else 'Out after %s.') % self.stats(0)
        parts = [('Case solved by %s: %s.' % (self.name(self.winner), self.stats(self.winner)))
                 if self.winner is not None else 'All detectives are out.']
        parts += ['%s: %s.' % (self.name(p), 'out' if self.out[p] else self.stats(p))
                  for p in range(self.n) if p != self.winner]
        return ' '.join(parts)

    def record(self, records):
        """Solo win: compare with and update records {level: [turns, questions]}; returns a message."""
        if self.n != 1 or self.winner != 0:
            return ''
        key, mine = str(self.level), [self.turns[0], self.questions[0]]
        best = records.get(key)
        records[key] = min(best, mine) if best else mine
        if not best:
            return 'First record for level %d.' % self.level
        if mine < best:
            return 'New record for level %d! (was %d turns, %d questions)' % (self.level, *best)
        return 'Best on level %d: %d turns, %d questions.' % (self.level, *best)


def font(size, bold=False):
    """Arial; where the apk brought DejaVu Sans beside this file (the phone has no Arial), that one."""
    path = os.path.join(getattr(sys, '_MEIPASS', HERE), 'DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')
    return pygame.font.Font(path, round(size * 0.9)) if os.path.exists(path) else pygame.font.SysFont('arial', size, bold=bold)


def draw_digit(surf, x, y, w, h, levels, on, off):
    """Seven-segment digit; levels[0..6] = brightness 0..1 of segments a..g."""
    t = max(3, w // 6)
    hs = [(x + t, y, w - 2 * t, t), (x + w - t, y + t, t, h // 2 - t), (x + w - t, y + h // 2, t, h // 2 - t),
          (x + t, y + h - t, w - 2 * t, t), (x, y + h // 2, t, h // 2 - t), (x, y + t, t, h // 2 - t),
          (x + t, y + h // 2 - t // 2, w - 2 * t, t)]
    for b, r in enumerate(hs):
        c = [round(f + (n - f) * levels[b]) for n, f in zip(on, off)]
        pygame.draw.rect(surf, c, r, border_radius=t // 2)


def ask_rom(error=None):
    """File dialog for the ROM (folder or zip). Returns a path or None."""
    import tkinter
    from tkinter import filedialog, messagebox
    root = tkinter.Tk(); root.withdraw()
    msg = ('Electronic Detective needs the original ROM (MAME romset "elecdet": mp6100a and four .pla files).\n\n'
           'Choose the elecdet.zip file, or press Cancel to choose a folder.')
    if error:
        msg = error + '\n\n' + msg
    messagebox.showinfo('ROM needed', msg, parent=root)
    p = filedialog.askopenfilename(parent=root, title='elecdet.zip', filetypes=[('Zip', '*.zip'), ('All', '*.*')])
    if not p:
        p = filedialog.askdirectory(parent=root, title='Folder with mp6100a and the .pla files')
    root.destroy()
    return p or None


def load_settings():
    try:
        return json.load(open(SETTINGS))
    except (OSError, ValueError):
        return {}


LOCK = threading.RLock()                 # the settings are written by the window and by the thread that deals ahead


SAVE_ERROR = ''                          # set when neither place can be written: shown while off


def writable(folder):
    """By trying: os.access says yes to Program Files on Windows."""
    probe = os.path.join(folder, '.write_test')
    try:
        os.makedirs(folder, exist_ok=True); open(probe, 'w').close(); os.remove(probe)
        return True
    except OSError:
        return False


def save_settings(**changes):
    global SAVE_ERROR, SETTINGS
    with LOCK:
        data = load_settings(); data.update(changes)
        for _ in range(2):
            try:
                os.makedirs(os.path.dirname(SETTINGS), exist_ok=True)
                with open(SETTINGS + '.tmp', 'w') as f:
                    json.dump(data, f, indent=1)
                os.replace(SETTINGS + '.tmp', SETTINGS)    # a crash while writing must not leave a broken file
                SAVE_ERROR = ''
                return
            except OSError as e:
                if ANDROID or SETTINGS == FALLBACK:
                    SAVE_ERROR = 'Records and settings are not saved (%s).' % (e.strerror or e)
                    return
                SETTINGS = FALLBACK                      # the folder of the program is read-only: the user's folder


def find_rom(arg):
    path, error = arg or load_settings().get('rom'), None
    while True:
        if path:
            try:
                files = load_romset(path)
                save_settings(rom=path)
                return files
            except (OSError, ValueError) as e:
                error = str(e)
        path = ask_rom(error)
        if not path:
            sys.exit('No ROM selected.')


class Stock(threading.Thread):
    """Cases of the game of two false alibis, dealt and checked ahead while nothing sounds: 2 + ON then starts at once.
    Kept in the settings as [number of the case, deals to skip]: the number seeds the deals, and the first of them
    that can be solved is the case (a number tells nothing about the case)."""

    def __init__(self, game):
        super().__init__(daemon=True)
        self.game = game
        self.start()

    def run(self):
        sys.path.append(os.path.dirname(PAR))        # on the phone the solver lies beside this file
        try:
            from solver import lie_suspects
        except ImportError:
            return                       # no solver here: the machine deals unchecked
        while True:
            if len(load_settings().get('lies_dealt', [])) >= STOCK:
                time.sleep(1); continue
            number, skip = random.SystemRandom().randrange(1, 10 ** NUMBER), 0
            rng = number_rng(number, True)
            while True:                  # as Machine.deal_solvable does for a number typed by the player
                t = time.thread_time()
                good = len(lie_suspects(observe(deal_lies(rng))[0], pause=self.game.quiet)) == 1
                self.game.timing['deal'] = time.thread_time() - t
                if good: break
                skip += 1
            with LOCK:
                save_settings(lies_dealt=load_settings().get('lies_dealt', []) + [[number, skip]])


class ParThread(threading.Thread):
    """The phone has no second process: the solver counts in a thread, behind the few calls used of a process."""

    def __init__(self, case, level):
        super().__init__(daemon=True)
        self.case, self.level, self.out, self.stdout = case, level, '', self
        self.start()

    def run(self):
        sys.path.append(os.path.dirname(PAR))        # on the phone the solver lies beside this file
        import par
        t = time.thread_time()
        self.out = str(par.case_par(self.case, self.level))
        self.seconds = time.thread_time() - t

    def poll(self):
        return None if self.is_alive() else 0

    def read(self):
        return self.out

    def kill(self):
        pass                             # shortcut: counts to its end (seconds); the answer is then dropped


class Game:
    HINT = 'S Suspect   Q Question   A Accuse   T End Turn   O/X On/Off   Space Peek   M Sound'
    M, U, KEY_H, GAP = 24, 91, 56, 12    # outer margin, key width/height, gap
    CW = 5 * U + 4 * GAP                 # keypad width = width of every area
    W = CW + 2 * M
    K, Z, LINES = 1, 1, 2                # pixels per unit of this layout, text size, lines of status
    DIGIT = 44, 68                       # a digit of the display
    LABEL, CMD = 13, (60, 140, 210)      # size of a word on a key; colour of the command keys
    DISP = pygame.Rect(M, M, CW, 100)
    STATUS = pygame.Rect(M, DISP.bottom + 14, CW, 52)
    PAD_TOP = STATUS.bottom + 16
    H = PAD_TOP + 5 * KEY_H + 4 * GAP + 44

    def px(self, n):
        return round(n * self.K)

    def fit(self, ww, wh):
        """The phone: the whole upright screen, drawn at its own resolution (sharp text) - larger text, 3 x 6 keys."""
        # shortcut: upright screens only (the apk is locked to portrait); a wide one needs side margins
        self.K, self.Z, self.LINES, self.DIGIT = ww / self.W, 1.8, 4, (48, 82)
        self.LABEL, self.CMD = 15, (40, 105, 175)                               # the commands stand out from the digits
        self.M, self.GAP, self.W, self.H = self.px(24), self.px(12), ww, wh
        self.CW = ww - 2 * self.M
        self.U = (self.CW - 2 * self.GAP) // 3
        self.DISP = pygame.Rect(self.M, self.M, self.CW, 2 * self.px(7) + self.LINES * self.px(19 * self.Z))
        self.STATUS = self.DISP.move(0, self.DISP.h + self.px(14))             # the same size as the display
        self.PAD_TOP = self.STATUS.bottom + self.px(16)
        self.KEY_H = (wh - self.PAD_TOP - self.M - 5 * self.GAP) // 6

    par = par_msg = None                 # the solver's process for this case; its line in the final summary
    wiped = False                        # the records were cleared: say so until the machine is switched on
    wipe_ask = False                     # 0 + ON was pressed: ENTER clears the records, any other key keeps them
    lies = False                         # the game of two false alibis (2 + ON)
    numbered = False                     # the case was chosen by its number: no records, no running score
    pending = None                       # the number typed after 9 + ON, kept for the next game
    booking = False                      # the machine is on after 8 + ON: it takes how many cases to write on paper
    count = None                         # that many, kept until ON or 2 + ON picks the game
    printed = None                       # what became of them: shown while the machine is off
    help = None                          # the page of the '?' screen that is open
    timing = {}                          # seconds of the last deal check and par count in this process (shown in the help)

    def quiet(self):
        """Holds the thread that deals ahead while the machine sounds (its counting would make the sound stutter)."""
        while isinstance(self.board, Machine) and self.board.powered and self.board.cycles < self.board.busy_until:
            time.sleep(0.02)

    def take(self):
        """A case dealt ahead for the game of two false alibis, with its number, or None."""
        with LOCK:
            stock = load_settings().get('lies_dealt', [])
            if not stock:
                return None
            save_settings(lies_dealt=stock[1:])
        (number, skip), rng = stock[0], number_rng(stock[0][0], True)
        for _ in range(skip): deal_lies(rng)
        return number, deal_lies(rng)

    def kind(self):
        """The game being played, as the ending of its records in the settings."""
        return '' if self.original else '_lies' if self.lies else '_fair'

    def __init__(self, files=None, rom=None):
        self.files, self.rom = files, rom   # the ROM (loaded files, or where to look) is asked for on 1 + ON only
        self.original = False
        self.board = None
        self._level = self._last = 0
        self.decoder = Decoder()
        self.status = OFF_HINT
        self.held = {}                   # board key -> number of sources holding it (mouse/keyboard)
        self.keyq, self.cur_key, self.key_age, self.key_rest = [], None, 0, 0   # presses waiting for the board
        pygame.init()                    # also brings up SDL audio, needed by AudioDevice
        sys.setswitchinterval(0.001)     # threads count the deal and the par: the sound must not wait long for its turn
        self.buf, self.lock, self.underruns = bytearray(), threading.Lock(), 0
        try:
            from pygame._sdl2 import audio, sdl2
            pygame.mixer.quit()          # Android has one playback device, and pygame.init() gave it to the mixer
            sdl2.init_subsystem(sdl2.INIT_AUDIO)
            self.audio = audio.AudioDevice(None, False, RATE, audio.AUDIO_S16, 1, 512, 0, self.fill_audio)
            self.audio.pause(0)
        except Exception as e:           # no audio device: run on the wall clock
            print('Sound disabled:', e)
            self.audio = None
            self.status = 'Sound disabled: %s. %s' % (e, OFF_HINT)
        self.window = self.screen = pygame.display.set_mode((0, 0) if ANDROID else (self.W, self.H))
        ww, wh = self.window.get_size()
        if ANDROID:
            self.fit(ww, wh)
        self.fingers = {}                # finger id -> the key it holds (None: it lifts the cover)
        pygame.display.set_caption('Electronic Detective ' + VERSION)
        icon = os.path.join(getattr(sys, '_MEIPASS', HERE), 'icon.png')    # the phone takes its icon from the apk
        if not ANDROID and os.path.exists(icon):
            pygame.display.set_icon(pygame.image.load(icon))
        self.font = font(int(15 * self.Z * self.K))
        self.fine = font(int(15 * self.Z * self.K * 4 / 5))   # five lines where four do not do
        self.small = font(int(self.LABEL * self.Z * self.K), bold=True)
        self.big = font(int(26 * self.Z * self.K), bold=True)
        self.hint_img = self.small.render(self.HINT, True, (110, 110, 100))
        room = self.px(self.W - self.M)                      # half the margin on each side
        if self.hint_img.get_width() > room:                 # DejaVu (Linux build) is wider than Arial
            self.hint_img = font(int(self.LABEL * self.Z * self.K * room / self.hint_img.get_width()),
                                 bold=True).render(self.HINT, True, (110, 110, 100))
        self.buttons = []
        for label, key, _, col, row, w in PAD:
            if ANDROID:
                col, row, w = TALL.get(key, (col, row, w))
            x = self.M + col * (self.U + self.GAP)
            r = pygame.Rect(x, self.PAD_TOP + row * (self.KEY_H + self.GAP), w * self.U + (w - 1) * self.GAP, self.KEY_H)
            self.buttons.append((r, label, key))
        self.clock_left = 0.0
        self.peek_key = self.peek_mouse = False
        self.score = self.note = self.final = None
        self.counted = self.final_seq = -1
        self.rec = ''
        self.d = ''
        self.static = self.screen.copy()
        self.paint_static(self.static)
        self.timing, self.lang, self.size = {}, load_settings().get('help_lang', 'en'), load_settings().get('help_size', 0)
        self.muted = load_settings().get('muted', False)
        Stock(self)

    # --- emulation & sound ---
    def feed_keys(self):
        """One step of the key queue: every press reaches the board for at least HOLD steps, one key at a time."""
        if self.cur_key:
            self.key_age += 1
            if self.key_age >= HOLD and not self.held.get(self.cur_key):
                self.board.set_key(self.cur_key, False)
                self.cur_key, self.key_rest = None, GAP_CHUNKS
        elif self.key_rest:
            self.key_rest -= 1
        elif self.keyq:
            self.cur_key, self.key_age = self.keyq.pop(0), 0
            if not self.deaf():                  # decided now, as the board decides: typed ahead keys can land in a sound
                self.heard(self.cur_key)
            self.board.set_key(self.cur_key, True)

    def emulate(self, seconds):
        n = int(seconds * IPS)
        if self.board is None:
            return [0] * round(seconds * RATE)
        b = self.board
        self.feed_keys()
        c0 = b.cpu.cycles
        b.run(n)
        ev, b.sound_events = b.sound_events, []
        out, lv, j = [], self._level, 0
        m = round(seconds * RATE)
        for i in range(m):
            cyc = c0 + i * n / m
            while j < len(ev) and ev[j][0] <= cyc:
                lv = ev[j][1]; j += 1
            out.append(lv)
        self._level = ev[-1][1] if ev else lv
        return out

    def fill_audio(self, dev, mem):
        """SDL audio thread: hand over buffered samples; on underrun hold the last level (no click)."""
        n = len(mem)
        with self.lock:
            k = min(n, len(self.buf))
            mem[:k] = self.buf[:k]
            del self.buf[:k]
        if k < n:
            self.underruns += 1
            mem[k:] = array.array('h', [self._last] * ((n - k) // 2)).tobytes()

    def pump_audio(self):
        """Emulate until AHEAD seconds of sound are buffered: the sound card sets the pace."""
        while len(self.buf) < AHEAD * RATE * 2:
            vol = 0 if self.muted else 5000      # muted: still emulate, the sound card keeps the pace
            samples = array.array('h', (v * vol for v in self.emulate(CHUNK)))
            self._last = samples[-1]
            with self.lock:
                self.buf += samples.tobytes()

    # --- input ---
    def press(self, key, down):
        if self.wipe_ask and down:               # after 0 + ON: ENTER clears, any other key keeps the records
            self.wipe_ask = False
            if key == 'ENTER':
                save_settings(records={}, records_fair={}, records_lies={}, par={}, par_fair={}, par_lies={})
                self.wiped = True
                return
        if key in ('ON', 'OFF'):
            book = bool(self.held.get('8')) and not ANDROID    # 8 + ON: only to type how many cases to write on paper
            ask = bool(self.held.get('9')) or book   # 9 + ON: only to type the number of the next case
            original = bool(self.held.get('1')) and not ask    # a held digit picks the game: 1 + ON, 2 + ON
            if key == 'ON' and down and self.held.get('0') and not (self.board and self.board.powered):
                self.wipe_ask, self.wiped = True, False                    # 0 + ON: asks first
                return
            lies = bool(self.held.get('2')) and not original and not ask          # 2 + ON: two false alibis
            if key == 'ON' and down and original and ANDROID and self.files is None:
                return                       # no ROM on the phone
            if key == 'ON' and self.board is not None and self.board.powered:
                return                       # already on: the real switch does nothing either
            if down:
                if key == 'ON' and original and self.files is None:
                    try:
                        self.files = find_rom(self.rom)
                    except SystemExit:           # no ROM chosen: stay off
                        return
                self.decoder.key(key)
                self.score = self.note = self.final = None
                self.stop_par()
                if key == 'OFF': self.pending = self.count = None                 # OFF forgets the number that was set
                self.printed = None
                if key == 'ON' and self.count and not ask and not original:       # the game is picked: write, stay off
                    self.write_cases(lies)
                elif key == 'ON' and (self.board is None or not self.board.powered):
                    number = None if ask or original else self.pending            # the ROM's cases have no numbers
                    self.board = ElecDet(self.files) if original else Machine(
                        lies=lies, take=self.take, ask=ask, number=number, **({'most': paper.MOST} if book else {}))
                    self.booking = book
                    self.original, self.lies, self._level, self.wiped = original, lies, 0, False
                    self.numbered = number is not None
                    if number: self.pending = None                                # played once
                    if ask: self.decoder.context = ('number', paper.MOST) if book else ('number',)
                    self.keyq, self.cur_key, self.key_rest = [], None, 0
                    self.board.power_on()
                elif key == 'OFF' and self.board:
                    self.board.power_off()
            return
        cnt = self.held.get(key, 0) + (1 if down else -1)
        self.held[key] = max(cnt, 0)
        if down and cnt == 1 and self.board:
            self.keyq.append(key)            # the status line follows it when it reaches the board (feed_keys)

    def write_cases(self, lies):
        """After 8 + ON: the cases go to a file, nothing of them to the screen. Two false alibis are checked by the
        solver (seconds each), so a thread writes and the window stays alive."""
        n, self.count = self.count, None
        self.printed = 'Writing %d case%s for the board game and counting the par (seconds per case)...' % (n, 's' * (n > 1))

        def work():
            try:
                lang = load_settings().get('help_lang', 'en')        # the book speaks the language of the help
                if writable(paper.BOOKS):
                    where = os.path.basename(paper.write(n, lies, NAMES, lang)) + ' beside the program'
                else:                                                # read-only folder: the user's folder
                    where = paper.write(n, lies, NAMES, lang, folder=os.path.dirname(FALLBACK))
                self.printed = '%d case%s of %s written to %s, in %s. ' % (
                    n, 's' * (n > 1), 'two false alibis' if lies else 'the usual game', where,
                    {'ru': 'Russian'}.get(lang, 'English'))
            except OSError as e:
                self.printed = 'The cases are not written: %s. ' % e
        threading.Thread(target=work, daemon=True).start()

    def heard(self, key):
        """A key the board takes now: the status line and the score follow it."""
        dec = self.decoder
        was_setup, entry = dec.context[0] == 'setup', list(dec.entry)
        dec.key(key)
        if key != 'ENDTURN':
            self.note = None             # the turn summary goes with the next player's first key
        if was_setup and dec.context[0] == 'crime':
            self.score = Score(dec.level, dec.players)
        elif self.score and key == 'ENTER' and entry[:1] == ['SUSPECT']:
            self.score.suspect()
            if self.par is None:
                self.start_par()
        elif self.score and key == 'ENDTURN':
            line = self.score.end_turn()
            if line:
                self.note = line

    def deaf(self):
        """The board will not take a key now (a sound is playing), so the status line must not follow it either."""
        b = self.board
        if b is None or not b.powered:
            return True
        if isinstance(b, Machine):
            return b.cycles < b.busy_until
        # shortcut: the ROM's other sounds are not known here, only the wait for ON; read its sound state if that matters
        return self.decoder.context[0] == 'setup' and not b.display().strip()

    # --- par: turns the methodical detective of research/solver needs for this case ---
    def start_par(self):
        """Counted by a separate process while the game goes on (seconds of work; this one must not stall)."""
        b = self.board
        case = b.case if hasattr(b, 'case') else from_ram(b.cpu.ram)     # the ROM's case is ready once keys are taken
        if ANDROID:
            self.par = ParThread(json.loads(json.dumps(case)), self.score.level)   # the same form the process gets
            return
        try:
            self.par = subprocess.Popen(paper.SOLVE + ['case', json.dumps(case), str(self.score.level)],
                                        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
                                        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        except OSError:
            self.par = False                 # no solver here: play without par

    def stop_par(self):
        if self.par and self.par.poll() is None:
            self.par.kill()
        self.par = self.par_msg = None

    def par_text(self):
        """Shown with the final summary, won or lost; nothing while it is still being counted."""
        if not self.par or self.par.poll() is None:
            return ''
        if self.par_msg is None:             # once per game: read the answer, keep the tally
            out = self.par.stdout.read().strip()
            self.timing['par'] = getattr(self.par, 'seconds', None)
            par, sc, self.par_msg = int(out) if out.isdigit() else 0, self.score, ''
            rel = lambda d: 'on par' if d == 0 else '%d %s par' % (abs(d), 'over' if d > 0 else 'under')
            if par:
                self.par_msg = ' Par for this case: %d turns.' % par
            if par and sc and sc.n == 1 and sc.winner == 0 and not self.numbered:   # a known case could be replayed
                name = 'par' + self.kind()                                 # as with the records: per game and level
                tally = load_settings().get(name, {})
                last = tally[str(sc.level)] = (tally.get(str(sc.level), []) + [sc.turns[0] - par])[-TALLY:]
                save_settings(**{name: tally})
                self.par_msg = ' Par for this case: %d turns - you are %s.' % (par, rel(last[-1]))
                if len(last) > 1:
                    self.par_msg += ' Your last %d solved cases on level %d: %s in total.' % (len(last), sc.level, rel(sum(last)))
        return self.par_msg

    # --- drawing ---
    def button(self, sc, r, label, key, down):
        color = {'ON': (50, 160, 90), 'OFF': (205, 70, 60)}.get(key, (60, 140, 210) if key.isdigit() else self.CMD)
        if down:
            color = tuple(min(255, c + 60) for c in color)
        pygame.draw.rect(sc, color, r, border_radius=self.px(8))
        f = self.big if len(label) == 1 else self.small
        words = label.split(' ') if len(label) > 10 else [label]
        for k, wd in enumerate(words):
            t = f.render(wd, True, (245, 245, 245))
            sc.blit(t, (r.centerx - t.get_width() // 2,
                        r.centery + int((k * 16 - len(words) * 8 - (4 if f is self.big else 0)) * self.Z * self.K)))

    def paint_static(self, sc):
        """Everything that does not change: drawn once, blitted every frame."""
        sc.fill((236, 232, 222))
        pygame.draw.rect(sc, (25, 10, 10), self.DISP, border_radius=self.px(8))
        pygame.draw.rect(sc, (255, 255, 250), self.STATUS, border_radius=self.px(6))
        pygame.draw.rect(sc, (150, 150, 140), self.STATUS, 1, border_radius=self.px(6))
        for r, label, key in self.buttons:
            self.button(sc, r, label, key, False)

    def update_status(self):
        self.d = d = self.board.display() if self.board and self.board.powered else ''
        if self.board is not None and not self.board.powered:
            self.decoder.context = ('off',)
        if self.decoder.entry:
            self.status = 'Entering: ' + self.decoder.typing()
        elif self.decoder.context[0] == 'turn' and not d.strip():
            self.status = '%s: SUSPECT, number, ENTER.' % ('Next turn' if self.score and self.score.n == 1 else 'Next player')
        elif d.strip() or self.decoder.context[0] in ('off', 'number', 'setup'):
            self.status = self.decoder.status(d) or self.status
            if self.status.startswith('The victim'):
                self.status = self.case_no() + self.status
            self.track(d)
        if self.board is not None and not self.board.powered:
            self.final = None
            self.status = SAVE_ERROR or 'Switched off. ' + OFF_HINT     # the messages below still go first
        if self.lies and self.decoder.context[0] in ('number', 'setup') and self.board and self.board.powered:
            self.status = 'Two false alibis. ' + self.status      # the rule is in the help: a longer line is cut
        b = self.board
        if isinstance(b, Machine) and b.ask and not b.powered and b.number:
            self.pending, self.count, b.number = (None, b.number, None) if self.booking else (b.number, None, None)
        if self.count and not (b and b.powered):
            self.status = ('%d case%s to write for the board game. Press ON for the usual game, or hold 2 and press ON for two '
                           'false alibis. OFF cancels.' % (self.count, 's' * (self.count > 1)))
        if self.printed and not (b and b.powered):
            self.status = self.printed + ('' if self.printed.endswith('...') else 'ON: a new case.')
        if self.pending and not (b and b.powered):
            self.status = ('Case %d is set. Press ON to play it, or hold 2 and press ON to play it as two false alibis. '
                           'OFF forgets it.'
                           % self.pending)
        if self.wiped and not (self.board and self.board.powered):
            self.status = 'Records and the running score are cleared. ' + OFF_HINT
        if self.wipe_ask:
            self.status = ('Clear the records and the running score of all games? '
                           'ENTER clears them; any other key keeps them.')
        if self.final and not self.decoder.entry and self.decoder.seq == self.final_seq:   # back after a stray key
            self.status = self.final + (' ' + self.case_no()).rstrip() + self.par_text()
        if self.score and not self.score.over and self.decoder.context[0] == 'turn' and self.score.n > 1 \
                and not d.strip() and not self.decoder.entry:
            self.status = '%s: SUSPECT, number, ENTER.' % self.score.name(self.score.cur)
        if self.note and not self.decoder.entry and not self.final:    # turn summary, or who is out: with the prompt
            c = self.decoder.context[0]
            if c == 'turn' and not d.strip():
                self.status = '%s. %s' % (self.note, self.status)
            elif c == 'accuse':
                self.status = '%s. Next player: press END TURN first.' % self.note

    def case_no(self):
        """The number of the case, to tell somebody else or to play it again (the ROM's cases have none)."""
        n = getattr(self.board, 'number', None)
        return 'Case %d. ' % n if n else ''

    def track(self, d):
        """Count each answered private question and each accusation once (per ENTER).
        Wrong accusation: 'N0' flashes; only when everybody is out does the machine show 'NNd1d' (murderer)."""
        dec, sc = self.decoder, self.score
        if not sc or dec.entry:
            return
        t, c = d.replace(' ', ''), dec.context[0]
        if c == 'question' and not sc.over and dec.seq != self.counted and dec.status(d) and t not in ('EE', 'ENd'):
            sc.question(); self.counted = dec.seq
        elif c == 'accuse':
            m = re.match(r'^([0-9b]+)(4E5|d1d)$', t)
            if (m or t == 'N0') and not sc.over and dec.seq != self.counted:
                self.counted = dec.seq
                p = sc.accused(bool(m) and m.group(2) == '4E5')
                self.rec = ''
                if sc.n == 1 and sc.winner == 0 and not self.numbered:
                    name = 'records' + self.kind()                           # the games are not comparable
                    records = load_settings().get(name, {})
                    self.rec = sc.record(records)
                    save_settings(**{name: records})
                if not sc.over:
                    self.note = '%s is out - %s' % (sc.name(p), sc.stats(p))
            if m and sc.over and dec.seq == self.counted and self.final_seq != dec.seq:
                self.final_seq = dec.seq
                head = ('YES! %s is the murderer.' if sc.winner is not None else 'The murderer was %s.') % who(num(m.group(1)))
                self.final = ('%s %s %s' % (head, sc.summary(), self.rec)).strip()

    def running(self):
        """The phone's bottom line of the status field: where the game stands, all the time."""
        sc = self.score
        if self.LINES < 3 or not sc or sc.over:
            return ''
        q = sc.questions[sc.cur]
        return '%sTurn %d  -  %d question%s' % (sc.name(sc.cur) + '  -  ' if sc.n > 1 else '', sc.turns[sc.cur] + 1,
                                                q, '' if q == 1 else 's')

    def wrap(self, text, width, font=None):
        lines, cur = [], ''
        for w in text.split(' '):
            if cur and (font or self.font).size(cur + ' ' + w)[0] > width:
                lines.append(cur); cur = w
            else:
                cur = cur + ' ' + w if cur else w
        return lines + [cur]

    def draw_cover(self, sc):
        r = self.DISP
        pygame.draw.rect(sc, (70, 70, 80), r, border_radius=self.px(8))
        sc.set_clip(r.inflate(-self.px(12), -self.px(12)))     # hatching inside the rounded frame
        for x in range(r.x - r.h, r.right, self.px(14)):
            pygame.draw.line(sc, (90, 90, 100), (x, r.y), (x + r.h, r.bottom), self.px(5))
        sc.set_clip(None)
        t = self.small.render('PRIVATE ANSWER  -  ' + ('touch here' if ANDROID else 'hold SPACE'), True, (240, 240, 240))
        sc.blit(t, t.get_rect(center=r.center))
        pygame.draw.rect(sc, (255, 255, 250), self.STATUS.inflate(-2, -2), border_radius=self.px(6))

    # --- the '?' screen: the rules, in pages
    def help_rect(self):
        s = self.px(18 * self.Z)
        return pygame.Rect(self.STATUS.right - s - self.px(6), self.STATUS.bottom - s - self.px(6), s, s)

    def sound_rect(self):
        """The speaker above the '?', in the same narrow column: sound on or off."""
        r = self.help_rect()
        return r.move(0, self.STATUS.top + self.px(6) - r.y)

    def toggle_sound(self):
        self.muted = not self.muted; save_settings(muted=self.muted)

    def draw_speaker(self, sc):
        r, col, w = self.sound_rect(), (110, 110, 100), max(1, self.px(1.5))
        x, y, u = r.x, r.centery, r.w / 8
        pygame.draw.polygon(sc, col, [(x + u, y - u), (x + 2.5 * u, y - u), (x + 4.5 * u, y - 3 * u),
                                      (x + 4.5 * u, y + 3 * u), (x + 2.5 * u, y + u), (x + u, y + u)])
        if self.muted:
            pygame.draw.line(sc, col, (x + 5.5 * u, y - 1.5 * u), (x + 8 * u, y + 1.5 * u), w)
            pygame.draw.line(sc, col, (x + 5.5 * u, y + 1.5 * u), (x + 8 * u, y - 1.5 * u), w)
        else:
            for rad in (3.4, 5.6):           # the waves, clear of the cone
                a = pygame.Rect(0, 0, 2 * rad * u, 2 * rad * u); a.center = (x + 3 * u, y)
                pygame.draw.arc(sc, col, a, -0.8, 0.8, w)

    def help_bar(self):
        """The keys under a page: back, smaller and larger text, the other language, forward, close."""
        h, w = self.KEY_H * 3 // 4, (self.CW - 5 * self.GAP) // 6
        names = ('<', 'A-', 'A+', 'RU' if self.lang == 'en' else 'EN', '>', 'X')
        return [(pygame.Rect(self.M + i * (w + self.GAP), self.H - self.M - h, w, h), n) for i, n in enumerate(names)]

    def help_fonts(self):
        """Text and headings of the help, in the size the reader chose (steps of 12 %)."""
        if getattr(self, '_fonts_src', None) != self.size:
            px = 15 * self.K * (self.Z if self.LINES > 2 else 1) * 1.12 ** self.size
            self._fonts_src = self.size
            self._fonts = font(int(px)), font(int(px * 1.15), bold=True)
        return self._fonts

    def help_pages(self):
        """The text of the current language as pages of (font, line): wrapped to the width, cut to the height."""
        if getattr(self, '_help_src', None) != (self.lang, self.size):
            body, head = self.help_fonts()
            step, room = body.get_linesize(), self.help_bar()[0][0].top - self.M - 2 * body.get_linesize()
            pages, page, y = [], [], 0
            texts = [t for text in HELP[self.lang] for t in                         # '@cards': who can be asked what
                     (['%d %s:  %s' % (s, NAMES[s - 1], ', '.join(map(str, CARDS[s]))) for s in sorted(CARDS)]
                      if text == '@cards' else [text])] + ['', 'Electronic Detective ' + VERSION]

            def cut(text):
                if text.startswith('# '): return [(head, t) for t in self.wrap(text[2:], self.CW, head)]
                return [(body, t) for t in self.wrap(text, self.CW, body)] if text else [(None, '')]
            for k, text in enumerate(texts):
                lines = cut(text)
                if text.startswith('# '):                                           # a heading keeps two lines of text
                    after = [ln for t in texts[k + 1:k + 3] for ln in cut(t) if ln[1]]
                    if y + step * (len(lines) + min(2, len(after))) > room and page:
                        pages.append(page); page, y = [], 0
                    page += lines; y += step * len(lines)
                    continue
                for ln in lines:                                                    # a paragraph goes on line by line
                    if y + step > room and page:
                        pages.append(page); page, y = [], 0
                    if page or ln[1]:                                               # no gap at the top of a page
                        page.append(ln); y += step
            self._help_src, self._help_pages = (self.lang, self.size), pages + [page]
        return self._help_pages

    def help_do(self, name):
        if name == 'X': self.help = None
        elif name in ('A-', 'A+'):
            first = self.help_pages()[self.help][0][1]              # stay at the text that was being read
            self.size = max(-2, min(5, self.size + (1 if name == 'A+' else -1))); save_settings(help_size=self.size)
            self.help = next((k for k, pg in enumerate(self.help_pages()) if any(t == first for _, t in pg)),
                             min(self.help, len(self.help_pages()) - 1))
        elif name in ('EN', 'RU'):
            self.lang = name.lower(); save_settings(help_lang=self.lang)
            self.help = min(self.help, len(self.help_pages()) - 1)
        else: self.help = max(0, min(len(self.help_pages()) - 1, self.help + (1 if name == '>' else -1)))

    def tap(self, pos):
        """A touch or a click: the '?' and its screen take it before the keys of the machine do."""
        if self.help is None:
            if self.sound_rect().inflate(self.px(20), self.px(8)).collidepoint(pos):
                self.toggle_sound()
                return True
            if self.help_rect().inflate(self.px(20), self.px(20)).collidepoint(pos):
                self.help = 0
                return True
            return False
        for r, name in self.help_bar():
            if r.collidepoint(pos): self.help_do(name)
        return True

    def draw_help(self):
        sc, pages = self.screen, self.help_pages()
        sc.fill((250, 248, 240))
        body = self.help_fonts()[0]
        for k, (f, t) in enumerate(pages[self.help]):
            if t: sc.blit(f.render(t, True, (20, 20, 20) if f is body else (40, 105, 175)), (self.M, self.M + k * body.get_linesize()))
        note = '%d / %d' % (self.help + 1, len(pages)) + ''.join(
            '     %s %.1f s' % (n, self.timing[n]) for n in ('deal', 'par') if self.timing.get(n))
        bar = self.help_bar()
        sc.blit(self.font.render(note, True, (120, 120, 110)), (self.M, bar[0][0].top - self.font.get_linesize() * 3 // 2))
        for r, name in bar:
            self.button(sc, r, name, 'help', False)
        pygame.display.flip()

    def draw(self):
        if self.help is not None:
            self.update_status()                 # the game goes on behind the page
            return self.draw_help()
        sc = self.screen
        sc.blit(self.static, (0, 0))
        if hasattr(self.board, 'brightness'):    # the original ROM: how long each segment was lit
            levels = self.board.brightness()
        else:                                    # our own machine draws steady digits
            levels = [[s >> b & 1 for b in range(7)] for s in (self.board.segments() if self.board else [0] * 7)]
        for i, s in enumerate(levels):
            draw_digit(sc, self.DISP.centerx - self.px(232) + i * self.px(70), self.DISP.centery - self.px(self.DIGIT[1] / 2),
                       self.px(self.DIGIT[0]), self.px(self.DIGIT[1]), s, (255, 40, 40), (55, 18, 18))
        self.update_status()
        pin = self.running()
        if (self.status, pin) != getattr(self, '_status_src', None):
            f, room, self._step = self.font, self.LINES - bool(pin), self.px(19 * self.Z)
            wide = self.CW - self.px(24) - self.help_rect().w
            if self.LINES > 2 and len(self.wrap(self.status, wide)) > room:
                f, room, self._step = self.fine, 5, self.px(19 * self.Z * 4 / 5)     # the phone's long final summary
            self._status_src, self._status_lines = (self.status, pin), [
                f.render(t, True, (20, 20, 20)) for t in self.wrap(self.status, wide, f)[:room]]
            self._pin = self.font.render(pin, True, (120, 120, 110))
        lines = self._status_lines
        if pin:
            sc.blit(self._pin, (self.STATUS.x + self.px(12), self.STATUS.y + self.px(7) + (self.LINES - 1) * self.px(19 * self.Z)))
        if self.decoder.is_private(self.d) and not (self.peek_key or self.peek_mouse or None in self.fingers.values()):
            self.draw_cover(sc)
            c = self.decoder.context
            lines = [self.font.render(t, True, (20, 20, 20)) for t in self.wrap(
                'Q%s for %s: %s here to see the answer.' % (c[1], who(c[2]), 'touch' if ANDROID else 'hold SPACE or click'), self.CW - self.px(24))[:self.LINES]]
        step = self._step if lines is self._status_lines else self.px(19 * self.Z)
        for k, img in enumerate(lines):
            sc.blit(img, (self.STATUS.x + self.px(12), self.STATUS.y + self.px(7) + k * step))
        r = self.help_rect()
        pygame.draw.circle(sc, (150, 150, 140), r.center, r.w // 2, max(1, self.px(1.5)))
        t = self.small.render('?', True, (110, 110, 100))
        sc.blit(t, t.get_rect(center=r.center))
        self.draw_speaker(sc)
        for r, label, key in self.buttons:
            if self.held.get(key, 0) > 0:
                self.button(sc, r, label, key, True)
        if not ANDROID:
            sc.blit(self.hint_img, self.hint_img.get_rect(center=(self.W // 2, self.H - 22)))
        pygame.display.flip()

    def run(self):
        clock = pygame.time.Clock()
        mouse_key = None
        keymap = {pc: key for _, key, pc, *_ in PAD}
        keymap.update(NUMPAD)
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    return
                if e.type == pygame.KEYDOWN and (e.key == pygame.K_F1 or self.help is not None):
                    if self.help is None: self.help = 0
                    else: self.help_do({pygame.K_LEFT: '<', pygame.K_RIGHT: '>', pygame.K_SPACE: '>',
                                        pygame.K_l: self.help_bar()[3][1], pygame.K_MINUS: 'A-', pygame.K_KP_MINUS: 'A-',
                                        pygame.K_EQUALS: 'A+', pygame.K_KP_PLUS: 'A+'}.get(e.key, 'X'))
                    continue
                if e.type == pygame.KEYDOWN and e.key == pygame.K_m:
                    self.toggle_sound()
                elif e.type in (pygame.KEYDOWN, pygame.KEYUP) and e.key in keymap:
                    if e.type == pygame.KEYDOWN and getattr(e, 'repeat', False):
                        continue
                    self.press(keymap[e.key], e.type == pygame.KEYDOWN)
                elif e.type in (pygame.KEYDOWN, pygame.KEYUP) and e.key == pygame.K_SPACE:
                    self.peek_key = e.type == pygame.KEYDOWN
                elif e.type == pygame.FINGERDOWN:           # every finger is a key of its own: 1 + ON needs two
                    ww, wh = self.window.get_size()
                    pos = (e.x * ww, e.y * wh)
                    if self.tap(pos):
                        continue
                    key = next((k for r, _, k in self.buttons if r.collidepoint(pos)), None)
                    if key:
                        self.press(key, True)
                    elif not (self.DISP.collidepoint(pos) or self.STATUS.collidepoint(pos)):
                        continue
                    self.fingers[e.finger_id] = key
                elif e.type == pygame.FINGERUP and e.finger_id in self.fingers:
                    key = self.fingers.pop(e.finger_id)
                    if key:
                        self.press(key, False)
                elif e.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP) and getattr(e, 'touch', False):
                    pass                                    # the same touch again, as a mouse: already handled
                elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.tap(e.pos):
                    pass
                elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and (
                        self.DISP.collidepoint(e.pos) or self.STATUS.collidepoint(e.pos)):
                    self.peek_mouse = True
                elif e.type == pygame.MOUSEBUTTONUP and e.button == 1 and self.peek_mouse:
                    self.peek_mouse = False
                elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    for r, _, key in self.buttons:
                        if r.collidepoint(e.pos):
                            mouse_key = key; self.press(key, True)
                elif e.type == pygame.MOUSEBUTTONUP and e.button == 1 and mouse_key:
                    self.press(mouse_key, False); mouse_key = None
            if self.audio is not None:
                self.pump_audio()
            else:                         # wall-clock pacing without sound
                self.clock_left += clock.get_time() / 1000
                while self.clock_left >= CHUNK:
                    self.emulate(CHUNK); self.clock_left -= CHUNK
            self.draw()
            clock.tick(60)


def main():
    Game(rom=sys.argv[1] if len(sys.argv) > 1 else None).run()
    # Any SDL audio shutdown (pause/close/pygame.quit) can deadlock against the audio callback waiting for the GIL,
    # so close the window and leave without it; nothing needs saving at exit.
    pygame.display.quit()
    os._exit(0)


if __name__ == '__main__':
    main()
