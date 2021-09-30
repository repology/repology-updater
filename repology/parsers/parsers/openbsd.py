# Copyright (C) 2016-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import os
import re
import sqlite3
from typing import Any, Iterable, Optional

from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers
from repology.transformer import PackageTransformer


def _normalize_version(version: str) -> str:
    match = re.match('(.*)v[0-9]+$', version)
    if match is not None:
        version = match.group(1)

    match = re.match('(.*)p[0-9]+$', version)
    if match is not None:
        version = match.group(1)

    return version


# XXX: use repology.parsers.sqlite.iter_sqlite instead
def _iter_sqlports(path: str) -> Iterable[dict[str, Any]]:
    columns = [
        'fullpkgpath',
        'categories',
        'comment',
        'distfiles',
        'fullpkgname',
        'homepage',
        'maintainer',
        'master_sites',
        'master_sites0',
        'master_sites1',
        'master_sites2',
        'master_sites3',
        'master_sites4',
        'master_sites5',
        'master_sites6',
        'master_sites7',
        'master_sites8',
        'master_sites9',
        'gh_account',
        'gh_project',
        'dist_subdir',
    ]

    db = sqlite3.connect(path)
    cur = db.cursor()
    #cur.execute('SELECT {} FROM Ports LEFT JOIN Paths USING(fullpkgpath)'.format(','.join(columns)))
    # Note that this is somewhat memory-hungry compared to other parsers
    # sqlite takes about 200MB mem, for this query, even with `limit 1`,
    # and this may be reproduced even with `sqlite3` utility. No idea if
    # that can be improved.
    cur.execute('SELECT {} FROM Ports'.format(','.join(columns)))

    while True:
        row = cur.fetchone()
        if row is None:
            break

        yield dict(zip(columns, row))


def _iter_distfiles(row: dict[str, Any]) -> Iterable[str]:
    if row['distfiles'] is None:
        return

    for distfile in row['distfiles'].split():
        # process distfile renames
        # Example: deco-{deco/archive/}1.6.4.tar.gz is downloaded as deco/archive/1.6.4.tar.gz
        # but saved as deco-1.6.4.tar.gz
        match = re.fullmatch('(.*)\\{(.*)\\}(.*)', distfile)
        if match:
            distfile = match.group(2) + match.group(3)

        # determine master_sites (1.tgz uses master_sites, 1.gz:0 uses master_sites0 etc.)
        match = re.fullmatch('(.*):([0-9])', distfile)
        if match:
            distfile = match.group(1)
            master_sites = row['master_sites' + match.group(2)]
        else:
            master_sites = row['master_sites']

        # fallback to openbsd distfiles mirror
        if not master_sites:
            master_sites = 'http://ftp.openbsd.org/pub/OpenBSD/distfiles/{}/'.format(row['dist_subdir'])

        yield from (master_site + distfile for master_site in master_sites.split())


def _strip_flavors_from_stem(stem: str, flavors: Iterable[str]) -> str:
    flavors_set = set(flavor.lstrip('-') for flavor in flavors if flavor.startswith('-'))

    stem_parts = stem.split('-')

    while len(stem_parts) > 1:
        if stem_parts[-1] in flavors_set:
            stem_parts.pop()
        else:
            break

    return '-'.join(stem_parts)


class OpenBSDsqlportsParser(Parser):
    _path_to_database: str

    def __init__(self, path_to_database: Optional[str] = None) -> None:
        self._path_to_database = path_to_database or ''

    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        for row in _iter_sqlports(os.path.join(path + self._path_to_database)):
            with factory.begin(row['fullpkgpath']) as pkg:
                # there are a lot of potential name sources in sqlports, namely:
                # fullpkgpath, fullpkgname, pkgname, pkgspec, pkgstem, pkgpath (comes from Paths table)
                # * pkgname may be NULL, so ignoring it
                # * pkgpath is the same as fullpkgpath with flavors stripped, so no need to join with Paths
                # * pkgspec may be complex for our purposes, for it may contain version ranges in form of python-bsddb->=2.7,<2.8
                # * fullpkgname may be split into stem, version and flavors according to https://man.openbsd.org/packages-specs
                # * pkgstem is usually equal to the stem got from fullpkgname, but there are currently 12 exceptions
                #   like php-7.1, php-7.2, php-7.3, polkit-qt-, polkit-qt5-, so it's more reliable to get stem from fullpkgname
                #
                # As a result, we're basically left with fullpkgpath (which is path in ports tree + flavors)
                # and fullpkgname (which is package name aka stem + version + flavors)

                pkgpath, *flavors = row['fullpkgpath'].split(',')
                stem, version = re.sub('(-[^0-9][^-]*)+$', '', row['fullpkgname']).rsplit('-', 1)

                stripped_stem = _strip_flavors_from_stem(stem, flavors)

                pkg.add_name(stem, NameType.OPENBSD_STEM)
                pkg.add_name(pkgpath, NameType.OPENBSD_PKGPATH)
                pkg.add_name(stripped_stem, NameType.OPENBSD_STRIPPED_STEM)
                pkg.add_flavors(flavors)
                pkg.set_version(version, _normalize_version)
                pkg.set_summary(row['comment'])
                pkg.add_homepages(row['homepage'])
                if row['gh_account'] and row['gh_project']:
                    pkg.add_homepages('https://github.com/{}/{}'.format(row['gh_account'], row['gh_project']))
                pkg.add_maintainers(extract_maintainers(row['maintainer']))
                pkg.add_categories(row['categories'].split())
                pkg.add_downloads(_iter_distfiles(row))

                yield pkg
