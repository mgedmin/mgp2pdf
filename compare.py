#!/usr/bin/python
"""
Compare screenshots of MGP presentations with screenshots of PDF files.

Use: compare.py file.pdf file.mgp

Keys:
    Left or PgUp    -- back one slide
    f               -- toggle fullscreen
    q or Esc        -- quit
    1               -- show only one of the images
    2               -- show the other one of the images
    3               -- show both images (alpha-blended)
    any other key   -- advance to next slide

Needs some external programs:
    mgp
    pdftoppm (from xpdf)
    convert (from imagemagick)

"""

import os
import sys
import subprocess
import glob


EXTRAPATH = "/usr/X11R6/bin"
MGP = "mgp"
PDFTOPPM = "pdftoppm"
CONVERT = "convert"


class Error(Exception):
    pass


def inform(msg):
    print msg


def newer(file1, file2, ifnotexist=True):
    try:
        return os.stat(file1).st_mtime  > os.stat(file2).st_mtime
    except OSError:
        return ifnotexist


def try_mkdir(dirname):
    try:
        os.mkdir(dirname)
    except OSError:
        pass


def touch(filename):
    file(filename, 'w').close()


def system(*cmd):
    rc = subprocess.call(cmd)
    if rc != 0:
        raise Error('%s returned code %s' % (cmd[0], rc))


def choose_tempdir(filename):
    return os.path.join(os.path.dirname(filename),
                        '.compare-' + os.path.basename(filename))


def mgp_to_images(filename):
    tempdir = choose_tempdir(filename)
    timestampfile = os.path.join(tempdir, 'timestamp')
    if newer(filename, timestampfile):
        try_mkdir(tempdir)
        touch(timestampfile)
        inform("Converting %s to images" % filename)
        system(MGP, '-U', '-E', 'png', '-D', tempdir, filename)
    return sorted(glob.glob(os.path.join(tempdir, 'mgp?????.png')))


def pdf_to_images(filename):
    tempdir = choose_tempdir(filename)
    timestampfile = os.path.join(tempdir, 'timestamp')
    if newer(filename, timestampfile):
        try_mkdir(tempdir)
        touch(timestampfile)
        inform("Converting %s to images" % filename)
        system(PDFTOPPM, filename, os.path.join(tempdir, 'img'))
        for ppm in glob.glob(os.path.join(tempdir, 'img*.ppm')):
            system(CONVERT, ppm, os.path.splitext(ppm)[0] + '.png')
            os.unlink(ppm)
    return sorted(glob.glob(os.path.join(tempdir, 'img*.png')))


def to_images(filename):
    if filename.endswith('.mgp'):
        return mgp_to_images(filename)
    if filename.endswith('.pdf'):
        return pdf_to_images(filename)
    raise Error("don't know what to do with %s")


class PygameComparator:

    screen_size = (1024, 768)
    fullscreen = False

    _shared_dict = dict(_did_init=False)

    def __init__(self, filename1, filename2):
        self.__dict__ = self._shared_dict
        self.filename1 = os.path.basename(filename1)
        self.filename2 = os.path.basename(filename2)

    def init(self):
        if self._did_init:
            return
        self._did_init = True

        import pygame, pygame.locals
        pygame.init()
        self._set_mode()

    def _set_mode(self, fullscreen=None):
        import pygame, pygame.locals
        if fullscreen is None:
            fullscreen = self.fullscreen
        else:
            self.fullscreen = fullscreen
        mode = self.fullscreen and pygame.locals.FULLSCREEN or 0
        self.screen = pygame.display.set_mode(self.screen_size, mode)

    def compare(self, images):
        self.init()
        self.idx = 0
        while self.idx < len(images):
            self.compare_image(*images[self.idx])
            self.idx += 1

    def compare_image(self, img1, img2):
        self.init()
        import pygame, pygame.locals
        pygame.display.set_caption('Comparing %s and %s: slide %s'
                                   % (self.filename1, self.filename2,
                                      self.idx+1))
        img1 = pygame.image.load(img1)
        self.img1 = pygame.transform.scale(img1, self.screen_size)
        img2 = pygame.image.load(img2)
        self.img2 = pygame.transform.scale(img2, self.screen_size)
        self._draw()
        self._wait_for_key()

    def _draw(self):
        import pygame, pygame.locals
        self.img1.set_alpha(255)
        self.img2.set_alpha(128)
        self.screen.blit(self.img1, (0, 0))
        self.screen.blit(self.img2, (0, 0))
        pygame.display.flip()

    def _draw_one(self, img):
        import pygame, pygame.locals
        img.set_alpha(255)
        self.screen.blit(img, (0, 0))
        pygame.display.flip()

    def _wait_for_key(self):
        import pygame, pygame.locals
        while True:
            event = pygame.event.wait()
            if event.type == pygame.locals.QUIT:
                return
            if event.type == pygame.locals.KEYDOWN:
                if event.key in [pygame.locals.K_LALT,
                                 pygame.locals.K_RALT,
                                 pygame.locals.K_LCTRL,
                                 pygame.locals.K_RCTRL,
                                 pygame.locals.K_LSHIFT,
                                 pygame.locals.K_RSHIFT]:
                    pass
                if event.key == pygame.locals.K_ESCAPE:
                    sys.exit(0)
                elif event.key in (pygame.locals.K_PAGEUP,
                                   pygame.locals.K_LEFT):
                    if self.idx > 0:
                        self.idx -= 2
                        return
                elif event.unicode == '1':
                    self._draw_one(self.img1)
                elif event.unicode == '2':
                    self._draw_one(self.img2)
                elif event.unicode == '3':
                    self._draw()
                elif event.unicode in ('f', 'F'):
                    self._set_mode(not self.fullscreen)
                    self._draw()
                elif event.unicode in ('q', 'Q'):
                    sys.exit(0)
                else:
                    return


def compare(file1, file2, comparator=None):
    images1 = to_images(file1)
    images2 = to_images(file2)
    if len(images1) != len(images2):
        print "%s has %d slides, but %s has %d slides" % (file1, len(images1),
                                                          file2, len(images2))
    if not comparator:
        return
    comparator(file1, file2).compare(zip(images1, images2))


def setup_extra_path(extrapath):
    os.environ['PATH'] += ':' + extrapath


def main():
    if len(sys.argv) != 3:
        print >> sys.stderr, "Use: compare.py filename.pdf filename.mgp"
        sys.exit(1)
    setup_extra_path(EXTRAPATH)
    comparator = PygameComparator
    try:
        compare(sys.argv[1], sys.argv[2], comparator)
    except Error, e:
        print >> sys.stderr, e
        sys.exit(1)


if __name__ == '__main__':
    main()
