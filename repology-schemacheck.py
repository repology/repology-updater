#!/usr/bin/env python3
#
# Copyright (C) 2016-2017 Dmitry Marakasov <amdmi3@amdmi3.ru>
#
# This file is part of repology
#
# repology is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# repology is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with repology.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import os
import sys

from datetime import date

from voluptuous import All, Any, MultipleInvalid, Required, Schema, Url

import yaml


families = [
    'alpine',
    'anitya',
    'arch',
    'centos',
    'chocolatey',
    'cpan',
    'cran',
    'crux',
    'debuntu',
    'distrowatch',
    'fdroid',
    'fedora',
    'freebsd',
    'freshcode',
    'gentoo',
    'gobolinux',
    'guix',
    'hackage',
    'haikuports',
    'homebrew',
    'libregamewiki',
    'macports',
    'mageia',
    'msys2',
    'nix',
    'openbsd',
    'openindiana',
    'opensuse',
    'openwrt',
    'pclinuxos',
    'pkgsrc',
    'pypi',
    'ravenports',
    'rosa',
    'rubygems',
    'sisyphus',
    'slackbuilds',
    'snap',
    'yacp',
]

schemas = {
    'repos': [
        {
            Required('name'): str,
            Required('type'): Any('repository', 'site', 'modules'),
            Required('desc'): str,
            Required('family'): Any(*families),
            'color': str,
            'valid_till': date,
            'default_maintainer': str,
            Required('sources'): [
                {
                    Required('name'): Any(str, [str]),
                    Required('fetcher'): str,
                    Required('parser'): str,
                    'url': str,  # not Url(), as there may be rsync or cvs addresses
                    'branch': str,
                    'subrepo': str,

                    'compression': Any('xz', 'bz2', 'gz'),
                    'sparse_checkout': [str]
                }
            ],
            'shadow': bool,
            'repolinks': [
                {
                    Required('desc'): str,
                    Required('url'): Url(),
                }
            ],
            'packagelinks': [
                {
                    Required('desc'): str,
                    Required('url'): Url(),
                }
            ],
            'tags': [
                str
            ]
        }
    ],
    'rules': [
        {
            'name': Any(str, [str]),
            'namepat': str,
            'ver': Any(str, [str]),
            'verpat': str,
            'wwwpart': Any(str, [str]),
            'wwwpat': str,
            'family': Any(Any(*families), [Any(*families)]),
            'category': Any(str, [str]),
            'verlonger': int,

            'setname': str,
            'ignorever': bool,
            'unignorever': bool,
            'ignore': bool,
            'unignore': bool,
            'last': bool,
            'tolowername': bool,
            'replaceinname': dict,
            'warning': str,
        }
    ]
}


def GetYaml(path):
    with open(path) as yamlfile:
        return yaml.safe_load(yamlfile)


def Main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-s', '--schema', choices=schemas.keys(), required=True, help='schema to use')
    parser.add_argument('files', metavar='file', nargs='*', help='files to check')
    options = parser.parse_args()

    errors = 0

    for path in options.files:
        try:
            Schema(schemas[options.schema])(GetYaml(path))
        except MultipleInvalid as e:
            print('Bad schema for {}: {}'.format(path, str(e)))
            errors += 1

    return 1 if errors else 0


if __name__ == '__main__':
    os.sys.exit(Main())
