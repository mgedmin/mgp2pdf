#!/usr/bin/env python
import os

from setuptools import setup


here = os.path.dirname(__file__)
with open(os.path.join(here, 'README.rst')) as f:
    long_description = f.read()
with open(os.path.join(here, 'CHANGES.rst')) as f:
    long_description += '\n\n' + f.read()

setup(
    name='mgp2pdf',
    version='0.11.0',
    author='Marius Gedminas',
    author_email='marius@gedmin.as',
    url='https://github.com/mgedmin/mgp2pdf/',
    description='MagicPoint to PDF converter',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    license='GPL v2 or v3',

    py_modules=['mgp2pdf'],
    zip_safe=False,
    python_requires=">=3.7",
    install_requires=[
        'ReportLab',
    ],
    extras_require={
        'test': [
            'mock',
        ],
    },
    entry_points={
        'console_scripts': [
            'mgp2pdf = mgp2pdf:main',
        ],
    },
)
