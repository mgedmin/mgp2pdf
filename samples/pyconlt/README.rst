My talk from PyConLT 2012

The PDF is also from 2012

This is another presentation where I couldn't use mgp (lack of UTF-8
support) and so had to rely on mgp2pdf exclusively.  This means any
conversion errors were probably intentional.

Conversion issues:

- python-lt.mgp: mgp2pdf is handling %again incorrectly, and I'm relying
  on its incorrect handling.  mgp shows 'python' at the top centered,
  I expect it to be right-aligned.

- talk.mgp: same issue, I want the image to be top-right, mgp puts it in
  front of the text and centers both

- talk.mgp: mgp2pdf counts %again as a blank line for purposes of
  %default directives, mgp doesn't
