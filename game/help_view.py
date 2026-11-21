"""The '?' screen: the text of help_text.py laid out in pages and drawn; a mixin of the Game window.

Markup of a line of help_text.HELP (one line = one paragraph):
  '# t'  a chapter of the rules     '#+ t'  a chapter of a game     '## t'  a chapter of the quick reference
  '### t' a subheading   '- t' an item   '1. t' a numbered item   '> t' a note in a tinted box   '' a little gap
  '@questions', '@cards': the tables.  In any text: **bold**, and [KEY] - a key of the machine, drawn as one.
A chapter opens a page, so the contents (page 0) leads to its top.
"""
import re
import pygame
from rules import CARDS

INK, BLUE, GREY, PAPER = (30, 30, 30), (40, 105, 175), (125, 120, 110), (250, 248, 240)
TINT, STRIPE, TILE, RULE = (226, 236, 248), (242, 238, 228), (236, 232, 222), (205, 200, 188)
TOKEN = re.compile(r'(\*\*.+?\*\*|\[[^\]]+\])')
GROUPS = {'#': 0, '#+': 1, '##': 2}                  # the marks of the chapters -> groups of the contents


DASHES = [(re.compile(r' - '), ' \u2013 '), (re.compile(r'\b([0-9]+|[A-F])-([0-9]+|[A-F])\b'), '\\1\u2013\\2')]


SOFT = 2


def tokens(text, base='r'):
    """[word, style, glued to the one before: False, True (never parted) or SOFT (no space, but a line may end
    there - after _ and / of a long name)]; style: r(egular), b(old), k(ey). A spaced hyphen and a hyphen of a
    range (1-4, A-F) become dashes."""
    for pattern, dash in DASHES:
        text = pattern.sub(dash, text)
    text = text.replace('] + [', ']\u00a0+\u00a0[')
    out, spaced = [], True
    for part in TOKEN.split(text):
        if not part:
            continue
        if part[0] == '[' and part[-1] == ']':
            out.append((part[1:-1], 'k', not spaced)); spaced = False
            continue
        style, s = ('b', part[2:-2]) if part[:2] == '**' else (base, part)
        for i, w in enumerate(s.split(' ')):
            for j, part in enumerate(re.split(r'(?<=[_/])', w)):
                if part: out.append((part, style, (i == 0 and not spaced) if j == 0 else SOFT))
        spaced = s.endswith(' ')
    return out


class Layout:
    """The help of one language at one text size: pages of lines, and the contents.
    A line is (height, ops, background, keep with the next one, source item); an op is ('t', x, font, text, colour)
    or ('k', x, text). Page 0 stays empty: the contents are drawn over it."""

    def __init__(self, items, f, width, room, names, questions):
        self.f, self.width = f, width
        self.step = int(f['r'].get_linesize() * 1.3)
        self.pad = f['k'].size(' ')[0] * 2
        lines, toc = [], []
        for src, text in enumerate(items):
            mark = text.split(' ', 1)[0] if text.startswith('#') else ''
            if mark in GROUPS:
                toc.append((text[len(mark):].strip(), len(lines), GROUPS[mark]))
                lines.append('page')
                lines += self.flow(text[len(mark):].strip(), 'h', 0, BLUE, src, keep=True)
                lines.append(self.gap(0.5, src))
            elif mark == '###':
                lines.append(self.gap(0.6, src))
                lines += self.flow(text[4:], 's', 0, INK, src, keep=True)
                lines.append(self.gap(0.2, src, keep=True))
            elif text == '@questions':
                lines += self.questions(questions, src)
            elif text == '@cards':
                lines += self.cards(names, src)
            elif text.startswith('- '):
                lines += self.flow(text[2:], 'r', self.indent('•'), INK, src, lead='•')
                lines.append(self.gap(0.25, src))
            elif re.match(r'\d+\. ', text):
                n, rest = text.split(' ', 1)
                lines += self.flow(rest, 'r', self.indent('8.'), INK, src, lead=n)
                lines.append(self.gap(0.25, src))
            elif text.startswith('> '):
                lines.append(self.gap(0.4, src, 'tint', keep=True))
                lines += [ln[:2] + ('tint', True, src) for ln in self.flow(text[2:], 'r', self.pad, INK, src, width=width - self.pad)]
                lines.append(self.gap(0.4, src, 'tint'))
                lines.append(self.gap(0.4, src))
            elif text:
                lines += self.flow(text, 'r', 0, INK, src)
                lines.append(self.gap(0.35, src))
            else:
                lines.append(self.gap(0.3, src))
        self.pages, at = self.paginate(lines, room)       # at: index of a chapter's mark -> its page
        self.toc = [(title, at[k], group) for title, k, group in toc]

    def gap(self, n, src, bg=None, keep=False):
        return int(self.step * n), [], bg, keep, src

    def indent(self, sample):
        return self.f['b'].size(sample + '  ')[0]

    def key_w(self, text):
        return self.f['k'].size(text)[0] + 2 * self.pad

    def flow(self, text, base, x0, colour, src, lead=None, keep=False, width=None, whole=False):
        """A paragraph wrapped from x0 to the width: its lines (keep: all kept with what follows; whole: not split).
        Words glued together (a key and its full stop, [2] + [ON]) move to the next line together."""
        width, font = (width or self.width), {'h': 'h', 's': 's'}.get(base, 'r')
        space = self.f[font].size(' ')[0]
        rows, row, x, start = [], [], x0, 0               # start: where the run of glued words began in the row
        for word, style, glued in tokens(text, base if base in 'hs' else 'r'):
            fk = font if style in 'hs' else style
            w = self.key_w(word) if style == 'k' else self.f[fk].size(word)[0]
            if glued is not True: start = len(row)
            gap = 0 if glued or not row else space
            if row and x + gap + w > width and start > 0:     # the run (perhaps just this word) goes down whole
                run = row[start:]
                rows.append(row[:start])
                shift = run[0][1] - x0 if run else x - x0
                row, x, start, gap = [op[:1] + (op[1] - shift,) + op[2:] for op in run], x - shift, 0, 0
            row.append(('k', x + gap, word) if style == 'k' else ('t', x + gap, fk, word, colour)); x += gap + w
        rows.append(row)
        if lead:
            rows[0].insert(0, ('t', 0, 'b', lead, BLUE))
        h = int(self.f[font].get_linesize() * 1.3) if font != 'r' else self.step
        return [(h, r, None, keep or whole and k < len(rows) - 1, src) for k, r in enumerate(rows)]

    def table_row(self, left, text, right, src, shade):
        """A row of a table: a number (bold, blue) at the left, wrapped text, a value at the right; never split."""
        num_w, right_w = self.indent('14'), self.f['r'].size(right)[0] + self.pad if right else 0
        rows = self.flow(text, 'r', num_w, INK, src, width=self.width - right_w, whole=True)
        out = []
        for k, (h, ops, _, keep, _) in enumerate(rows):
            if k == 0:
                ops = [('t', 0, 'b', left, BLUE)] + ops + ([('t', self.width - right_w + self.pad // 2, 'r', right, GREY)] if right else [])
            out.append((h, ops, 'stripe' if shade else None, keep, src))
        return out

    def questions(self, questions, src):
        out = []
        for k, q in enumerate(questions):                    # '3  What area did the murderer go to?  3 / 4 / 5'
            n, text, ans = (q.split('  ') + ['YES / NO'])[:3]
            out += self.table_row(n, text, ans.replace('-', '–'), src, k % 2 == 0)
        return out + [self.gap(0.35, src)]

    def cards(self, names, src):
        out = []
        for s in sorted(CARDS):
            out += self.table_row(str(s), names[s - 1], '  '.join(map(str, CARDS[s])), src, s % 2 == 1)
        return out + [self.gap(0.35, src)]

    @staticmethod
    def paginate(lines, room):
        """Pages of lines: a chapter opens a page; a line kept with the next ones goes with them (a paragraph, a row
        of a table, a heading and what follows) unless they are longer than a page; no plain gap opens a page.
        Returns the pages and {index of a chapter's mark: its page}."""
        pages, page, y, at = [[]], [], 0, {}
        for k, ln in enumerate(lines):
            if ln == 'page':
                if page: pages.append(page)
                page, y, at[k] = [], 0, len(pages)
                continue
            need = ln[0]
            for nxt in lines[k + 1:] if ln[3] else ():
                if nxt == 'page': break
                need += nxt[0]
                if not nxt[3]: break
            if page and y + (need if need <= room else ln[0]) > room:
                pages.append(page); page, y = [], 0
            if not page and not ln[1] and not ln[2]:
                continue                                     # no gap at the top of a page
            page.append(ln); y += ln[0]
        pages.append(page)
        return pages, at

    def draw(self, sc, page, x, y):
        f, kh = self.f, self.f['k'].get_linesize() + self.pad // 2
        for h, ops, bg, _, _ in self.pages[page]:
            if bg:
                pygame.draw.rect(sc, TINT if bg == 'tint' else STRIPE, (x - self.pad, y, self.width + 2 * self.pad, h))
                if bg == 'tint':
                    pygame.draw.rect(sc, BLUE, (x - self.pad, y, max(2, self.pad // 2), h))
            for op in ops:
                if op[0] == 't':
                    _, ox, fk, text, colour = op
                    img = f[fk].render(text, True, colour)
                    sc.blit(img, (x + ox, y + (h - img.get_height()) // 2))
                else:
                    _, ox, text = op
                    r = pygame.Rect(x + ox, y + (h - kh) // 2, self.key_w(text), kh)
                    pygame.draw.rect(sc, (255, 255, 252), r, border_radius=max(2, kh // 5))
                    pygame.draw.rect(sc, (95, 95, 90), r, max(1, kh // 14), border_radius=max(2, kh // 5))
                    img = f['k'].render(text, True, INK)
                    sc.blit(img, img.get_rect(center=r.center))
            y += h


class HelpScreen:
    """The '?' screen of the Game: the contents, the chapters in pages, the keys around them.
    Uses of the Game: px, K, Z, LINES, M, CW, H, screen, lang, size, help, timing; help_font(size, bold),
    help_save(**settings), and help_source() = (items, names, questions, titles of the contents, version)."""

    def help_fonts(self):
        """The fonts of the help in the size the reader chose (steps of 12 %)."""
        font = self.help_font
        if getattr(self, '_fonts_src', None) != self.size:
            px = 15 * self.K * (self.Z if self.LINES > 2 else 1) * 1.12 ** self.size
            self._fonts_src = self.size
            self._fonts = {'r': font(int(px)), 'b': font(int(px), bold=True), 'h': font(int(px * 1.35), bold=True),
                           's': font(int(px * 1.08), bold=True), 'k': font(int(px * 0.78), bold=True),
                           'btn': font(int(15 * self.K * (self.Z if self.LINES > 2 else 1)), bold=True)}
        return self._fonts

    def help_frame(self):
        """The rects of the header (keys), the page and the footer (back, the page number, forward)."""
        h = int(self.help_fonts()['btn'].get_linesize() * 2.1)
        head = pygame.Rect(self.M, self.M, self.CW, h)
        foot = pygame.Rect(self.M, self.H - self.M - h, self.CW, h)
        body = pygame.Rect(self.M, head.bottom + h // 2, self.CW, foot.top - head.bottom - h)
        return head, body, foot

    def help_bar(self):
        """The keys: [contents] ... [A-] [A+] [language] [close] above, [<] ... [>] below. The language stays 4th."""
        head, _, foot = self.help_frame()
        h, g = head.h, self.px(8)
        wide = self.help_fonts()['btn'].size(self.help_source()[3][0] + '      ')[0]
        small = [pygame.Rect(head.right - (4 - i) * (h + g) + g, head.y, h, h) for i in range(4)]
        third = (foot.w - 2 * g) // 3
        return [(pygame.Rect(head.x, head.y, wide, h), '≡'), (small[0], 'A-'), (small[1], 'A+'),
                (small[2], 'RU' if self.lang == 'en' else 'EN'), (small[3], 'X'),
                (pygame.Rect(foot.x, foot.y, third, h), '<'), (pygame.Rect(foot.right - third, foot.y, third, h), '>')]

    def help_pages(self):
        """The layout of the current language and size (cached); its pages, page 0 being the contents."""
        if getattr(self, '_help_src', None) != (self.lang, self.size):
            items, names, questions = self.help_source()[:3]
            _, body, _ = self.help_frame()
            pad = self.help_fonts()['k'].size(' ')[0] * 2
            self._layout = Layout(items, self.help_fonts(), body.w - 2 * pad, body.h, names, questions)
            self._help_src = (self.lang, self.size)
        return self._layout.pages

    def help_do(self, name):
        if name == 'X': self.help = None
        elif name == '≡': self.help = 0
        elif name in ('A-', 'A+'):
            page = self.help_pages()[self.help]
            src = page[0][4] if page else None                # stay at the text that was being read
            self.size = max(-2, min(5, self.size + (1 if name == 'A+' else -1)))
            self.help_save(help_size=self.size)
            pages = self.help_pages()
            self.help = 0 if src is None else next(k for k, pg in enumerate(pages) if any(ln[4] >= src for ln in pg))
        elif name in ('EN', 'RU'):
            self.lang = name.lower(); self.help_save(help_lang=self.lang)
            self.help = min(self.help, len(self.help_pages()) - 1)
        else: self.help = max(0, min(len(self.help_pages()) - 1, self.help + (1 if name == '>' else -1)))

    def help_tap(self, pos):
        for r, name in self.help_bar():
            if r.collidepoint(pos) and not (name == '≡' and self.help == 0): self.help_do(name)
        if self.help == 0:
            for r, _, page, _ in self.toc_rows():
                if r.collidepoint(pos): self.help = page

    def toc_rows(self):
        """The contents: (rect, chapter, page, the group's title or None), in groups - the rules, the games, the quick
        reference; the rows close up when the text is large."""
        self.help_pages()
        _, body, _ = self.help_frame()
        toc, f, titles = self._layout.toc, self.help_fonts(), self.help_source()[3][1:]
        n = len(toc) + 1.5 * len({g for _, _, g in toc})       # a group: its title and a little gap
        step = min(int(f['b'].get_linesize() * 1.9), int(body.h / n))
        rows, y, group = [], body.y, None
        for title, page, g in toc:
            first = g != group
            if first:
                y += step // 2 * (group is not None) + step
                group = g
            rows.append((pygame.Rect(body.x, y, body.w, step - max(2, step // 7)), title, page, titles[g] if first else None))
            y += step
        return rows

    def draw_button(self, sc, r, label):
        pygame.draw.rect(sc, BLUE, r, border_radius=self.px(8))
        f = self.help_fonts()['h' if len(label) == 1 else 'btn']          # a lone sign: larger
        img = f.render(label, True, (245, 245, 245))
        sc.blit(img, img.get_rect(center=r.center))

    def draw_help(self):
        sc, f = self.screen, self.help_fonts()
        pages = self.help_pages()
        head, body, foot = self.help_frame()
        sc.fill(PAPER)
        contents = self.help_source()[3][0]
        if self.help == 0:
            for r, title, page, group in self.toc_rows():
                if group:
                    img = f['k'].render(group.upper(), True, GREY)
                    sc.blit(img, (r.x + self.px(4), r.y - img.get_height() - self.px(5)))
                pygame.draw.rect(sc, TILE, r, border_radius=self.px(8))
                img = f['b'].render(title, True, BLUE)
                sc.blit(img, (r.x + self.px(12), r.centery - img.get_height() // 2))
                img = f['h'].render('›', True, GREY)
                sc.blit(img, (r.right - img.get_width() - self.px(12), r.centery - img.get_height() // 2))
        else:
            pad = f['k'].size(' ')[0] * 2
            self._layout.draw(sc, self.help, body.x + pad, body.y)
        for r, name in self.help_bar():
            if name == '≡':
                if self.help == 0:
                    img = f['h'].render(contents, True, INK)
                    sc.blit(img, (r.x, r.centery - img.get_height() // 2))
                else:
                    self.draw_button(sc, r, '≡  ' + contents)
            else:
                self.draw_button(sc, r, {'A-': 'A−', 'X': '×', '<': '‹', '>': '›'}.get(name, name))
        pygame.draw.line(sc, RULE, (head.x, head.bottom + head.h // 4), (head.right, head.bottom + head.h // 4))
        pygame.draw.line(sc, RULE, (foot.x, foot.top - foot.h // 4), (foot.right, foot.top - foot.h // 4))
        note = '%d / %d' % (self.help + 1, len(pages))
        img = f['btn'].render(note, True, GREY)
        sc.blit(img, img.get_rect(center=foot.center))
        extra = '   '.join(['Electronic Detective ' + self.help_source()[4]] + [
            '%s %.1f s' % (n, self.timing[n]) for n in ('deal', 'par') if self.timing.get(n)])
        img = f['k'].render(extra, True, GREY)
        sc.blit(img, img.get_rect(midtop=(foot.centerx, foot.bottom + self.px(4))))
        pygame.display.flip()
