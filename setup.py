#!/usr/bin/env python3

from distutils.core import Extension, setup

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
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Web Environment',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: C',
    ],
    ext_modules=[
        Extension(
            'repology.version',
            sources=['repology/version.c'],
        )
    ]
)
