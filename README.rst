mgp2pdf
=======

This is a quick-and-dirty MagicPoint_ to PDF converter.

.. _MagicPoint: http://member.wide.ad.jp/wg/mgp/

It supports only a subset of MagicPoint, specifically, the subset I used
in my slides.


Installation
------------

::

    pip install reportlab  # or sudo apt-get install python-reportlab


You can't pip install mgp2pdf (yet).


Usage
-----

::

    python mgp2pdf slides.mgp [-o output.pdf]


Why another converter?
----------------------

I used mgp to produce slides for a Python course I taught at Vilnius
University.  However, since most of the students are not (yet) Linux
users, they couldn't use MagicPoint to view my slides at home.  There are
some converters from MagicPoint to PostScript/HTML, but the result either
looks ugly, or doesn't support Unicode characters.  MagicPoint itself can
produce a number of bitmaps (by taking screenshots), but those are big,
and the conversion process is inconvenient (you cannot use your machine
while mgp is busy rendering slides and taking screenshots).

I wrote a Python program to interpret MagicPoint commands and produce a
PDF file using ReportLab.  It can handle my slides (Lithuanian), but
otherwise it is probably incomplete.  Feel free to give it a try.  File
bugs for missing features, and I'll see what I can do.


Resources
---------

There's a web page, of sorts, at http://mg.pov.lt/mgp2pdf

The source code can be found in this Git repository:
https://github.com/mgedmin/mgp2pdf.

To check it out, use ``git clone https://github.com/mgedmin/mgp2pdf``.

Report bugs at https://github.com/mgedmin/mgp2pdf/issues.

Licence: GPL v2 or later (http://www.gnu.org/copyleft/gpl.html)

If you want to leave a tip, see https://www.gittip.com/mgedmin/

.. image:: https://travis-ci.org/mgedmin/mgp2pdf.svg?branch=master
    :target: https://travis-ci.org/mgedmin/mgp2pdf
