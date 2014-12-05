Slides from my Python course at Vilnius University

I taught this course in 2004, 2005 and 2006.  These slides are from 2006.
More information available at http://gedmin.as/study/python/index-lt.html
(in Lithuanian).

Trivia: mgp2pdf was written in 2004 specifically so that I could publish
my slides.

(How did I handle UTF-8 in 2004?  I don't remember!)

The PDFs are from http://gedmin.as/study/python/slides/

Current mgp2pdf fails to convert the mgp files with an exception inside PIL!
https://bitbucket.org/rptlab/reportlab/issue/51/transparent-png-causes-a-typeerror-cannot

Conversion issues:

- python2.pdf, slide 6: ideally there would be no word-wrapping.  (Original PDF
  from 2006 has the same problem, might be just a bug in my slides.  Maybe I
  used a different screen resolution during the presentation.)

- python3.pdf, slide 44 and also python7.pdf, slide 33 (same slide):
  I used %newimage -raise -50 in the original .mgp files.  mgp2pdf ignored
  the -raise due to a bug, so the original PDF from 2006 acts as if -raise
  wasn't specified.  Today's mgp also ignores -raise.  I don't remember
  what was happening with mgp in 2006.  Today's mgp2pdf handles -raise,
  which makes it clear the 50% shift I specified is wrong, so I adjusted
  the .mgp.  Anyway, if your PDFs do not match the original, that's the
  reason.
