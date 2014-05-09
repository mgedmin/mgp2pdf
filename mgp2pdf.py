#!/usr/bin/python
"""
A quick-and-dirty MagicPoint to PDF converter.
"""

import os
import re
import sys
import optparse
import subprocess
import logging

from reportlab.lib.pagesizes import landscape
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas


log = logging.getLogger('mgp2pdf')


Screen_1024x768_at_100_dpi = 1024 * inch / 100, 768 * inch / 100
Screen_1024x768_at_72_dpi = 1024 * inch / 72, 768 * inch / 72


class MgpSyntaxError(Exception):
    pass


def parse_color(color):
    color = {'black': '#000000', 'white': '#ffffff'}.get(color, color)
    if len(color) == 4 and color.startswith('#'):
        r, g, b = color[1:]
        color = '#' + r + r + g + g + b + b
    return HexColor(color)


def textWrapPositions(s):
    """Find all break points in text, starting from the rightmost.

        >>> textWrapPositions('well hello world')
        [16, 10, 4]
        >>> textWrapPositions('a  good  day')
        [12, 7, 1]
        >>> textWrapPositions(u'neangli\u0161kas tekstas'.encode('UTF-8'))
        [20, 12]

    """
    poses = [len(s)]
    for idx in range(len(s) - 1, 0, -1):
        if not s[idx - 1].isspace() and s[idx].isspace():
            poses.append(idx)
    return poses


class Slide(object):
    """Description of a slide."""

    def __init__(self):
        self.lines = []
        self._cur_line = None
        self.font = 'Helvetica'
        self.size = 5
        self.vgap = 0
        self.area = (100, 100)
        self.color = black
        self.alignment = Left
        self.prefix = 0

    def setArea(self, w, h):
        self.area = (w, h)

    def setFont(self, font):
        self.font = font

    def setSize(self, size):
        self.size = size

    def setVGap(self, vgap):
        self.vgap = vgap

    def setColor(self, color):
        self.color = parse_color(color)

    def setAlignment(self, alignment):
        self.alignment = alignment
        if self._cur_line is not None:
            self._cur_line.alignment = alignment

    def setPrefix(self, prefix):
        self.prefix = prefix
        if self._cur_line is not None:
            # XXX: not sure how mgp handles prefix changes in the middle of a
            # line
            self._cur_line.prefix = prefix

    def currentOrNewLine(self):
        if self._cur_line is None:
            self._cur_line = Line(self.alignment, self.prefix)
            self.lines.append(self._cur_line)
        return self._cur_line

    def closeCurrentLine(self):
        self._cur_line = None

    def reopenCurrentLine(self):
        if self.lines and self._cur_line is None:
            self._cur_line = self.lines[-1]
            return True
        else:
            return False

    def addText(self, text):
        line = self.currentOrNewLine()
        line.add(TextChunk(text, self.font, self.size, self.vgap, self.color))
        self.closeCurrentLine()

    def addImage(self, filename, zoom=100, raised_by=0):
        line = self.currentOrNewLine()
        line.add(Image(filename, zoom, raised_by))

    def addMark(self):
        line = self.currentOrNewLine()
        mark = Mark()
        line.add(mark)
        return mark

    def addAgain(self, mark):
        line = self.currentOrNewLine()
        line.add(Again(mark))

    def __str__(self):
        return '\n'.join(map(str, self.lines))

    def wordWrap(self, canvas, w, h):
        new_lines = []
        for line in self.lines:
            new_lines += line.split(canvas, w, h)
        self.lines = new_lines

    def drawOn(self, canvas, pageSize):
        # canvas.bookmarkPage(title)
        # canvas.addOutlineEntry(title, title, outlineLevel)
        w = pageSize[0] * self.area[0] / 100
        h = pageSize[1] * self.area[1] / 100
        x = (pageSize[0] - w) / 2
        y = (pageSize[1] + h) / 2
        self.wordWrap(canvas, w, h)
        for p in self.lines:
            x, y = p.drawOn(canvas, x, y, w, h)


class Left(object):
    @staticmethod
    def align(textwidth, boxwidth):
        return 0


class Right(object):
    @staticmethod
    def align(textwidth, boxwidth):
        return boxwidth - textwidth


class Center(object):
    @staticmethod
    def align(textwidth, boxwidth):
        return (boxwidth - textwidth) / 2


class Line(object):
    """A line of text (and images)."""

    def __init__(self, alignment=Left, prefix=0):
        self.chunks = []
        self.alignment = alignment
        self.prefix = 0
        # XXX prefix can be a string (usually of whitespace), but that is not
        # yet implemented in size(), split() nor drawOn().

    def cloneStyle(self, newchunks):
        clone = Line(self.alignment, self.prefix)
        clone.chunks = newchunks
        return clone

    def add(self, chunk):
        self.chunks.append(chunk)

    def size(self, canvas, w, h):
        myw = myh = 0
        seen_text = False
        if isinstance(self.prefix, int):
            w = w * (100 - self.prefix) / 100
        for chunk in self.chunks:
            cw, ch = chunk.size(canvas, w, h)
            if isinstance(chunk, TextChunk):
                if chunk is not self.chunks[-1]:
                    seen_text = True
                elif not seen_text and not chunk.text and len(self.chunks) > 1:
                    # MagicPoint weirdness: if a line only has images and no
                    # text, and nothing more, then the text size is not
                    # considered when calculating line height, but the vgap is
                    # computed in the usual fashion.
                    ch -= h * chunk.fontSize / 100
            myw += cw
            myh = max(myh, ch)
        myh += 1 # Another MagicPoint oddity
        return myw, myh

    def split(self, canvas, w, h):
        chunks_that_fit = []
        remaining_chunks = list(self.chunks)
        remaining_space = w
        if isinstance(self.prefix, int):
            w = w * (100 - self.prefix) / 100
        while remaining_chunks:
            chunk = remaining_chunks.pop(0)
            cw, ch = chunk.size(canvas, w, h)
            if cw <= remaining_space:
                chunks_that_fit.append(chunk)
                remaining_space -= cw
            else:
                bits = chunk.split(canvas, w, h, remaining_space)
                cw, ch = bits[0].size(canvas, w, h)
                if cw <= remaining_space:
                    chunks_that_fit.append(bits.pop(0))
                remaining_chunks = bits + remaining_chunks
                break
        if not chunks_that_fit and remaining_chunks:
            chunks_that_fit.append(remaining_chunks.pop(0))
        if remaining_chunks:
            return ([self.cloneStyle(chunks_that_fit)] +
                    self.cloneStyle(remaining_chunks).split(canvas, w, h))
        else:
            return [self]

    def drawOn(self, canvas, x, y, w, h):
        x0, y0 = x, y
        myw, myh = self.size(canvas, w, h)
        if isinstance(self.prefix, int):
            x += w * self.prefix / 100
            x0 += w * self.prefix / 100
            w = w * (100 - self.prefix) / 100
        x += self.alignment.align(myw, w)
        for chunk in self.chunks:
            x, y = chunk.drawOn(canvas, x, y, w, h)
            if isinstance(chunk, Again): # XXX breaks OOP and is fugly hack
                y0 = y
        return x0, y0 - myh

    def __str__(self):
        return ''.join(map(str, self.chunks))


class SimpleChunk(object):
    """A simple chunk that takes no space, is invisible, and unsplittable."""

    def size(self, canvas, w, h):
        return 0, 0

    def drawOn(self, canvas, x, y, w, h):
        return x, y

    def split(self, canvas, w, h, maxw):
        return [self]


class Mark(SimpleChunk):
    """A position marker."""

    def __init__(self):
        self.pos = None

    def drawOn(self, canvas, x, y, w, h):
        self.pos = x, y
        return x, y

    def __str__(self):
        return '<mark>'


class Again(SimpleChunk):
    """Move to a position marker."""

    def __init__(self, mark):
        self.mark = mark

    def drawOn(self, canvas, x, y, w, h):
        assert self.mark.pos is not None, "Mark not initialized yet!"
        mx, my = self.mark.pos
        return x, my

    def __str__(self):
        return '<again>'


class Image(SimpleChunk):
    """An image."""

    def __init__(self, filename, zoom=100, raised_by=0):
        self.filename = filename
        self.zoom = zoom
        self.raised_by = 0
        self.image = ImageReader(filename)

    def size(self, canvas, w, h):
        myw, myh = self.image.getSize()
        myw = myw * self.zoom / 100
        myh = myh * self.zoom / 100
        return myw, myh

    def drawOn(self, canvas, x, y, w, h):
        myw, myh = self.size(canvas, w, h)
        canvas.drawImage(self.filename, x, y - myh + self.raised_by, myw, myh,
                         mask='auto')
        return x + myw, y

    def __str__(self):
        return '[%s]' % self.filename


class TextChunk(object):
    """A chunk of text."""

    def __init__(self, text, font, fontSize, vgap, color):
        self.text = text
        self.font = font
        self.fontSize = fontSize
        self.vgap = vgap
        self.color = color

    def cloneStyle(self, newtext):
        return TextChunk(newtext, self.font, self.fontSize, self.vgap,
                         self.color)

    def _splitIntoRuns(self, text=None):
        if text is None:
            text = self.text
        return map(None, re.split('(\t)', text))

    def _calcSizes(self, w, h):
        fontSize = h * self.fontSize / 100
        leading = fontSize * (100 + self.vgap) / 100
        tabsize = fontSize * 2
        return fontSize, leading, tabsize

    def size(self, canvas, w, h, text=None):
        fontSize, leading, tabsize = self._calcSizes(w, h)
        textwidth = 0
        for run in self._splitIntoRuns(text):
            if run == '\t':
                textwidth = textwidth + tabsize - textwidth % tabsize
            else:
                textwidth += canvas.stringWidth(run, self.font, fontSize)
        return textwidth, leading

    def drawOn(self, canvas, x, y, w, h):
        fontSize, leading, tabsize = self._calcSizes(w, h)
        x0 = x
        for run in self._splitIntoRuns():
            if run == '\t':
                curpos = x - x0
                newpos = curpos + tabsize - curpos % tabsize
                x = x0 + newpos
            else:
                txt = canvas.beginText(x, y - fontSize)
                txt.setFont(self.font, fontSize, leading)
                txt.setFillColor(self.color)
                txt.textOut(run)
                canvas.drawText(txt)
                x = txt.getX()
        return x, y

    def split(self, canvas, w, h, maxw):
        for pos in textWrapPositions(self.text):
            myw = self.size(canvas, w, h, self.text[:pos])[0]
            if myw <= maxw:
                return [self.cloneStyle(self.text[:pos]),
                        self.cloneStyle(self.text[pos:].lstrip())]
        if pos < len(self.text):
            # well, it still sticks out, but a bit less
            return [self.cloneStyle(self.text[:pos]),
                    self.cloneStyle(self.text[pos:].lstrip())]
        return [self]

    def __str__(self):
        return self.text


class Presentation(object):
    """Presentation."""

    pageSize = landscape(Screen_1024x768_at_72_dpi)

    def __init__(self, file=None, title=None):
        self.defaultDirectives = {}
        self.fonts = Fonts()
        self.slides = []
        self._directives_used_in_this_line = set()
        self.title = title
        if file:
            self.load(file)

    def load(self, file):
        if not hasattr(file, 'read'):
            file = open(file)
        for line in self.preprocess(file):
            if line.startswith('%'):
                self._handleDirectives(line)
            elif line.startswith('#'):
                pass
            else:
                self._handleText(line)

    def preprocess(self, file):
        filter_cmd = None
        data_to_filter = []
        for line in file:
            if line.startswith('%filter'):
                filter_cmd = line[len('%filter'):].strip()
                if not filter_cmd.startswith('"') or not filter_cmd.startswith('"'):
                    raise MgpSyntaxError("%filter directive expects a quoted string")
                filter_cmd = filter_cmd[1:-1]
                data_to_filter = []
            elif line.startswith('%endfilter'):
                if not filter_cmd:
                    raise MgpSyntaxError('%endfilter without matching %filter')
                # UNSAFE -- should have a cmdline option to turn this on
                child = subprocess.Popen(filter_cmd, shell=True,
                                         stdin=subprocess.PIPE,
                                         stdout=subprocess.PIPE)
                output = child.communicate(''.join(data_to_filter))[0]
                for line in output.splitlines(True):
                    yield line
                filter_cmd = None
            elif filter_cmd:
                data_to_filter.append(line)
            else:
                yield line

    def _newPage(self):
        self.slides.append(Slide())
        self._lastlineno = 0
        self._use_defaults = True
        self._continuing = False
        self._directives_used_in_this_line = set()
        self.mark = None

    @staticmethod
    def _splitDirectives(line):
        """
            >>> Presentation._splitDirectives('foo, bar 42, baz "q, q", wumba')
            ['foo', 'bar 42', 'baz "q, q"', 'wumba']

        """
        return [s.strip() for s in re.findall('(?:[^,"]|"[^"]*")+', line)]

    @staticmethod
    def _splitArgs(line):
        """
            >>> Presentation._splitArgs('baz 42 "q w" e -foo 11')
            ['baz', '42', '"q w"', 'e', '-foo', '11']

        """
        return [s.strip() for s in re.findall('(?:[^ "]|"[^"]*")+', line)]

    def _handleDirectives(self, line):
        line = line[1:].strip()
        parts = self._splitDirectives(line)
        if parts[0].startswith('default'):
            args = self._splitArgs(parts[0])
            n = int(args[1])
            parts[0] = ' '.join(args[2:])
            self.defaultDirectives[n] = parts
        else:
            for part in parts:
                self._handleDirective(part.strip())

    def _handleDirective(self, directive):
        parts = self._splitArgs(directive)
        if not parts:
            return # warn maybe
        word = parts[0]
        self._directives_used_in_this_line.add(word)
        handler = getattr(self, '_handleDirective_%s' % word,
                          self._handleUnknownDirective)
        handler(parts)

    def _handleDirective_page(self, parts):
        self._newPage()

    def _handleDirective_nodefault(self, parts):
        self._use_defaults = False

    def _handleDirective_area(self, parts):
        w, h = self._parseArgs(parts, "nn")
        self.slides[-1].setArea(w, h)

    def _handleDirective_deffont(self, parts):
        # XXX this is not entirely correct
        name, engine, enginefont = self._parseArgs(parts, "sws")
        self.fonts.define(name, engine, enginefont)

    def _handleDirective_font(self, parts):
        name, = self._parseArgs(parts, "s")
        self.slides[-1].setFont(name)

    def _handleDirective_prefix(self, parts):
        prefix, = self._parseArgs(parts, "S")
        self.slides[-1].setPrefix(prefix)

    def _handleDirective_size(self, parts):
        size, = self._parseArgs(parts, "n")
        self.slides[-1].setSize(size)

    def _handleDirective_vgap(self, parts):
        vgap, = self._parseArgs(parts, "n")
        self.slides[-1].setVGap(vgap)

    def _handleDirective_fore(self, parts):
        color, = self._parseArgs(parts, "s")
        self.slides[-1].setColor(color)

    def _handleDirective_left(self, parts):
        self.slides[-1].setAlignment(Left)
        self._directives_used_in_this_line.add('right')
        self._directives_used_in_this_line.add('center')

    def _handleDirective_right(self, parts):
        self.slides[-1].setAlignment(Right)
        self._directives_used_in_this_line.add('left')
        self._directives_used_in_this_line.add('center')

    def _handleDirective_center(self, parts):
        self.slides[-1].setAlignment(Center)
        self._directives_used_in_this_line.add('left')
        self._directives_used_in_this_line.add('right')

    def _handleDirective_cont(self, parts):
        self.slides[-1].reopenCurrentLine()
        self._continuing = True

    def _handleDirective_newimage(self, parts):
        n = (len(parts) - 1) / 2
        args = self._parseArgs(parts, "wn" * n + "s")
        zoom = 100
        raised_by = 0
        for k, v in zip(args[:-1:2], args[1:-1:2]):
            if k == '-zoom':
                zoom = v
            elif k == '-raise':
                raised_by = v
            else:
                raise MgpSyntaxError("newimage %s not handled yet" % k)
        self.slides[-1].addImage(args[-1], zoom, raised_by)

    def _handleDirective_mark(self, parts):
        self.mark = self.slides[-1].addMark()

    def _handleDirective_again(self, parts):
        if not self.mark:
            raise MgpSyntaxError("%again without %mark")
        self._handleText('')
        self.slides[-1].addAgain(self.mark)

    def _handleUnknownDirective(self, parts):
        pass

    def _parseArgs(self, parts, argspec):
        if len(parts) != 1 + len(argspec):
            raise MgpSyntaxError("%s directive expects %d args, got %d"
                                 % (parts[0], len(argspec), len(parts) - 1))
        results = []
        for n, (arg, part) in enumerate(zip(argspec, parts[1:])):
            if arg == 'S': # either 'n' or 's'
                if part.isdigit():
                    arg = 'n'
                else:
                    arg = 's'
            if arg == 'w':
                results.append(part)
            elif arg == 'n':
                results.append(int(part))
            elif arg == 's':
                if not part.startswith('"') or not part.startswith('"'):
                    raise MgpSyntaxError("%s directive expects a quoted string as its %dth arg"
                                         % (parts[0], n + 1))
                results.append(part[1:-1])
            else:
                assert False, 'unknown argspec %r' % arg
        return tuple(results)

    def _handleText(self, line):
        if not self._continuing:
            self._lastlineno += 1
            if self._use_defaults:
                for part in self.defaultDirectives.get(self._lastlineno, []):
                    word = self._splitArgs(part)[0]
                    if word not in self._directives_used_in_this_line:
                        self._handleDirective(part)
        line = line.rstrip('\n').replace(r'\#', '#').replace(r'\\', '\\')
        self.slides[-1].addText(line)
        self._continuing = False
        self._directives_used_in_this_line = set()

    def __str__(self):
        res = []
        for n, s in enumerate(self.slides):
            res.append('--- Slide %d ---\n' % (n + 1))
            res.append(str(s) + '\n')
        return ''.join(res)

    def makePDF(self, outfile):
        canvas = Canvas(outfile, self.pageSize)
        if self.title:
            canvas.setTitle(self.title)
        # canvas.setAuthor(...)
        # canvas.setSubject(...)
        for n, s in enumerate(self.slides):
            s.drawOn(canvas, self.pageSize)
            canvas.showPage()
        canvas.save()


class Fonts(object):
    """Manages the fonts used in the presentation."""

    def define(self, name, engine, enginefontname):
        if engine != "xfont":
            raise NotImplementedError("unsupported font engine %s" % engine)
        if '-' in enginefontname and ':' not in enginefontname:
            if enginefontname.count('-') == 1:
                # family-weight
                family, weight = enginefontname.split('-')
                enginefontname = '%s:weight=%s' % (family, weight)
            elif enginefontname.count('-') == 2:
                # family-weight-slant
                family, weight, slant = enginefontname.split('-')
                slant = {'i': 'italic', 'm': 'roman'}[slant]
                enginefontname = '%s:weight=%s:slant=%s' % (family, weight, slant)
        filename = subprocess.Popen(
            ['fc-match', enginefontname, '-f', '%{file}'],
            stdout=subprocess.PIPE).communicate()[0].strip()
        if not filename:
            sys.exit('Could not find the font file for %s', enginefontname)
        log.debug("Font %s: %s -> %s" % (name, enginefontname, filename))
        pdfmetrics.registerFont(TTFont(name, filename))
        pdfmetrics.getFont(name)  # just see if raises


def setUpLogging(verbose=False):
    root = logging.getLogger()
    root.addHandler(logging.StreamHandler(sys.stdout))
    root.setLevel(logging.DEBUG if verbose else logging.INFO)


def main():
    parser = optparse.OptionParser()
    parser.add_option('-v', action='store_true', dest='verbose', default=False,
                      help="print the presentation as text (debug)")
    parser.add_option('-o', action='store', dest='outfile',
                      help="override output file name")
    try:
        opts, args = parser.parse_args(sys.argv[1:])
    except optparse.OptParseError, e:
        print >> sys.stderr, e
        sys.exit(1)
    if opts.outfile and len(args) > 1:
        print >> sys.stderr, "-o not allowed when there is more than one file"
        sys.exit(1)
    if not args:
        print >> sys.stderr, "nothing to do (try mgp2pdf -h for help)"
        sys.exit(1)
    setUpLogging(opts.verbose)
    for fn in args:
        title = os.path.splitext(os.path.basename(fn))[0]
        p = Presentation(fn, title)
        if opts.outfile:
            outfile = opts.outfile
        else:
            outfile = os.path.splitext(fn)[0] + '.pdf'
        p.makePDF(outfile)
        if opts.verbose:
            print p


if __name__ == '__main__':
    main()
