Changelog
---------

0.10.2 (unreleased)
~~~~~~~~~~~~~~~~~~~

- Add Python 3.6 and 3.7 support (no actual code changes required).

- Drop Python 3.3 and 3.4 support.

- Stop using :weight=bold and such when passing font patterns to fc-match;
  specify :weight=200 etc.  Fixes "Unable to parse the pattern" from fc-match
  and "Could not find the font file for Sans:weight=bold" from mgp2pdf.


0.10.1 (2016-09-17)
~~~~~~~~~~~~~~~~~~~

- Correctly recognize ``...-...-r`` fonts as roman
  (`GH #6 <https://github.com/mgedmin/mgp2pdf/pull/6>`_).

- Add support for ``cyan`` color
  (`GH #5 <https://github.com/mgedmin/mgp2pdf/pull/5>`_).

- Fix typo in error message
  (`GH #4 <https://github.com/mgedmin/mgp2pdf/pull/4>`_).

- Add Python 3.5 support.

- Drop Python 2.6 support.


0.10 (2015-01-06)
~~~~~~~~~~~~~~~~~

- ``%filter`` is disabled by default for being a security risk.  Use
  ``--unsafe`` to enable.

- ``-o DIRECTORY`` is now supported.

- Interpret image paths relative to the location of the mgp file.

- Support Python 3.3 and up in addition to 2.6 and 2.7.

- More accurate text positioning (mgp2pdf no longer truncates the
  corrdinates to integral point values).

- More color names are now recognized: white, red, green, blue, yellow.

- Better font name recognition (requires ``fc-match`` from fontconfig).

- Improved error handling and reporting.

- Support ``%%`` comment syntax.

- Corrected handling of ``%default``, ``%tab``, ``%deffont``.

- Implemented ``%include``.

- Implemented ``%newimage -raise`` (also discovered that mgp itself ignores
  ``-raise``).

- 100% test coverage.


0.9 (2014-05-09)
~~~~~~~~~~~~~~~~

- First packaged release.
