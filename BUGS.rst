Bug examples:

- samples/doctests/doctests.mgp, slide 8: image should be centered

- samples/doctests/doctests.mgp, slide 17: image should be above text

- samples/doctests2/literate-doctesting.mgp: slide 42 shouldn't be
  word-wrapped (this was correct in the original PDF from 2006)

- samples/doctests2/literate-doctesting.mgp: slide 58 shouldn't be
  word-wrapped (this was correct in the original PDF from 2006;
  same problem as the above)

- samples/doctests2/literate-doctesting.mgp: slide 71 has excessive
  word-wrapping?

- samples/python/python2.mgp: slide 6 has excessive word-wrapping?

Systemic bugs:

- %mark/%again handling is wrong: you can use %again only once
  (https://github.com/mgedmin/mgp2pdf/pull/1)

- %mark/%again handling is wrong: %again isn't supposed to add a new blank
  line and apply defaults etc (but I rely on that in
  samples/pyconlt/talk.mgp!)

- %defaults are applied too late: when I see text.  So if I have

     %left
     text on line N

  I'm handling %left before I'm applying the defaults of line N, so I have
  to hack _directives_used_in_this_line to suppress default application,
  which is totally the wrong mechanism to solve this.

  Also, defaults do not get applied for %newimage, which causes
  the image alignment bug in samples/doctests/doctests.mgp

- %newimage is supposed to break lines:

    %newimage "a.png"
    %newimage "b.png"

  mgp puts them on different lines, mgp2pdf puts them on one line.

- %cont is weird, e.g.

    %newimage "a.png"
    %cont, newimage "b.png"
    %newimage "c.png"

  puts all three images on a single line in mgp, which I don't understand

- %deffont is handled totally incorrectly; it's just a macro that
  records a bunch of directives to be replayed when the user uses %font
