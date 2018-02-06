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
    'aosc',
    'arch',
    'centos',
    'chocolatey',
    'cpan',
    'cran',
    'crates_io',
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
    'kaos',
    'libregamewiki',
    'macports',
    'mageia',
    'msys2',
    'nix',
    'openbsd',
    'openindiana',
    'openmandriva',
    'opensuse',
    'openwrt',
    'pclinuxos',
    'pkgsrc',
    'pypi',
    'ravenports',
    'rosa',
    'rubygems',
    'rudix',
    'scoop',
    'sisyphus',
    'slackbuilds',
    'snap',
    'vcpkg',
    'wikidata',
    'yacp',
]

rulesets = families + [
    'aur',
    'deb_multimedia',
    'deepin',
    'hyperbola',
    'parrot',
]

customflags = [
    'preserve_underscore',
    'nowildcard',
    'theiling',
]

schemas = {
    'repos': [
        {
            Required('name'): str,
            'sortname': str,
            'singular': str,
            Required('type'): Any('repository', 'site', 'modules'),
            Required('desc'): str,
            Required('family'): Any(*families),
            'ruleset': Any(Any(*rulesets), [Any(*rulesets)]),  # XXX: make required
            'color': str,
            'valid_till': date,
            'default_maintainer': str,
            Required('sources'): [
                {
                    Required('name'): Any(str, [str]),
                    Required('fetcher'): str,
                    Required('parser'): str,
                    'url': str,  # not Url(), as there may be rsync or cvs addresses

                    # git fetcher args
                    'branch': str,
                    'subrepo': str,
                    'sparse_checkout': [str],

                    # arch parser
                    'allowed_archs': [str],

                    # file fetcher
                    'compression': Any('xz', 'bz2', 'gz'),
                    'post': {str: str},
                    'headers': {str: str},
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
            'family': Any(Any(*families), [Any(*families)]),  # XXX: legacy; remove after rules converted to ruleset
            'ruleset': Any(Any(*rulesets), [Any(*rulesets)]),
            'noruleset': Any(Any(*rulesets), [Any(*rulesets)]),
            'category': Any(str, [str]),
            'verlonger': int,
            'vergt': str,
            'verge': str,
            'verlt': str,
            'verle': str,
            'flag': Any(Any(*customflags), [Any(*customflags)]),
            'noflag': Any(Any(*customflags), [Any(*customflags)]),

            'setname': str,
            'setver': str,
            'addflavor': Any(bool, str, [str]),
            'resetflavors': bool,
            'remove': bool,
            'ignore': bool,
            'devel': bool,
            'p_is_patch': bool,
            'any_is_patch': bool,
            'outdated': bool,
            'legacy': bool,
            'incorrect': bool,
            'untrusted': bool,
            'noscheme': bool,
            'snapshot': bool,
            'successor': bool,
            'rolling': bool,
            'addflag': Any(Any(*customflags), [Any(*customflags)]),
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


def ParseArguments():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-s', '--schema', choices=schemas.keys(), required=True, help='schema to use')
    parser.add_argument('files', metavar='file', nargs='*', help='files to check')

    return parser.parse_args()


def Main():
    options = ParseArguments()

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
