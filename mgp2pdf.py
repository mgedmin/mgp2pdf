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
    """Parse a named color or '#rgb'/'#rrggbb'

        >>> parse_color('#3366cc')
        Color(.2,.4,.8,1)
        >>> parse_color('#c96')
        Color(.8,.6,.4,1)

    The only hardcoded named colors are black and white:

        >>> parse_color('black')
        Color(0,0,0,1)
        >>> parse_color('white')
        Color(1,1,1,1)

    """
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
    """Presentation page builder.

    A presentation page consists of a number of lines that contain
    text and other objects (e.g. images), collectively called "chunks"
    for lack of a better name.

    There's also a set of methods for building the slides incrementally.
    """

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
        """Change the slide area.

        ``w`` and ``h`` specify the horizontal and vertical percentage
        (0 < w, h <= 100).
        """
        self.area = (w, h)

    def setFont(self, font):
        """Change the font for future text additions."""
        self.font = font

    def setSize(self, size):
        """Change the font size for future text additions.

        Units are expressed in percent of the slide area.
        """
        self.size = size

    def setVGap(self, vgap):
        """Change the extra vertical gap between lines for future text additions.

        Units are expressed in percent of the font size.
        """
        self.vgap = vgap

    def setColor(self, color):
        """Change the text color for future text additons."""
        self.color = parse_color(color)

    def setAlignment(self, alignment):
        """Change the alignment of the current and subsequent lines."""
        self.alignment = alignment
        if self._cur_line is not None:
            self._cur_line.alignment = alignment

    def setPrefix(self, prefix):
        """Change the prefix for the current and subsequent lines.

        The prefix is basically indentation, indicated as percentage
        of the slide area width.

        TODO: MagicPoint also supports string prefixes, but we don't
        support that yet.  Actually we don't support non-zero numeric
        prefixes either.
        """
        self.prefix = prefix
        if self._cur_line is not None:
            # XXX: not sure how mgp handles prefix changes in the middle of a
            # line
            self._cur_line.prefix = prefix

    def currentOrNewLine(self):
        """Return the line that will be the target of subsequent additions."""
        if self._cur_line is None:
            self._cur_line = Line(self.alignment, self.prefix)
            self.lines.append(self._cur_line)
        return self._cur_line

    def closeCurrentLine(self):
        """Close the current line for additions.

        Makes ``currentOrNewLine()`` return a new empty line.

        Can be undone by ``reopenCurrentLine()``.
        """
        self._cur_line = None

    def reopenCurrentLine(self):
        """Indicate that subsequent additions should continue the last line.

        (By default they'll start new lines.)
        """
        if self.lines and self._cur_line is None:
            self._cur_line = self.lines[-1]

    def addText(self, text):
        """Add a new line containing some text."""
        line = self.currentOrNewLine()
        line.add(TextChunk(text, self.font, self.size, self.vgap, self.color))
        self.closeCurrentLine()

    def addImage(self, filename, zoom=100, raised_by=0):
        """Add an image to the current line.

        ``zoom`` is a percentage (100 meaning no scaling).  This assumes
        that one image pixel represents one point, i.e. the image is
        assumed to be 72 dpi.

        XXX: shouldn't setArea() influence the image size?

        ``raised_by`` is a baseline adjustment, in points.

        XXX: should it be in points?
        """
        line = self.currentOrNewLine()
        line.add(Image(filename, zoom, raised_by))
        # XXX: self.closeCurrentLine()?

    def addMark(self):
        """Add a mark to the current line and return it.

        This mark is can be latter passed to ``addAgain()`` to move
        the drawing position back and overdraw some text or overlay
        an image.
        """
        line = self.currentOrNewLine()
        mark = Mark()
        line.add(mark)
        return mark

    def addAgain(self, mark):
        """Indicate that the subsequent drawing should occur at ``mark``."""
        line = self.currentOrNewLine()
        line.add(Again(mark))

    def __str__(self):
        """Represent the contents of the slide as text."""
        return '\n'.join(map(str, self.lines))

    def wordWrap(self, canvas, w, h):
        """Perform word-wrapping.

        ``canvas`` is the ReportLab drawing canvas.  It can be useful
        for calculating text extents and such.

        ``w`` and ``h`` specify the available space in points.

        Splits each object in ``self.lines`` into two or more bits,
        if it doesn't fit horizontally.

        Vertical overflow is ignored.
        """
        new_lines = []
        for line in self.lines:
            new_lines += line.split(canvas, w, h)
        self.lines = new_lines

    def drawOn(self, canvas, pageSize):
        """Draw the current slide on a ReportLab canvas.

        ``pageSize`` is a tuple (width, height), in points.

        The slide is centered on the page, occupying a certain
        percentage of it, as specified via ``setArea()``.
        """
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
    """Left alignment."""

    @staticmethod
    def align(textwidth, boxwidth):
        """Compute the position of text inside a given box width."""
        return 0


class Right(object):
    """Right alignment."""

    @staticmethod
    def align(textwidth, boxwidth):
        """Compute the position of text inside a given box width."""
        return boxwidth - textwidth


class Center(object):
    """Center alignment."""

    @staticmethod
    def align(textwidth, boxwidth):
        """Compute the position of text inside a given box width."""
        return (boxwidth - textwidth) / 2


class Line(object):
    """A line of text (and images)."""

    def __init__(self, alignment=Left, prefix=0):
        self.chunks = []
        self.alignment = alignment
        self.prefix = 0
        # XXX: we're ignoring the `prefix` argument!
        # XXX prefix can be a string (usually of whitespace), but that is not
        # yet implemented in size(), split() nor drawOn().

    def cloneStyle(self, newchunks):
        """Create a new Line with the same style but different contents."""
        clone = Line(self.alignment, self.prefix)
        clone.chunks = newchunks
        return clone

    def add(self, chunk):
        """Add a drawable object to this line."""
        self.chunks.append(chunk)

    def size(self, canvas, w, h):
        """Compute the size of this line.

        ``canvas`` is the ReportLab drawing canvas.  It can be useful
        for calculating text extents and such.

        ``w`` and ``h`` specify the slide area space in points.

        Returns (width, height), in points.
        """
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
        """Perform word-wrapping if necessary.

        ``canvas`` is the ReportLab drawing canvas.  It can be useful
        for calculating text extents and such.

        ``w`` and ``h`` specify the slide area space in points.

        Returns a list of Line objects that are supposed to fit inside
        the requested width.
        """
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
        """Render the line.

        ``canvas`` is the ReportLab drawing canvas.

        ``w`` and ``h`` specify the slide area space in points.

        ``x`` and ``y`` specify the origin point for this line.

        Returns (x, y) specifying the origin point for the next line.

        (Reminder: the PDF coordinate space is in points and starts in
        the lower left corner of the page.)
        """
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
        """Represent the contents of the line as text."""
        return ''.join(map(str, self.chunks))


class SimpleChunk(object):
    """A simple chunk that takes no space, is invisible, and unsplittable."""

    def size(self, canvas, w, h):
        """Compute the size of this chunk.

        ``canvas`` is the ReportLab drawing canvas.  It can be useful
        for calculating text extents and such.

        ``w`` and ``h`` specify the slide area space in points.  It
        needs to be passed because so many parameters in MagicPoint
        are relative to the slide area size.
        """
        return 0, 0

    def drawOn(self, canvas, x, y, w, h):
        """Render the chunk on canvas.

        ``canvas`` is the ReportLab drawing canvas.

        ``w`` and ``h`` specify the slide area space in points.  It
        needs to be passed because so many parameters in MagicPoint
        are relative to the slide area size.

        ``x`` and ``y`` specify the origin point for this chunk.

        Returns (x, y) specifying the origin point for the next chunk.
        """
        return x, y

    def split(self, canvas, w, h, maxw):
        """Perform word-wrapping if necessary.

        ``canvas`` is the ReportLab drawing canvas.  It can be useful
        for calculating text extents and such.

        ``w`` and ``h`` specify the slide area space in points.

        ``maxw`` specifies the remaining space available on this line

        Returns a list of chunk objects, the first of which is supposed
        to fit inside the requested width.
        """
        return [self]

    def __str__(self):
        """Represent the contents of the chunk as text."""
        return '<%s>' % self.__class__.__name__


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
        try:
            canvas.drawImage(self.filename, x, y - myh + self.raised_by, myw, myh,
                             mask='auto')
        except Exception:
            log.debug("Exception in canvas.drawImage:", exc_info=True)
            log.warning("Could not render image %s", self.filename)

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

    def __init__(self, file=None, title=None, unsafe=False):
        self.defaultDirectives = {}
        self.fonts = Fonts()
        self.slides = []
        self._directives_used_in_this_line = set()
        self.title = title
        self.unsafe = unsafe
        self.basedir = ''
        self.lineno = None
        if file:
            self.load(file)

    def load(self, file, basedir=''):
        """Parse an .mgp file.

        ``file`` can be a filename or a file-like object.
        """
        self.basedir = basedir
        if not hasattr(file, 'read'):
            if not self.basedir:
                self.basedir = os.path.dirname(file)
            file = open(file)
        for lineno, line in self.preprocess(file):
            self.lineno = lineno
            if line.startswith(('#', '%%')):
                pass
            elif line.startswith('%'):
                self._handleDirectives(line)
            else:
                self._handleText(line)
        self.lineno = None

    def preprocess(self, file):
        """Handle %filter directives in the source file.

        ``file`` is a file-like object.

        Returns a generator that yields (lineno, line) with preprocessed lines
        and line numbers in the original file.

        Finds ``%filter`` and ``%endfilter`` directives and pipes the text
        between them through the external command specified (if self.unsafe
        is True) OR emits a warning and replaces the text with an error
        message (if self.unsafe is False).

        Can raise MgpSyntaxError if the directives are unbalanced or
        ill-formed.
        """
        filter_cmd = None
        filter_lineno = None
        data_to_filter = []
        for lineno, line in enumerate(file, 1):
            if line.startswith('%filter'):
                if filter_cmd is not None:
                    raise MgpSyntaxError(
                        'Cannot nest %filter directives (line {0}, previous'
                        ' %filter on line {1}), did you forget %endfilter?'
                        .format(lineno, filter_lineno))
                filter_cmd = line[len('%filter'):].strip()
                if not filter_cmd.startswith('"') or not filter_cmd.endswith('"'):
                    raise MgpSyntaxError("%filter directive expects a quoted string")
                filter_cmd = filter_cmd[1:-1]
                filter_lineno = lineno
                data_to_filter = []
            elif line.startswith('%endfilter'):
                if not filter_cmd:
                    raise MgpSyntaxError('%endfilter on line {0} without matching %filter'.format(lineno))
                if self.unsafe:
                    child = subprocess.Popen(filter_cmd, shell=True,
                                             cwd=self.basedir,
                                             stdin=subprocess.PIPE,
                                             stdout=subprocess.PIPE)
                    output = child.communicate(''.join(data_to_filter))[0]
                else:
                    log.warning("Ignoring %filter directive on line {0} in safe mode".format(filter_lineno))
                    output = 'Filtering through "%s" disabled, use --unsafe to enable\n' % filter_cmd
                for line in output.splitlines(True):
                    yield filter_lineno, line
                filter_cmd = None
            elif filter_cmd:
                data_to_filter.append(line)
            else:
                yield lineno, line
        if filter_cmd is not None:
            raise MgpSyntaxError(
                'Missing %endfilter at end of file (%filter on line {0})'
                .format(filter_lineno))

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
        """Handle a directive line

        The line starts with '%' and contains a number of comma-separated
        MagicPoint directives with arguments.
        """
        line = line[1:].strip()
        parts = self._splitDirectives(line)
        if parts[0].startswith('default'):
            # "%default <n>" is a special prefix that consumes all the other
            # directives on this line.  It means "for the rest of the file,
            # pretend that all the directives specified here show up on
            # line <n> in each slide" (unless %nodefault is used for that
            # slide, of course).
            args = self._splitArgs(parts[0])
            n = int(args[1])
            parts[0] = ' '.join(args[2:])
            self.defaultDirectives[n] = parts
        else:
            for part in parts:
                self._handleDirective(part.strip())

    def _handleDirective(self, directive):
        """Handle a single directive with arguments."""
        parts = self._splitArgs(directive)
        if not parts:
            # Huh, an empty directive.  We end up here if we encounter
            # something like "%foo, , bar".  This should probably abort
            # with a syntax error or something.
            log.debug("Ignoring empty directive on line {0}".format(self.lineno))
            return
        word = parts[0]
        self._directives_used_in_this_line.add(word)
        handler = getattr(self, '_handleDirective_%s' % word,
                          self._handleUnknownDirective)
        handler(parts)

    def inPreamble(self):
        return len(self.slides) == 0

    def _handleDirective_page(self, parts):
        """Handle %page.

        Starts a new slide.
        """
        self.slides.append(Slide())
        self._lastlineno = 0
        self._use_defaults = True
        self._continuing = False
        self._directives_used_in_this_line = set()
        self.mark = None

    def _handleDirective_nodefault(self, parts):
        """Handle %nodefault.

        Suppresses the application of %default rules for this page.
        """
        self._use_defaults = False

    def _handleDirective_area(self, parts):
        """Handle %area <w> <h>.

        Specifies the usable slide area in percent.
        """
        w, h = self._parseArgs(parts, "nn")
        self.slides[-1].setArea(w, h)

    def _handleDirective_deffont(self, parts):
        """Handle %deffont "<name>" <engine> "<font-name>".

        Defines a named font, to be used with %font <name>.
        """
        # XXX this is not entirely correct
        name, engine, enginefont = self._parseArgs(parts, "sws")
        self.fonts.define(name, engine, enginefont)

    def _handleDirective_font(self, parts):
        """Handle %font <name>.

        Selects the named font (previously defined with %deffont) for
        text.
        """
        name, = self._parseArgs(parts, "s")
        self.slides[-1].setFont(name)

    def _handleDirective_prefix(self, parts):
        """Handle %prefix <prefix>.

        Specifies left indentation (in percent of the slide area size) or a
        string to be prepended to each line of text.
        """
        prefix, = self._parseArgs(parts, "S")
        self.slides[-1].setPrefix(prefix)

    def _handleDirective_size(self, parts):
        """Handle %size <font-size>.

        Specifies font size (as percent of the slide area height).
        """
        size, = self._parseArgs(parts, "n")
        self.slides[-1].setSize(size)

    def _handleDirective_vgap(self, parts):
        """Handle %vgap <percent>.

        Specifies extra line spacing, as percentage of the font size.
        """
        vgap, = self._parseArgs(parts, "n")
        self.slides[-1].setVGap(vgap)

    def _handleDirective_fore(self, parts):
        """Handle %fore "<color>".

        Specifies text color.
        """
        color, = self._parseArgs(parts, "s")
        self.slides[-1].setColor(color)

    def _handleDirective_left(self, parts):
        """Handle %left.

        Specifies left-adjustment.
        """
        self.slides[-1].setAlignment(Left)
        self._directives_used_in_this_line.add('right')
        self._directives_used_in_this_line.add('center')

    def _handleDirective_right(self, parts):
        """Handle %right.

        Specifies right-adjustment.
        """
        self.slides[-1].setAlignment(Right)
        self._directives_used_in_this_line.add('left')
        self._directives_used_in_this_line.add('center')

    def _handleDirective_center(self, parts):
        """Handle %center.

        Specifies center-adjustment.
        """
        self.slides[-1].setAlignment(Center)
        self._directives_used_in_this_line.add('left')
        self._directives_used_in_this_line.add('right')

    def _handleDirective_cont(self, parts):
        """Handle %cont.

        Suppresses the line break.

        Example::

            %fore "#00cc00"
            Hello
            %fore "#cc0000"
            World

        would print a green "Hello" and a red "World" on two different lines,
        while ::

            %fore "#00cc00"
            Hello
            %fore "#cc0000", cont
            World

        would print them on the same line.
        """
        self.slides[-1].reopenCurrentLine()
        self._continuing = True

    def _handleDirective_newimage(self, parts):
        """Handle %newimage [-<flag> <value>] [...] "<filename>".

        Supported flags include:

            -zoom <percent>
            -raise <amount>

        """
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
        filename = os.path.join(self.basedir, args[-1])
        self.slides[-1].addImage(filename, zoom, raised_by)

    def _handleDirective_mark(self, parts):
        """Handle %mark.

        Puts an invisible marker on the line so you can go back and overdraw
        it.

        Example::

            %mark
            %left
            Left-aligned text
            %again
            %right
            Right-aligned text

        puts "Left-aligned text" and "Right-aligned text" on the same line.
        """
        self.mark = self.slides[-1].addMark()

    def _handleDirective_again(self, parts):
        """Handle %again.

        Moves back to the screen location of the last %mark.

        Example::

            %mark
            %left
            Left-aligned text
            %again
            %right
            Right-aligned text

        puts "Left-aligned text" and "Right-aligned text" on the same line.
        """
        if not self.mark:
            raise MgpSyntaxError("%again without %mark")
        self._handleText('')
        self.slides[-1].addAgain(self.mark)

    def _handleUnknownDirective(self, parts):
        """Handle an unrecognized directive."""
        directive = parts[0]
        if directive in ('pcache', 'ccolor', 'system', 'noop'):
            # These are meaningless for PDF or literal no-ops.
            return
        log.debug("Ignoring unrecognized directive %{0} on line {1}"
                  .format(directive, self.lineno))

    def _parseArgs(self, parts, argspec):
        """Validate and convert arguments into the desired data types.

        ``parts`` is a list of strings, as returned by ``_splitArgs()``.

        ``argspec`` is a string describing the type of each argument::

            'S': either a number or a quoted string
            's': a quoted string
            'n': a decimal number
            'w': a bare word

        """
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
            else: # pragma: nocover
                assert False, 'unknown argspec %r' % arg
        return tuple(results)

    def _handleText(self, line):
        """Handle a line of text that is not a comment or a directive."""
        if self.inPreamble():
            raise MgpSyntaxError('No text allowed in the preamble')
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
        """Represent the contents of the presentation as text."""
        res = []
        for n, s in enumerate(self.slides):
            res.append('--- Slide %d ---\n' % (n + 1))
            res.append(str(s) + '\n')
        return ''.join(res)

    def makePDF(self, outfile):
        """Render the presentation into a PDF.

        ``outfile`` can be a filename or a file-like object.
        """
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
        """Define a new font.

        ``name`` is the name that will be used for this font in the
        presentation text.

        ``engine`` is the font engine.  MagicPoint supports several,
        but mgp2pdf supports only "xfont".

        ``enginefontname`` is the name of the font according to the
        font engine.  For ``xfont`` it can be "family", "family-weight"
        or "family-weight-slant".  Or it can be a fontconfig pattern.
        """
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
            sys.exit('Could not find the font file for %s' % enginefontname)
        log.debug("Font %s: %s -> %s" % (name, enginefontname, filename))
        pdfmetrics.registerFont(TTFont(name, filename))
        pdfmetrics.getFont(name)  # just see if raises


def setUpLogging(verbose=False):
    root = logging.getLogger()
    root.addHandler(logging.StreamHandler(sys.stdout))
    root.setLevel(logging.DEBUG if verbose else logging.INFO)


def main(args=None):
    parser = optparse.OptionParser(usage='%prog [options] filename.mgp ...')
    parser.add_option('-v', action='store_true', dest='verbose', default=False,
                      help="print the presentation as text (debug)")
    parser.add_option('-o', action='store', dest='outfile',
                      help="output file name or directory (default: input file name with extension changed to .pdf)")
    parser.add_option('--unsafe', action='store_true', default=False,
                      help="enable %filter (security risk)")
    opts, args = parser.parse_args(args)
    if opts.outfile and len(args) > 1 and not os.path.isdir(opts.outfile):
        parser.error("%s must be a directory when you're converting multiple files" % opts.outfile)
    if not args:
        parser.error("nothing to do, try -h for help")
    setUpLogging(opts.verbose)
    for fn in args:
        log.debug("Loading %s", fn)
        try:
            title = os.path.splitext(os.path.basename(fn))[0]
            p = Presentation(fn, title, unsafe=opts.unsafe)
        except Exception as e:
            log.debug("Exception while parsing input file", exc_info=True)
            log.error("Error loading %s: %s: %s",
                      fn, e.__class__.__name__, e)
            continue
        if opts.verbose:
            print(p)
        try:
            outfile = os.path.splitext(fn)[0] + '.pdf'
            if opts.outfile:
                if os.path.isdir(opts.outfile):
                    outfile = os.path.join(opts.outfile, os.path.basename(outfile))
                else:
                    outfile = opts.outfile
            p.makePDF(outfile)
        except Exception as e:
            log.debug("Exception while rendering PDF", exc_info=True)
            log.error("Error generating %s: %s: %s",
                      outfile, e.__class__.__name__, e)


if __name__ == '__main__':
    main()
