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
    'appget',
    'arch',
    'ataraxia',
    'buckaroo',
    'carbs',
    'centos',
    'chakra',
    'chocolatey',
    'conan',
    'conda',
    'cpan',
    'cran',
    'crates_io',
    'crux',
    'cygwin',
    'debuntu',
    'distri',
    'distrowatch',
    'elpa',
    'exherbo',
    'fdroid',
    'fedora',
    'fink',
    'freebsd',
    'freshcode',
    'fsd',
    'gentoo',
    'gobolinux',
    'guix',
    'hackage',
    'haikuports',
    'homebrew',
    'homebrew_casks',
    'hpux',
    'ibmi',
    'justinstall',
    'kaos',
    'kiss',
    'kwort',
    'librecnc',
    'libregamewiki',
    'luarocks',
    'lunar',
    'macports',
    'mageia',
    'mer',
    'msys2',
    'nix',
    'npackd',
    'openbsd',
    'openindiana',
    'openmamba',
    'openmandriva',
    'openpkg',
    'opensuse',
    'openwrt',
    'os4depot',
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
    'winget',
    'yacp',
]

rulesets = families + [
    'antergos',
    'antix',
    'apertis',
    'artix',
    'astra',
    'aur',
    'blackarch',
    'bunsenlabs',
    'calculate',
    'deb_multimedia',
    'debian',
    'deepin',
    'dports',
    'entware',
    'epel',
    'frugalware',
    'funtoo',
    'gnuelpa',
    'hyperbola',
    'kaos_build',
    'liguros',
    'macosx',
    'macosxbins',
    'maemo',
    'manjaro',
    'melpa',
    'mint',
    'msys2_mingw',
    'msys2_msys2',
    'mx',
    'openeuler',
    'packman',
    'parabola',
    'pardus',
    'parrot',
    'pureos',
    'rebornos',
    'rpm',
    'rpmsphere',
    'siduction',
    'slitaz_next',
    'trisquel',
    'ubuntu',
    'unitedrpms',
    'whonix',
    'windows',
]

schemas = {
    'repos': [
        {
            Required('name'): str,
            'sortname': str,
            'singular': str,
            Required('type'): Any('repository', 'site', 'modules'),
            Required('desc'): str,
            'statsgroup': str,
            Required('family'): Any(*families),
            'ruleset': Any(Any(*rulesets), [Any(*rulesets)]),  # XXX: make required
            'color': str,
            'valid_till': date,
            'default_maintainer': All(str, Contains('@')),
            'update_period': Any(int, str),
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
                    'depth': Any(int, None),

                    # some common fetcher args
                    'fetch_timeout': Any(int, float),

                    # rpm parser(s)
                    'src': bool,
                    'binary': bool,
                    'arch_from_filename': bool,

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
                    'compression': Any('xz', 'bz2', 'gz', 'br', 'zstd'),
                    'post': {str: str},
                    'headers': {str: str},
                    'nocache': bool,
                    'allow_zero_size': bool,

                    # crates_io fetcher
                    'fetch_delay': Any(int, float),

                    # aur fetcher
                    'max_api_url_length': int,

                    # rsync fetcher
                    'rsync_include': str,
                    'rsync_exclude': str,

                    # gentoo parser
                    'require_md5cache_metadata': bool,
                    'require_xml_metadata': bool,

                    # openbsd parser
                    'path_to_database': Any(None, str),

                    # kiss parser
                    'maintainer_from_git': bool,
                    'blob_prefix': str,
                }
            ],
            'shadow': bool,
            'incomplete': bool,
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
            'notver': Any(str, [str]),
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
            'nolegacy': bool,
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


def get_yaml(path: str) -> Any:
    with open(path) as yamlfile:
        return yaml.safe_load(yamlfile)


def parse_arguments() -> argparse.Namespace:
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
