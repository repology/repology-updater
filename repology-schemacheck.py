#!/usr/bin/env python3
#
# Copyright (C) 2016-2023 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from voluptuous import All, Any, Contains, MultipleInvalid, NotIn, Required, Schema, Url

from repology.yamlloader import YamlConfig


families = [
    'adelie',
    'aix',
    'alpine',
    'anitya',
    'aosc',
    'appget',
    'arch',
    'ataraxia',
    'baulk',
    'buildroot',
    'carbs',
    'centos',
    'chakra',
    'chimera',
    'chocolatey',
    'chromebrew',
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
    'glaucus',
    'gobolinux',
    'guix',
    'hackage',
    'haikuports',
    'homebrew',
    'homebrew_casks',
    'hpux',
    'ibmi',
    'izzyondroid',
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
    'mpr',
    'msys2',
    'nix',
    'noir',
    'npackd',
    'opam',
    'openbsd',
    'openindiana',
    'openmamba',
    'openmandriva',
    'openpkg',
    'opensuse',
    'openvsx',
    'openwrt',
    'os4depot',
    'pacstall',
    'pclinuxos',
    'pisi',
    'pkgsrc',
    'pld',
    'postmarketos',
    'ptxdist',
    'pypi',
    'ravenports',
    'reactos',
    'rosa',
    'rubygems',
    'rudix',
    'sagemath',
    'salix',
    'sclo',
    'scoop',
    'serpentos',
    'sisyphus',
    'slackbuilds',
    'spack',
    'stalix',
    'tinycore',
    'slackware',
    'slitaz',
    'snap',
    'solus',
    't2',
    'termux',
    'tincan',
    'ubi',
    'vcpkg',
    'void',
    'wakemeops',
    'wikidata',
    'winget',
    'yacp',
    'yiffos',
]

rulesets = families + [
    'amazon',
    'antergos',
    'antix',
    'apertis',
    'archpower',
    'artix',
    'astra',
    'aur',
    'bioarch',
    'blackarch',
    'bunsenlabs',
    'calculate',
    'chaotic-aur',
    'deb_multimedia',
    'debian',
    'debjanitor',
    'deepin',
    'dports',
    'endlessos',
    'entware',
    'epel',
    'frugalware',
    'funtoo',
    'gnuelpa',
    'hyperbola',
    'kali',
    'kaos_build',
    'liguros',
    'macosx',
    'macosxbins',
    'maemo',
    'manjaro',
    'melpa',
    'melpa_stable',
    'melpa_unstable',
    'mint',
    'mports',
    'msys2_mingw',
    'msys2_msys2',
    'msys2_clang64',
    'msys2_clangarm64',
    'msys2_ucrt64',
    'mx',
    'openeuler',
    'packman',
    'parabola',
    'pardus',
    'parrot',
    'pureos',
    'raspbian',
    'rebornos',
    'rpm',
    'rpmsphere',
    'side',
    'siduction',
    'slitaz_next',
    'slitaz_current',
    'stackage',
    'terra',
    'trisquel',
    'ubuntu',
    'unitedrpms',
    'whonix',
    'windows',
]

packagelinks = [
    {
        Required('type'): str,
        Required('url'): Url(),
        'priority': All(int, NotIn([0], 'priority 0 is reserved for generated links'))
    }
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
            Required('ruleset'): Any(Any(*rulesets), [Any(*rulesets)]),
            'color': str,
            'valid_till': date,
            'default_maintainer': All(str, Contains('@')),
            'update_period': Any(int, str),
            Required('minpackages'): int,
            'pessimized': str,
            Required('sources'): [
                {
                    Required('name'): Any(str, [str]),
                    'disabled': bool,

                    'subrepo': str,

                    Required('fetcher'): {
                        Required('class'): str,

                        'url': str,  # not Url(), as there may be rsync or cvs addresses

                        # git
                        'branch': str,
                        'sparse_checkout': [str],
                        'depth': Any(int, None),

                        # elasticsearch
                        'scroll_url': str,
                        'es_scroll': str,
                        'es_size': int,
                        'es_filter': dict,
                        'es_fields': [str],

                        # common fetcher args
                        'fetch_timeout': Any(int, float),

                        # file
                        'compression': Any('xz', 'bz2', 'gz', 'br', 'zstd'),
                        'post': {str: str},
                        'headers': {str: str},
                        'nocache': bool,
                        'allow_zero_size': bool,

                        # crates_io
                        'fetch_delay': Any(int, float),

                        # aur
                        'max_api_url_length': int,

                        # rsync
                        'rsync_include': str,
                        'rsync_exclude': str,
                    },
                    Required('parser'): {
                        Required('class'): str,

                        # alpine
                        'path_suffix': str,

                        # rpm
                        'src': bool,
                        'binary': bool,
                        'vertags': Any(str, [str]),
                        'binnames_from_provides': bool,

                        # srclist
                        'encoding': Any('utf-8', 'cp1251'),

                        # misc dsv parsers
                        'numfields': int,

                        # gentoo
                        'require_md5cache_metadata': bool,
                        'require_xml_metadata': bool,

                        # openbsd
                        'path_to_database': Any(None, str),

                        # kiss
                        'maintainer_from_git': bool,
                        'use_meta': bool,

                        # debian
                        'allowed_vcs_urls': str,
                        'extra_garbage_words': Any(str, [str]),

                        # aur
                        'maintainer_host': str,

                        # guix
                        'download_hosts_blacklist': [str],

                        # nixos
                        'branch': str,
                        'enable_build_log_links': bool,

                        # homebrew
                        'require_ruby_source_path': bool,
                    },
                    'packagelinks': packagelinks,
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
            'packagelinks': packagelinks,
            'groups': [
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
    ],
    'maintainers': [
        {
            Required('maintainer'): str,
            'hide': bool,
            'replace': str,
        }
    ]
}


def get_yaml(path: str) -> Any:
    return YamlConfig.from_path(path).get_items()


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
            print(f'Bad schema for {path}: {str(e)}')
            errors += 1

    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
