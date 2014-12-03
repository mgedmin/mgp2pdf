My EuroPython 2006 presentation

The .mgp file isn't the actual source; I used a Python script to generate
it from a simpler ad-hoc markup format.

Conversion: the PDF actually looks better than the original (MagicPoint
wraps text in the middle of a word!).  Some excepions:

- on pages 42 and 58, mgp2pdf wraps the closing parenthesis of a Python
  expression (but mgp itself doesn't).

- slide 69 ought to have a smaller font so the text fits and isn't
  wrapped (mgp gets this hilariously wrong too).

- slide 71 also ought to fit (and fits with mgp)

- I've a feeling slide 86 was supposed to fit in three lines
