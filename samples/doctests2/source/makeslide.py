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
    .title
    .author
    .email
    .conference
        title page elements
    .titlepage
        produce a title page
    .page
        start a new page (one--two lines of text, centered vertically)
    .midpage
        start a new page (three lines of text, centered vertically)
    .bigpage
        start a new big page (four lines of text, centered vertically)
    .pageofcode
        start a new page for code examples (12 lines), enables Python syntax
    .pageoftext
        start a new page for text examples (12 lines)
    .italic
        switch font to italic
    .monospace
        switch font to monospace
    .normal
        switch font to normal
    .python
        enable Python syntax highlight
    .defaultsyntax
        use default syntax highlight (doctests)
    .nosyntax
        disable syntax highlight

Empty lines following a directive are skipped.

makeslide.py was written by Marius Gedminas <marius@pov.lt>
"""
import re
import sys
import string
import keyword
import fileinput

templates = dict(
    titlepage = string.Template('''\
#!/usr/bin/env mgp
# Note: tabs and trailing spaces are *important* in this file
# - Preamble ----------------------------------------------------------------
%deffont "standard" xfont "verdana"
%deffont "thick" xfont "verdana-bold"
%deffont "em" xfont "verdana-medium-i"
%deffont "mono" xfont "andale mono"
%default 1 area 90 90, vgap 260, size 8, font "standard", fore "#134d73", back "white", right, newimage -zoom 50 "povlogo.png"
%default 2 center, size 5
%default 3 size 8, vgap 80
%default 4 font "em", size 7, vgap 10
%default 5 font "standard", size 3
# ---------------------------------------------------------------------------
%page
%pcache 1 1 0 1
%ccolor "#134d73"
%nodefault
%size 7, font "standard", vgap 20, fore "black", back "white"


%center, font "thick", size 11
$title
%center, font "standard", size 7


%size 5, font "standard", fore "#134d73"
$author
%size 4
$email
%size 2

%size 5
Programmers of Vilnius
%size 4
http://pov.lt/
%size 2

%newimage "povlogo.png"


%fore "black"
$conference
'''),
    pageofcode = string.Template('''\
%page
%nodefault
%area 90 90, vgap 60, size 8, font "standard", fore "#134d73", back "white", right, newimage -zoom 50 "povlogo.png"

%left, size 6, vgap 10
'''),
    pageoftext = string.Template('''\
%page
%nodefault
%area 90 90, vgap 60, size 8, font "standard", fore "#134d73", back "white", right, newimage -zoom 50 "povlogo.png"

%left, size 6, vgap 10
'''),
    page = string.Template('''\
%page


'''),
    bigpage = string.Template('''\
%page
%nodefault
%area 90 90, vgap 60, size 8, font "standard", fore "#134d73", back "white", right, newimage -zoom 50 "povlogo.png"


%center, size 8, vgap 80
'''),
    midpage = string.Template('''\
%page
%nodefault
%area 90 90, vgap 60, size 8, font "standard", fore "#134d73", back "white", right, newimage -zoom 50 "povlogo.png"


%center, size 8, vgap 80

'''),
    italic = string.Template('%font "em"\n'),
    monospace = string.Template('%font "mono"\n'),
    normal = string.Template('%font "standard"\n'),
)



python_syntax_patterns = {
    r'\b(?P<kw>%s)\b' % '|'.join(keyword.kwlist): string.Template('''
%cont, font "thick"
$kw
%cont, font "standard"
'''),
    "(?P<s>'.*?')": string.Template('''
%cont, fore "#13734d"
$s
%cont, fore "#134d73"
''')
}

class PythonSyntaxHighligh(string.Template):

    def substitute(self, **kw):
        kw['line'] = apply_syntax_patterns(python_syntax_patterns, kw['line'])
        return super(PythonSyntaxHighligh, self).substitute(**kw)


line_patterns = {
    r'^(?P<indent>\s*)(?P<prefix>\.\.\.|>>>)(?P<line>.*)$': PythonSyntaxHighligh('''\
$indent
%cont, font "mono", fore "#00aaaa"
$prefix
%cont, font "standard", fore "#134d73"
$line
%font "standard"'''),
}

syntax_modes = {
    'nosyntax': {},
    'defaultsyntax': line_patterns,
    'python': python_syntax_patterns,
    'pageofcode': python_syntax_patterns,
}

default_syntax = line_patterns


def apply_syntax_patterns(syntax_patterns, line):
    idx = 0
    mega_re = []
    for idx, (pat, tmpl) in enumerate(syntax_patterns.items()):
        mega_re.append('(?P<r%d>%s)' % (idx, pat))
    mega_re = '|'.join(mega_re)
    def replacement(match):
        for idx, (pat, tmpl) in enumerate(syntax_patterns.items()):
            if match.group('r%d' % idx):
                return tmpl.substitute(**match.groupdict())
        assert False, 'empty match?'
    if mega_re:
        line = re.sub(mega_re, replacement, line)
    return line


def preprocess(inputfile, outputfile):
    args = {'title': '', 'author': '', 'email': '', 'conference': ''}
    syntax_patterns = default_syntax
    skipping_empty_lines = True
    for line in inputfile:
        if not line.strip() and skipping_empty_lines:
            continue
        line = line.rstrip('\n')
        if line.startswith('.') and not line.startswith('...'):
            keyword = line.split()[0][1:]
            if keyword in args:
                args[keyword] = line[len(keyword)+1:].strip()
            elif keyword in templates:
                print >> outputfile, templates[keyword].substitute(**args),
                syntax_patterns = syntax_modes.get(keyword, default_syntax)
            elif keyword in syntax_modes:
                syntax_patterns = syntax_modes[keyword]
            else:
                print >> sys.stderr, ".%s ignored" % keyword
            skipping_empty_lines = True
        else:
            skipping_empty_lines = False
            line = apply_syntax_patterns(syntax_patterns, line)
            print >> outputfile, line


if __name__ == '__main__':
    preprocess(fileinput.input(), sys.stdout)
