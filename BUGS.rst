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

- samples/python/python3.mgp: slide 44 is rendered wrong,
  compared to the original PDF from 2006

  I've a rendering in /tmp timestampled 2014-12-04 10:26 +0200 which
  gets the text-vs-image alignment right, but moves all the text down
  unnecessarily (and has other problems on other slides).  The timestamp
  is right after commit a480eb14e3cb8c1c560ca8039f591736b3f56f66, but I
  can't reproduce those renders using that commit any more. :/

- samples/python/python7.mgp: slide 33 is rendered wrong,
  compared to the original PDF from 2006 (same problem as the above
  actually)
