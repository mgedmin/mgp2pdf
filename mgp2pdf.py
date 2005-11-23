#!/usr/bin/python
"""
A quick-and-dirty MagicPoint to PDF converter.
"""

import os

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch
from reportlab.lib.fonts import addMapping
from reportlab.lib.colors import HexColor, black
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas


Screen_1024x768_at_100_dpi = 1024 * inch / 100, 768 * inch / 100
Screen_1024x768_at_72_dpi = 1024 * inch / 72, 768 * inch / 72



class MgpSyntaxError(Exception):
    pass


def parse_color(color):
    color = {'black': '#000000'}.get(color, color)
    return HexColor(color)


class Slide(object):
    """Description of a slide."""

    def __init__(self):
        self.text = []
        self.font = 'Helvetica'
        self.size = 5
        self.vgap = 0
        self.area = (100, 100)
        self.color = black
        self.alignment = Left

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

    def addText(self, text):
        self.text.append(TextChunk(text, self.font, self.size, self.vgap,
                                   self.color, self.alignment))

    def addImage(self, filename, zoom):
        self.text.append(Image(filename, zoom, self.alignment))

    def __str__(self):
        return ''.join(map(str, self.text))

    def drawOn(self, canvas, pageSize):
        # canvas.bookmarkPage(title)
        # canvas.addOutlineEntry(title, title, outlineLevel)

        w = pageSize[0] * self.area[0] / 100
        h = pageSize[1] * self.area[1] / 100
        x = (pageSize[0] - w) / 2
        y = (pageSize[1] + h) / 2
        for p in self.text:
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


class Image(object):
    """An image."""

    def __init__(self, filename, zoom=100, alignment=Left):
        self.filename = filename
        self.zoom = zoom
        self.alignment = alignment

    def drawOn(self, canvas, x, y, w, h):
        return x, y


class TextChunk(object):
    """A chunk of text."""

    def __init__(self, text, font, size, vgap, color, alignment):
        self.text = text
        self.font = font
        self.size = size
        self.vgap = vgap
        self.color = color
        self.alignment = alignment

    def drawOn(self, canvas, x, y, w, h):
        fontSize = h * self.size / 100
        leading = fontSize * (100 + self.vgap) / 100
        txt = canvas.beginText(x, y - fontSize)
        txt.setFont(self.font, fontSize, leading)
        txt.setFillColor(self.color)
        for line in self.text.splitlines(True):
            if line.endswith('\n'):
                fn, arg = txt.textLine, line.rstrip()
            else:
                fn, arg = txt.textOut, line
            textwidth = canvas.stringWidth(arg, self.font, fontSize)
            xpos = self.alignment.align(textwidth, w)
            txt.setXPos(xpos)
            fn(arg)
            txt.setXPos(-xpos)
        canvas.drawText(txt)
        return txt.getX(), txt.getY() + fontSize

    def toParagraph(self):
        style = getParagraphStyles()['BodyText']
        return Paragraph('<font name="%s">%s</font>' % (self.font, self.text),
                         style)

    def __str__(self):
        return self.text


class Presentation(object):
    """Presentation."""

    pageSize = landscape(Screen_1024x768_at_72_dpi)

    def __init__(self, file=None):
        self.defaultDirectives = {}
        self.fonts = Fonts()
        self.slides = []
        if file:
            self.load(file)

    def load(self, file):
        if not hasattr(file, 'read'):
            file = open(file)
        for line in file:
            if line.startswith('%'):
                self._handleDirectives(line)
            elif line.startswith('#'):
                pass
            else:
                self._handleText(line)

    def _newPage(self):
        self.slides.append(Slide())
        self._lastlineno = 0
        self._use_defaults = True

    def _handleDirectives(self, line):
        line = line[1:].strip()
        parts = line.split(",")
        if parts[0].startswith('default'):
            n = int(parts[0].split()[1])
            parts[0] = ' '.join(parts[0].split()[2:])
            self.defaultDirectives[n] = parts
        else:
            for part in parts:
                self._handleDirective(part.strip())

    def _handleDirective(self, directive):
        parts = directive.split()
        word = parts[0]
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

    def _handleDirective_right(self, parts):
        self.slides[-1].setAlignment(Right)

    def _handleDirective_center(self, parts):
        self.slides[-1].setAlignment(Center)

    def _handleDirective_newimage(self, parts):
        n = (len(parts) - 1) / 2
        args = self._parseArgs(parts, "wn" * n + "s")
        zoom = 100
        for k, v in zip(args[:-1:2], args[1:-1:2]):
            if k == '-zoom':
                zoom = v
            else:
                raise MgpSyntaxError("newimage %s not handled yet" % k)
        self.slides[-1].addImage(args[-1], zoom)


    def _handleUnknownDirective(self, parts):
        pass

    def _parseArgs(self, parts, argspec):
        if len(parts) != 1 + len(argspec):
            raise MgpSyntaxError("%s directive expects %d args, got %d"
                                 % (parts[0], len(argspec), len(parts) - 1))
        results = []
        for n, (arg, part) in enumerate(zip(argspec, parts[1:])):
            if arg == 'w':
                results.append(part)
            elif arg == 'n':
                results.append(int(part))
            elif arg == 's':
                if not part.startswith('"') or not part.startswith('"'):
                    raise MgpSyntaxError("%s directive expects a quoted string as its %dth arg"
                                         % (parts[0], n+1))
                results.append(part[1:-1])
            else:
                assert False, 'unknown argspec %r' % arg
        return tuple(results)

    def _handleText(self, line):
        self._lastlineno += 1
        if self._use_defaults:
            for part in self.defaultDirectives.get(self._lastlineno, []):
                self._handleDirective(part)
        self.slides[-1].addText(line)

    def __str__(self):
        res = []
        for n, s in enumerate(self.slides):
            res.append('--- Slide %d ---\n' % (n+1))
            res.append(str(s) + '\n')
        return ''.join(res)

    def makePDF(self, outfile):
        canvas = Canvas(outfile, self.pageSize)
        # canvas.setTitle(...)
        # canvas.setAuthor(...)
        # canvas.setSubject(...)
        for n, s in enumerate(self.slides):
            s.drawOn(canvas, self.pageSize)
            canvas.showPage()
        canvas.save()


class Fonts(object):
    """Manages the fonts used in the presentation."""

    fontpath = '/usr/share/fonts/truetype/msttcorefonts/'

    def define(self, name, engine, enginefontname):
        if engine != "xfont":
            raise NotImplementedError("unsupported font engine %s" % engine)
        enginefontname = enginefontname.replace('-bold', 'b')
        enginefontname = enginefontname.replace('-medium-i', 'i')
        filename = os.path.join(self.fontpath, enginefontname + '.ttf')
        pdfmetrics.registerFont(TTFont(name, filename))
        font = pdfmetrics.getFont(name)


def main():
    p = Presentation('intro.mgp')
    p.makePDF('intro.pdf')


if __name__ == '__main__':
    main()
