Problem statement
=================

I need a tool to compare two PDF files to catch regressions in mgp2pdf.

- I know the PDFs have the same number of pages (well, they're supposed to; if
  they don't, the tool needs to report that as a difference).
- I care about the visual layout, not just textual contents.  Perceptual diff:
  good, piping pdftotext to GNU diff: bad.
- I want automation: the tool should be able to compare two sets of PDFs
  and tell me if they're identical, and if not, produce a report with the
  differences between each pair of files.

My options are:

- Find an existing tool.
- Write a new tool.

I actually once wrote such a tool for an internal project.  I can extract and
open-source it.  I just need a name.  This means I have to survey existing
tools to avoid name clashes.  And hey, maybe one of the existing tools will
turn out to do what I want and I can save effort!


Survey of existing tools
------------------------

Sources:

- Google search for "pdf diff" or "pdf compare"

  - http://superuser.com/questions/517004/tool-for-performing-a-pdf-diff

    - http://www.cs.ox.ac.uk/people/cas.cremers/misc/pdfdiff.html
      (relies on pdftotext)

  - http://superuser.com/questions/46123/how-to-compare-the-differences-between-two-pdf-files-on-windows

    - apt-get install diffpdf (package of http://www.qtrac.eu/diffpdf.html)
    - https://github.com/vslavik/diff-pdf

  - http://stackoverflow.com/questions/145657/tool-to-compare-large-numbers-of-pdf-files

    - Nice idea in one answer: compare PDF content directly, ignoring irrelevant
      changes ::

        diff --brief -I xap: -I xapMM: -I /CreationDate -I /BaseFont -I /ID --binary --text

- apt-cache search compare pdf

    - comparepdf - command line tool for comparing two PDF files
    - diffpdf - compare two PDF files textually or visually

- GitHub search for "pdf diff" or "pdf compare"

  - https://github.com/search?utf8=%E2%9C%93&q=pdf+diff: 24 repos, which I cut
    down to this list:

    - https://github.com/vslavik/diff-pdf
    - https://github.com/JoshData/pdf-diff
    - https://github.com/zeliboba/DiffPDF-app (import of http://www.qtrac.eu/diffpdf.html)
    - https://github.com/hyperjeff/PDF-Diff (text only)
    - https://github.com/witwall/diffpdf (import of http://www.qtrac.eu/diffpdf.html)
    - https://github.com/apex-hughin/DiffPDF (import of http://www.qtrac.eu/diffpdf.html)
    - https://github.com/apark0114/pdfBox (no README)
    - https://github.com/koyachi/diff_pdf_image (small Ruby script, grayscales and composes as different color channels)
    - https://github.com/momeni/visual-pdf-diff (small shell script that composes two pdfs with imagemagick)
    - https://github.com/mattcorey/pdfpdiff (perceptual diff in Java, no screenshots, "still under development")
    - https://github.com/omiron/pdfdiff (no README; uses Pillow to convert PDF to PNG; loops over every pixel in Python to diff them)
    - https://github.com/HyGear/diff-dwg (Python script; "only compatible with Windows but Linux compatiblity will be added later"; red/green composition)
    - https://github.com/svi-berlin/image-diff/blob/master/send_email.py#L44
      (the repo is otherwise uninteresting, but the use of ImageMagick's
      convert foo.jpg bar.jpg -compose difference ... was intriguing)
    - https://github.com/nuxeo/nuxeo-versions-difference (no README; Java)
    - https://github.com/tpltnt/cli-diffpdf (pdftotext + wdiff)
    - https://github.com/hgustafsson/skillnad (requires LaTeX sources)

  - https://github.com/search?utf8=%E2%9C%93&q=pdf+compare: 28 repos, some of
    them duplicating the ones from the previous search

    - https://github.com/jnweiger/pdfcompare
    - https://github.com/ESCRIBA/lenient-pdf-compare (Java; no screenshots)
    - https://github.com/enroxorz/pdfcompare (Ruby, wraps PDFBox which is Java; no screenshots)
    - https://github.com/magmax/pdfcomparator (pypi and travis badges! computes similarity percentage, doesn't produce visual reports with differences; uses Poppler's python bindings and Cairo to render PDFs)
    - https://github.com/kspeeckaert/pyPdfCompare (uses Wand, which is a ctypes-based ImageMagick binding; produces PDF with differences)
    - https://github.com/anandsudhir/pdfassert (Java unit test assertion library)
    - https://github.com/ralfebert/imageassert (Java unit test assertion library)


`compare.py <https://github.com/mgedmin/mgp2pdf/blob/master/compare.py>`_
in this very repository:

- Can compare an .mgp with a .pdf, not just two PDFs.
- Renders the pages to images, makes them translucent, overlays them for manual
  visual comparison.
- Can be used interactively.
- Can produe a "report" (set of PNG files with translucent original pages
  overlaid on top of each other) in non-interactive mode.
- Not automated: doesn't tell if the two presentations are identical.
- Written in Python, uses Pillow and/or Pygame.
- Relies on external tools: mgp, pdftoppm, ImageMagick.

**compare-reportgen-output** from that internal project I mentioned:

- Can compare two sets of PDFs.
- Renders the pages to images, compares them pixel-by-pixel.
- Automated.
- Produes a report with differing pages shown next to each other and a third
  page with the differences highlighted.
- Some work needs to be done to make it generic.
- Written in Python.
- Relies on external tools: ImageMagick.

`DiffPDF <http://www.qtrac.eu/diffpdf.html>`__

- Packaged for Ubuntu (apt-get install diffpdf).
- Upstream no longer open source.
- Interactive.

`ComparePDF <http://www.qtrac.eu/comparepdf.html>`__

- Packaged for Ubuntu (apt-get install comparepdf).
- Automated.
- Reports "yes" or "no", doesn't show differences, doesn't produce reports.

`vslavik/diff-pdf <https://github.com/vslavik/diff-pdf>`__

- Website: http://vslavik.github.io/diff-pdf/
- Uses overlaid red/green channels to compose an image from two sources.
- Automated.
- Can produce a report as PDF.
- Has an interactive mode.
- Written in C++.

`JoshData/pdf-diff <https://github.com/JoshData/pdf-diff>`__

- Compares document text rather than visual layout.
- Produces a nice PNG report.
- Written in Python.
- Relies on external tools: pdftotext.

`jnweiger/pdfcompare <https://github.com/jnweiger/pdfcompare>`__

- Can compare document text, annotate the PDF with highlighted changes.
- Doesn't compare images.
- Written in Python.
- Relies on pdftohtml.

`magmax/pdfcomparator <https://github.com/magmax/pdfcomparator>`__

- https://pypi.python.org/pypi/pdfcomparator
- Compares rendered images.
- Automated: can report yes/no, can report similarity percentage (using
  difflib on extracted text).
- Doesn't produce a report with the differences.
- Written in Python.
- Relies on Poppler and Cairo Python bindings to render them.

`kspeeckaert/pyPdfCompare <https://github.com/kspeeckaert/pyPdfCompare>`__

- Automated.
- Produces PDF report using Pillow's ImageChops for highlighting differenes, using
  http://stackoverflow.com/questions/18341754/color-in-red-diffrencies-between-two-pictures
- Written in Python.
- Relies on ImageMagick via Wand (ctypes-based wrapper).
