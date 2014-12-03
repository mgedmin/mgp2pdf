#!/usr/bin/env python
r"""
Produce a MagicPoint file from a text file with simple markup.

Markup:
    directives (lines starting with .)
    MagicPoint text (everything else)

You can use MagicPoint markup (lines starting with %), but that is discouraged.
You should know that \ is MagicPoint's escape character.  If you want to
include a literal \ in the text, write \\.  You should also know that lines
starting with a # are comments.  If you want to include a line starting with
a # in the output, write \#

Directives:
    .logo FILENAME (default: povlogo.png)
        logo image used on the title page and on all other pages
        should be specified before the first page directive

    .title TITLE
    .author AUTHOR
    .email <EMAIL>
    .conference CONFERENCE NAME YEAR
    .company COMPANY NAME (default: Programers of Vilnius)
    .url COMPANY URL (default: http://pov.lt)
    .logo FILENAME (default: povlogo.png)
        title page elements
        can be specified either before or inside the .titlepage directive

    .titlepage
        produce a title page
        you can use a different logo image for the title page if you
        specify .logo between the .titlepage directive and the next page
        directive.

    .heading TEXT
        define the header line to show at the top of the current page
    .footer TEXT
        define a footer line to show at bottom of the current page
    .subpage
        start a new page that is a copy of the old page with extra text added

    .page
        start a new page (first line of text is centered, second line right
        below it, rendered in italics; further lines horizontally centered,
        in a smaller font)
    .pageoftext
        start a new page for text examples (12 lines of text, left-aligned)
    .dictpage
        start a new page (5 lines of vertically centered text)
    .listpage
        start a new page (title, blank line, then up to 8 list items)

Blank lines following a directive are skipped.

makeslide.py was written by Marius Gedminas <marius@pov.lt>
"""

import sys
import string
import fileinput


#
# Tokenizer
#

class Token(object):
    def __init__(self, filename, lineno):
        self.filename = filename
        self.lineno = lineno

    def report_error(self, message):
        print >> sys.stderr, '%s:%d: %s' % (self.filename, self.lineno, message)

class Directive(Token):
    def __init__(self, filename, lineno, name, args):
        Token.__init__(self, filename, lineno)
        self.name = name
        self.args = args

class LineOfText(Token):
    def __init__(self, filename, lineno, text):
        Token.__init__(self, filename, lineno)
        self.text = text

class BlankLine(LineOfText):
    pass


def tokenize(inputfile):
    filename = getattr(inputfile, 'name', '<input>')
    for n, line in enumerate(inputfile, 1):
        line = line.rstrip('\n')
        if not line:
            yield BlankLine(filename, n, line)
            continue
        if line.startswith('.') and line[1:2].isalpha():
            args = line.split(None, 1)
            name = args.pop(0)[1:]
            yield Directive(filename, n, name, (args + [''])[0])
        else:
            yield LineOfText(filename, n, line)

#
# Parser
#

def parse(token_stream, variables, templates, preamble):
    variables = variables.copy()
    cur_page = preamble(variables)
    pages = [cur_page]
    skipping_empty_lines = True
    for token in token_stream:
        if isinstance(token, BlankLine) and skipping_empty_lines:
            continue
        elif isinstance(token, Directive):
            keyword = token.name
            if keyword in variables:
                variables[keyword] = token.args
            elif keyword in templates:
                variables = variables.copy()
                cur_page = templates[keyword](variables)
                pages.append(cur_page)
            elif keyword == 'subpage':
                if cur_page is None:
                    token.report_error(".subpage before first page ignored")
                else:
                    cur_page = cur_page.copy()
                    pages.append(cur_page)
                    variables = cur_page.variables
            else:
                token.report_error(".%s ignored" % keyword)
            skipping_empty_lines = True
        elif isinstance(token, LineOfText):
            skipping_empty_lines = False
            if cur_page is None:
                token.report_error("text before first page ignored")
            else:
                try:
                    cur_page.add_line(token.text)
                except NotImplementedError:
                    token.report_error("text ignored")
    return pages


#
# Compiler
#


def process(inputfile, outputfile, variables, templates, preamble):
    pages = parse(tokenize(inputfile), variables, templates, preamble)
    for page in pages:
        outputfile.write(page.render())


#
# Semantics
#

VARIABLES = dict(title='', author='', email='', conference='',
                 logo='povlogo.png',
                 company='Programmers of Vilnius',
                 url='http://pov.lt',
                 heading='', footer='')


TEMPLATES = {}


def template(name):
    def decorator(cls):
        TEMPLATES[name] = cls
        return cls
    return decorator


class PageTemplate(object):

    template = string.Template('$text')
    supports_text = True

    defaults = dict(
        pageoftextlogo='area 90 90, vgap 60,'
            ' size 8, font "standard", fore "#134d73", back "white", right,'
            ' newimage -zoom 50 "$logo", mark, again, center, size 4',
        default1='area 90 90, vgap 260,'
            ' size 8, font "standard", fore "#134d73", back "white", right,'
            ' newimage -zoom 50 "$logo", mark, again, center, size 4, vgap 520',
        default2='fore "#134d73"',
        default3='center, size 5, vgap 260',
        default4='size 8, vgap 80',
        default5='font "em", size 7, vgap 10',
        default6='font "standard", size 3',
        footer_impl='%again, size 950, center, vgap 10\n\n%size 4\n$footer\n',
    )

    variables_to_reset_for_each_page = dict(
        heading=' ',
        footer='',
    )

    def __init__(self, variables):
        self.variables = variables
        self.text = []
        self.variables.update(self.variables_to_reset_for_each_page)

    def copy(self):
        new = self.__class__({})
        new.variables = self.variables.copy()
        new.text = list(self.text)
        return new

    def add_line(self, text):
        if not self.supports_text and not text.startswith('#'):
            raise NotImplementedError
        self.text.append(text)

    def namespace(self):
        namespace = dict((k, string.Template(v).substitute(**self.variables))
                         for k, v in self.defaults.items())
        namespace.update(self.variables)
        namespace['text'] = ''.join(line + '\n' for line in self.text)
        for n, line in enumerate(self.text, 1):
            namespace['line%d' % n] = line
            namespace['rest%d' % n] = ''.join(line + '\n' for line in self.text[n:])
        for n in range(len(self.text) + 1, 20):
            namespace['line%d' % n] = ''
            namespace['rest%d' % n] = ''
        return namespace

    def render(self):
        return self.template.substitute(**self.namespace())


class Preamble(PageTemplate):
    supports_text = False
    template = string.Template('\n'.join([
        '#!/usr/bin/env mgp',
        '# Note: tabs and trailing spaces are *important* in this file',
        '# - Preamble ----------------------------------------------------------------',
        '%deffont "standard" xfont "verdana"',
        '%deffont "thick" xfont "verdana-bold"',
        '%deffont "em" xfont "verdana-medium-i"',
        '%deffont "mono" xfont "andale mono"',
        '%default 1 $default1',
        '%default 2 $default2',
        '%default 3 $default3',
        '%default 4 $default4',
        '%default 5 $default5',
        '%default 6 $default6',
        '# ---------------------------------------------------------------------------',
        '$text',
    ]))


@template('titlepage')
class TitlePage(PageTemplate):
    supports_text = False
    template = string.Template('\n'.join([
        '%page',
        '%pcache 1 1 0 1',
        '%ccolor "#134d73"',
        '%nodefault',
        '%size 7, font "standard", vgap 20, fore "black", back "white"',
        '',
        '',
        '%center, font "thick", size 11',
        '$title',
        '%center, font "standard", size 7',
        '',
        '',
        '%size 5, font "standard", fore "#134d73"',
        '$author',
        '%size 4',
        '$email',
        '%size 2',
        '',
        '%size 5',
        '$company',
        '%size 4',
        '$url',
        '%size 2',
        '',
        '%newimage "$logo"',
        '',
        '',
        '',
        '%fore "black"',
        '$conference',
        '$text',
    ]))


@template('page')
class Page(PageTemplate):

    template = string.Template('\n'.join([
        '%page',
        '$heading',
        '',
        '$text',
        '$footer_impl',
    ]))

    def __init__(self, variables):
        PageTemplate.__init__(self, variables)


@template('pageoftext')
class PageOfText(PageTemplate):

    template = string.Template('\n'.join([
        '%page',
        '%nodefault',
        '%$pageoftextlogo',
        '$heading',
        '%left, size 6, vgap 10',
        '$text',
        '$footer_impl',
    ]))


@template('dictpage')
class DictPage(PageTemplate):

    template = string.Template('\n'.join([
        '%page',
        '%nodefault',
        '%$default1',
        '$heading',
        '%center, size 8, vgap 20',
        '$text',
    ]))


@template('listpage')
class ListPage(PageTemplate):

    template = string.Template('\n'.join([
        '%page',
        '%nodefault',
        '%$default1',
        '$heading',
        '%$default2',
        '%$default3',
        '%$default4',
        '$line1',
        '%size 1',
        '$line2',
        '%size 6, vgap 20',
        '$rest2',
        '$footer_impl',
    ]))


def main():
    process(fileinput.input(), sys.stdout, VARIABLES, TEMPLATES, Preamble)


if __name__ == '__main__':
    main()
