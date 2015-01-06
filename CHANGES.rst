Changelog
---------

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
