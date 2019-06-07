#!/usr/bin/env python3
#
# Copyright (C) 2016-2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
import sys
from datetime import date

from voluptuous import All, Any, Contains, MultipleInvalid, Required, Schema, Url

import yaml


families = [
    'adelie',
    'aix',
    'alpine',
    'anitya',
    'aosc',
    'arch',
    'buckaroo',
    'centos',
    'chocolatey',
    'conda',
    'cpan',
    'cran',
    'crates_io',
    'crux',
    'cygwin',
    'debuntu',
    'distrowatch',
    'elpa',
    'exherbo',
    'fdroid',
    'fedora',
    'fink',
    'freebsd',
    'freshcode',
    'gentoo',
    'gobolinux',
    'guix',
    'hackage',
    'haikuports',
    'homebrew',
    'hpux',
    'kaos',
    'librecnc',
    'libregamewiki',
    'lunar',
    'macports',
    'mageia',
    'mer',
    'msys2',
    'nix',
    'openbsd',
    'openindiana',
    'openmandriva',
    'openpkg',
    'opensuse',
    'openwrt',
    'pclinuxos',
    'pisi',
    'pkgsrc',
    'pld',
    'pypi',
    'ravenports',
    'reactos',
    'rosa',
    'rubygems',
    'rudix',
    'salix',
    'scoop',
    'sisyphus',
    'slackbuilds',
    'tinycore',
    'slackware',
    'slitaz',
    'snap',
    'solus',
    't2',
    'termux',
    'vcpkg',
    'void',
    'wikidata',
    'yacp',
]

rulesets = families + [
    'antergos',
    'antix',
    'astra',
    'aur',
    'blackarch',
    'bunsenlabs',
    'deb_multimedia',
    'deepin',
    'epel',
    'frugalware',
    'funtoo',
    'gnuelpa',
    'homebrew_casks',
    'hyperbola',
    'maemo',
    'manjaro',
    'melpa',
    'mint',
    'msys2_mingw',
    'msys2_msys2',
    'mx',
    'packman',
    'parabola',
    'pardus',
    'parrot',
    'slitaz_next',
    'unitedrpms',
    'whonix',
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
            'default_maintainer': All(str, Contains('@')),
            Required('minpackages'): int,
            Required('sources'): [
                {
                    Required('name'): Any(str, [str]),
                    'disabled': bool,
                    Required('fetcher'): str,
                    Required('parser'): str,
                    'url': str,  # not Url(), as there may be rsync or cvs addresses

                    # git fetcher args
                    'branch': str,
                    'subrepo': str,
                    'sparse_checkout': [str],

                    # some common fetcher args
                    'fetch_timeout': Any(int, float),

                    # arch parser
                    'allowed_archs': [str],

                    # debian parser
                    'project_name_from_source': bool,

                    # srclist parser
                    'encoding': Any('utf-8', 'cp1251'),

                    # misc dsv parsers
                    'numfields': int,

                    # elasticsearch fetcher
                    'scroll_url': str,
                    'es_scroll': str,
                    'es_size': int,
                    'es_filter': dict,
                    'es_fields': [str],

                    # file fetcher
                    'compression': Any('xz', 'bz2', 'gz'),
                    'post': {str: str},
                    'headers': {str: str},
                    'nocache': bool,

                    # crates_io fetcher
                    'fetch_delay': Any(int, float),

                    # aur fetcher
                    'max_api_url_length': int,

                    # rsync fetcher
                    'rsync_include': str,
                    'rsync_exclude': str,
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
            'maintainer': Any(str, [str]),
            'verlonger': int,
            'vergt': str,
            'verge': str,
            'verlt': str,
            'verle': str,
            'flag': str,
            'noflag': str,

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
            'rolling': bool,
            'snapshot': bool,
            'successor': bool,
            'generated': bool,
            'addflag': str,
            'last': bool,
            'tolowername': bool,
            'replaceinname': dict,
            'warning': str,
        }
    ]
}


def get_yaml(path):
    with open(path) as yamlfile:
        return yaml.safe_load(yamlfile)


def parse_arguments():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-s', '--schema', choices=schemas.keys(), required=True, help='schema to use')
    parser.add_argument('files', metavar='file', nargs='*', help='files to check')

    return parser.parse_args()


def main() -> int:
    options = parse_arguments()

    errors = 0

    for path in options.files:
        try:
            Schema(schemas[options.schema])(get_yaml(path))
        except MultipleInvalid as e:
            print('Bad schema for {}: {}'.format(path, str(e)))
            errors += 1

    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
