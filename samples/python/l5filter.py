#!/usr/bin/python
import sys

pagesize = 11
preamble = """
%nodefault,area 90 90, vgap 260, size 8, font "standard", fore "#134d73", back "white", right, newimage -zoom 75 "vu-logo.png"
%size 3

%size 6, vgap 40, left
""".strip()

pagebreak = "%page\n" + preamble



def format(lines):
    iterlines = iter(lines)
    def nextline():
        try:
            return iterlines.next()
        except StopIteration:
            return None

    print preamble
    nlines = 0
    line = nextline()
    while line is not None:
        if line.startswith("#"):
            print line.strip()
            line = nextline()
            continue
        output = []
        if '--' in line:
            a, b = line.split("--", 1)
            output = []
            if a:
                output += ['%font "thick"\n' + a.strip()]
            if b.strip():
                output.append('%font "standard"\n\t' + b.strip())
                line = nextline()
            else:
                while True:
                    line = nextline()
                    if line is None: break
                    if not line.startswith('    '): break
                    line = line[4:]
                    output.append('%font "standard"\n\t' + line.rstrip())
        else:
            output = ['%font "thick"\n' + line.strip()]
            line = nextline()
        if nlines + len(output) > pagesize:
            nlines = 0
            print pagebreak
        print "\n".join(output)
        nlines += len(output)


format(sys.stdin)
