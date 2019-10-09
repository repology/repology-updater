#!/usr/bin/env python3

from setuptools import setup


setup(
    name='repology',
    version='0.0.0',
    description='Compare package versions in many repositories',
    author='Dmitry Marakasov',
    author_email='amdmi3@amdmi3.ru',
    url='https://repology.org/',
    packages=[
        'repology',
        'repology.fetchers',
        'repology.parsers',
    ],
    scripts=[
        'repology-dump.py',
        'repology-gensitemap.py',
        'repology-update.py',
    ],
    classifiers=[
        'Topic :: System :: Archiving :: Packaging',
        'Topic :: System :: Software Distribution',
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: C',
    ],
    install_requires=[
        'Jinja2',
        'PyYAML',
        'jsonslicer',
        'libversion',
        'lxml',
        'psycopg2',
        'pyparsing',
        'requests',
        'rubymarshal>=1.2.6',
        'protobuf',
    ]
)
