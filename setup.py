#!/usr/bin/env python3

import subprocess

from distutils.core import Extension, setup


def pkgconfig(package):
    result = {}
    for token in subprocess.check_output(['pkg-config', '--libs', '--cflags', package]).decode('utf-8').split():
        if token.startswith('-I'):
            result.setdefault('include_dirs', []).append(token[2:])
        elif token.startswith('-L'):
            result.setdefault('library_dirs', []).append(token[2:])
        elif token.startswith('-l'):
            result.setdefault('libraries', []).append(token[2:])
    return result


setup(
    name='repology',
    version='0.0.0',
    description='Compare package versions in many repositories',
    author='Dmitry Marakasov',
    author_email='amdmi3@amdmi3.ru',
    url='http://repology.org/',
    packages=[
        'repology',
        'repology.fetcher',
        'repology.parser',
    ],
    scripts=[
        'repology-app.py',
        'repology-benchmark.py',
        'repology-dump.py',
        'repology-gensitemap.py',
        'repology-linkchecker.py',
        'repology-update.py',
    ],
    classifiers=[
        'Topic :: System :: Archiving :: Packaging',
        'Topic :: System :: Software Distribution',
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Environment :: Web Environment',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: C',
    ],
    ext_modules=[
        Extension(
            'repology.version',
            sources=['repology/version.c'],
            **pkgconfig('libversion')
        )
    ]
)
