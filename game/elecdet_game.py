"""Electronic Detective (Ideal, 1979) in a window.

    python elecdet_game.py [path to ROM folder or elecdet.zip]      (the ROM is needed only for 1 + ON)

Keys: 0-9, S = Suspect, Q = Private Question, A = I Accuse, Enter, T = End Turn, O = On, X = Off.
ON starts our own machine (machine.py: same rules and behaviour, cases dealt at random, no ROM needed).
ON pressed while 1 is held runs the original ROM in the emulator, with the regularities of its deals;
2 + ON is kept for a game with rules of our own (not made yet: the machine stays off).
Suspect cards are not shown: use the paper cards or the PDF.
"""
import array, json, os, re, subprocess, sys, threading
import pygame
from board import ElecDet, IPS, SEG, load_romset
from machine import Machine
from rules import from_ram

TALLY = 10                               # solved cases kept for the running score against par
PAR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'research', 'solver', 'par.py')

HERE = os.path.dirname(os.path.abspath(__file__))
SETTINGS = os.path.join(HERE, 'settings.json')
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
NUMPAD = {getattr(pygame, 'K_KP%d' % i): str(i) for i in range(10)}
NUMPAD[pygame.K_KP_ENTER] = 'ENTER'
OFF_HINT = 'Press ON to start a game without patterns (the shell deals the case), or hold 1 and press ON for an original game.'


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
        if k == 'ON':
            self.entry, self.context, self.victim = [], ('setup',), None
        elif k == 'ENTER':
            e, self.entry = self.entry, []
            digits = ''.join(x for x in e if x.isdigit())
            n = int(digits) if digits else None
            self.seq += 1
            if self.context[0] == 'setup':
                self.context = ('crime',)
                self.level = int(digits[0]) if digits else 0
                self.players = int(digits[1]) if len(digits) > 1 else 1   # level, players
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
            return '%s: "I was %s."' % (who(s), ', '.join(parts)) if parts else ''
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


def draw_digit(surf, x, y, w, h, segs, on, off):
    """Seven-segment digit; bit 0..6 = a..g."""
    t = max(3, w // 6)
    hs = [(x + t, y, w - 2 * t, t), (x + w - t, y + t, t, h // 2 - t), (x + w - t, y + h // 2, t, h // 2 - t),
          (x + t, y + h - t, w - 2 * t, t), (x, y + h // 2, t, h // 2 - t), (x, y + t, t, h // 2 - t),
          (x + t, y + h // 2 - t // 2, w - 2 * t, t)]
    for b, r in enumerate(hs):
        pygame.draw.rect(surf, on if segs >> b & 1 else off, r, border_radius=t // 2)


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


def save_settings(**changes):
    data = load_settings(); data.update(changes)
    json.dump(data, open(SETTINGS, 'w'), indent=1)


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


class Game:
    HINT = 'S Suspect   Q Question   A Accuse   T End Turn   O/X On/Off   Space Peek'
    M, U, KEY_H, GAP = 24, 91, 56, 12    # outer margin, key width/height, gap
    CW = 5 * U + 4 * GAP                 # keypad width = width of every area
    W = CW + 2 * M
    DISP = pygame.Rect(M, M, CW, 100)
    STATUS = pygame.Rect(M, DISP.bottom + 14, CW, 52)
    PAD_TOP = STATUS.bottom + 16
    H = PAD_TOP + 5 * KEY_H + 4 * GAP + 44

    par = par_msg = None                 # the solver's process for this case; its line in the final summary

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
        self.buf, self.lock, self.underruns = bytearray(), threading.Lock(), 0
        try:
            from pygame._sdl2 import audio
            self.audio = audio.AudioDevice(None, False, RATE, audio.AUDIO_S16, 1, 512, 0, self.fill_audio)
            self.audio.pause(0)
        except Exception as e:           # no audio device: run on the wall clock
            print('Sound disabled:', e)
            self.audio = None
        self.screen = pygame.display.set_mode((self.W, self.H))
        pygame.display.set_caption('Electronic Detective')
        self.font = pygame.font.SysFont('arial', 15)
        self.small = pygame.font.SysFont('arial', 13, bold=True)
        self.big = pygame.font.SysFont('arial', 26, bold=True)
        self.hint_img = self.small.render(self.HINT, True, (110, 110, 100))
        self.buttons = []
        for label, key, _, col, row, w in PAD:
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
            samples = array.array('h', (v * 5000 for v in self.emulate(CHUNK)))
            self._last = samples[-1]
            with self.lock:
                self.buf += samples.tobytes()

    # --- input ---
    def press(self, key, down):
        if key in ('ON', 'OFF'):
            original = bool(self.held.get('1'))      # a held digit picks the game: 1 + ON, 2 + ON
            if key == 'ON' and down and self.held.get('2'):
                return                       # the game with our own rules is not made yet
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
                if key == 'ON' and (self.board is None or not self.board.powered):
                    self.board = ElecDet(self.files) if original else Machine()
                    self.original, self._level = original, 0
                    self.keyq, self.cur_key, self.key_rest = [], None, 0
                    self.board.power_on()
                elif key == 'OFF' and self.board:
                    self.board.power_off()
            return
        cnt = self.held.get(key, 0) + (1 if down else -1)
        self.held[key] = max(cnt, 0)
        if down and cnt == 1 and self.board:
            self.keyq.append(key)
        if down and cnt == 1:
            dec = self.decoder
            was_setup, entry = dec.context[0] == 'setup', list(dec.entry)
            dec.key(key)
            if key != 'ENDTURN':
                self.note = None             # the turn summary goes with the next player's first key
            self.final = None
            if was_setup and key == 'ENTER':
                self.score = Score(dec.level, dec.players)
            elif self.score and key == 'ENTER' and entry[:1] == ['SUSPECT']:
                self.score.suspect()
                if self.par is None:
                    self.start_par()
            elif self.score and key == 'ENDTURN':
                line = self.score.end_turn()
                if line:
                    self.note = line

    # --- par: turns the methodical detective of research/solver needs for this case ---
    def start_par(self):
        """Counted by a separate process while the game goes on (seconds of work; this one must not stall)."""
        b = self.board
        case = b.case if hasattr(b, 'case') else from_ram(b.cpu.ram)     # the ROM's case is ready once keys are taken
        try:
            self.par = subprocess.Popen([sys.executable, PAR, 'case', json.dumps(case), str(self.score.level)],
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
            par, sc, self.par_msg = int(out) if out.isdigit() else 0, self.score, ''
            rel = lambda d: 'on par' if d == 0 else '%d %s par' % (abs(d), 'over' if d > 0 else 'under')
            if par:
                self.par_msg = ' Par for this case: %d turns.' % par
            if par and sc and sc.n == 1 and sc.winner == 0:
                name = 'par' if self.original else 'par_fair'              # as with the records: per mode and level
                tally = load_settings().get(name, {})
                last = tally[str(sc.level)] = (tally.get(str(sc.level), []) + [sc.turns[0] - par])[-TALLY:]
                save_settings(**{name: tally})
                self.par_msg = ' Par for this case: %d turns - you are %s.' % (par, rel(last[-1]))
                if len(last) > 1:
                    self.par_msg += ' Your last %d solved cases on level %d: %s in total.' % (len(last), sc.level, rel(sum(last)))
        return self.par_msg

    # --- drawing ---
    def button(self, sc, r, label, key, down):
        color = (120, 185, 235) if down else (60, 140, 210)
        pygame.draw.rect(sc, color, r, border_radius=8)
        f = self.big if len(label) == 1 else self.small
        words = label.split(' ') if len(label) > 10 else [label]
        for k, wd in enumerate(words):
            t = f.render(wd, True, (245, 245, 245))
            sc.blit(t, (r.centerx - t.get_width() // 2, r.centery - len(words) * 8 + k * 16 - (4 if f is self.big else 0)))

    def paint_static(self, sc):
        """Everything that does not change: drawn once, blitted every frame."""
        sc.fill((236, 232, 222))
        pygame.draw.rect(sc, (25, 10, 10), self.DISP, border_radius=8)
        pygame.draw.rect(sc, (255, 255, 250), self.STATUS, border_radius=6)
        pygame.draw.rect(sc, (150, 150, 140), self.STATUS, 1, border_radius=6)
        for r, label, key in self.buttons:
            self.button(sc, r, label, key, False)

    def update_status(self):
        self.d = d = self.board.display() if self.board and self.board.powered else ''
        if self.board is not None and not self.board.powered:
            self.decoder.context = ('off',)
        if self.decoder.entry:
            self.status = 'Entering: ' + self.decoder.typing()
        elif self.decoder.context[0] == 'turn' and not d.strip():
            self.status = 'Next player: SUSPECT, number, ENTER.'
        elif d.strip() or self.decoder.context[0] in ('off', 'setup'):
            self.status = self.decoder.status(d) or self.status
            self.track(d)
        if self.board is not None and not self.board.powered:
            self.final = None
            self.status = 'Switched off. ' + OFF_HINT
        if self.final and not self.decoder.entry:
            self.status = self.final + self.par_text()
        if self.score and not self.score.over and self.decoder.context[0] == 'turn' and self.score.n > 1 \
                and not d.strip() and not self.decoder.entry:
            self.status = '%s: SUSPECT, number, ENTER.' % self.score.name(self.score.cur)
        if self.note and not self.decoder.entry and not self.final:    # turn summary, or who is out: with the prompt
            c = self.decoder.context[0]
            if c == 'turn' and not d.strip():
                self.status = '%s. %s' % (self.note, self.status)
            elif c == 'accuse':
                self.status = '%s. Next player: press END TURN first.' % self.note

    def track(self, d):
        """Count each answered private question and each accusation once (per ENTER).
        Wrong accusation: 'N0' flashes; only when everybody is out does the machine show 'NNd1d' (murderer)."""
        dec, sc = self.decoder, self.score
        if not sc or dec.entry:
            return
        t, c = d.replace(' ', ''), dec.context[0]
        if c == 'question' and not sc.over and dec.seq != self.counted and dec.status(d):
            sc.question(); self.counted = dec.seq
        elif c == 'accuse':
            m = re.match(r'^([0-9b]+)(4E5|d1d)$', t)
            if (m or t == 'N0') and not sc.over and dec.seq != self.counted:
                self.counted = dec.seq
                p = sc.accused(bool(m) and m.group(2) == '4E5')
                self.rec = ''
                if sc.n == 1 and sc.winner == 0:
                    name = 'records' if self.original else 'records_fair'    # the two modes are not comparable
                    records = load_settings().get(name, {})
                    self.rec = sc.record(records)
                    save_settings(**{name: records})
                if not sc.over:
                    self.note = '%s is out - %s' % (sc.name(p), sc.stats(p))
            if m and sc.over and dec.seq == self.counted and self.final_seq != dec.seq:
                self.final_seq = dec.seq
                head = ('YES! %s is the murderer.' if sc.winner is not None else 'The murderer was %s.') % who(num(m.group(1)))
                self.final = ('%s %s %s' % (head, sc.summary(), self.rec)).strip()

    def wrap(self, text, width):
        lines, cur = [], ''
        for w in text.split(' '):
            if cur and self.font.size(cur + ' ' + w)[0] > width:
                lines.append(cur); cur = w
            else:
                cur = cur + ' ' + w if cur else w
        return lines + [cur]

    def draw_cover(self, sc):
        r = self.DISP
        pygame.draw.rect(sc, (70, 70, 80), r, border_radius=8)
        sc.set_clip(r.inflate(-12, -12))                       # hatching inside the rounded frame
        for x in range(r.x - r.h, r.right, 14):
            pygame.draw.line(sc, (90, 90, 100), (x, r.y), (x + r.h, r.bottom), 5)
        sc.set_clip(None)
        t = self.small.render('PRIVATE ANSWER  -  hold SPACE', True, (240, 240, 240))
        sc.blit(t, t.get_rect(center=r.center))
        pygame.draw.rect(sc, (255, 255, 250), self.STATUS.inflate(-2, -2), border_radius=6)

    def draw(self):
        sc = self.screen
        sc.blit(self.static, (0, 0))
        segs = self.board.segments() if self.board else [0] * 7
        for i, s in enumerate(segs):
            draw_digit(sc, self.DISP.centerx - 232 + i * 70, self.DISP.y + 16, 44, 68, s, (255, 40, 40), (55, 18, 18))
        self.update_status()
        if self.status != getattr(self, '_status_src', None):
            self._status_src, self._status_lines = self.status, [
                self.font.render(t, True, (20, 20, 20)) for t in self.wrap(self.status, self.CW - 24)[:2]]
        lines = self._status_lines
        if self.decoder.is_private(self.d) and not (self.peek_key or self.peek_mouse):
            self.draw_cover(sc)
            c = self.decoder.context
            lines = [self.font.render(t, True, (20, 20, 20)) for t in self.wrap(
                'Q%s for %s: hold SPACE or click here to see the answer.' % (c[1], who(c[2])), self.CW - 24)[:2]]
        for k, img in enumerate(lines):
            sc.blit(img, (self.STATUS.x + 12, self.STATUS.y + 7 + k * 19))
        for r, label, key in self.buttons:
            if self.held.get(key, 0) > 0:
                self.button(sc, r, label, key, True)
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
                if e.type in (pygame.KEYDOWN, pygame.KEYUP) and e.key in keymap:
                    if e.type == pygame.KEYDOWN and getattr(e, 'repeat', False):
                        continue
                    self.press(keymap[e.key], e.type == pygame.KEYDOWN)
                elif e.type in (pygame.KEYDOWN, pygame.KEYUP) and e.key == pygame.K_SPACE:
                    self.peek_key = e.type == pygame.KEYDOWN
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
