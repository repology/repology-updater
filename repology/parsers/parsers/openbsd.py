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

import logging
import os
import re
import sqlite3
from dataclasses import dataclass
from typing import Iterable, Iterator, Tuple

from repology.package import LinkType, PackageFlags
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers


logger = logging.getLogger(__name__)


def _normalize_version(version: str) -> str:
    match = re.match('(.*)v[0-9]+$', version)
    if match is not None:
        version = match.group(1)

    match = re.match('(.*)p[0-9]+$', version)
    if match is not None:
        version = match.group(1)

    return version


# splits package name into (stem, version, list of flavors) according to https://man.openbsd.org/packages-specs
def _split_packagename(packagename: str) -> Tuple[str, str, list[str]]:
    components = packagename.split('-')
    for (pos, component) in enumerate(components):
        if pos > 0 and component and '0' <= component[0] <= '9':
            return ('-'.join(components[0:pos]), components[pos], components[pos + 1:])
    raise RuntimeError(f'package name {packagename} does not contain a version')


_PORTS_QUERY = """
SELECT
    _Ports.FullPkgPath AS id_,
    _Paths.FullPkgPath AS fullpkgpath,
    Categories_ordered.Value AS categories,
    comment,
    fullpkgname,
    homepage,
    _Email.Value AS maintainer,
    gh_account,
    gh_project,
    dist_subdir,
    _Broken.Value AS broken
FROM _Ports
    JOIN _Paths
        ON Canonical=_Ports.FullPkgPath
    JOIN Categories_ordered
        ON Categories_ordered.FullPkgpath=_Ports.FullPkgpath
    JOIN _Email
        ON _Email.KeyRef=MAINTAINER
    LEFT JOIN _Broken
        ON _Broken.FullPkgPath=_Ports.FullPkgPath
"""


@dataclass
class Port:
    id_: int
    fullpkgpath: str
    categories: str
    comment: str | None
    fullpkgname: str
    homepage: str | None
    maintainer: str
    gh_account: str | None
    gh_project: str | None
    dist_subdir: str | None
    broken: str | None
    distfiles_cursor: sqlite3.Cursor


def _iter_sqlports(path: str) -> Iterator[Port]:
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row

    cur = db.cursor()
    cur.execute(_PORTS_QUERY)

    while (row := cur.fetchone()) is not None:
        distfiles_cursor = db.cursor()
        distfiles_cursor.execute(_DISTFILES_QUERY, (row['id_'],))
        row_dict = dict(
            zip(
                (key.lower() for key in row.keys()),
                row
            )
        )
        yield Port(**row_dict, distfiles_cursor=distfiles_cursor)


_DISTFILES_QUERY = """
SELECT
    _sites.Value AS sites,
    _fetchfiles.Value AS file
FROM _distfiles
    JOIN _fetchfiles
        ON KeyRef=_Distfiles.Value
    LEFT JOIN _sites
        ON _sites.FullPkgPath=_Distfiles.FullPkgPath AND _distfiles.SUFX is not distinct from _sites.N
WHERE
    _distfiles.FullPkgPath = ?
"""


def _iter_distfiles(port: Port) -> Iterator[str]:
    while (row := port.distfiles_cursor.fetchone()) is not None:
        sites, file = row

        # process distfile renames
        # Example: deco-{deco/archive/}1.6.4.tar.gz is downloaded as deco/archive/1.6.4.tar.gz
        # but saved as deco-1.6.4.tar.gz
        if (match := re.fullmatch(r'(.*)\{(.*)\}(.*)', file)) is not None:
            file = match.group(2) + match.group(3)

        # fallback to openbsd distfiles mirror
        if not sites:
            sites = 'http://ftp.openbsd.org/pub/OpenBSD/distfiles/' + (f'{port.dist_subdir}/' if port.dist_subdir else '')

        yield from (site + file for site in sites.split())


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

    def __init__(self, path_to_database: str | None = None) -> None:
        self._path_to_database = path_to_database or ''

    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        for port in _iter_sqlports(os.path.join(path + self._path_to_database)):
            if port.broken:
                logger.info('Skipping broken package %s: %s', port.fullpkgpath, port.broken)
                continue

            with factory.begin(port.fullpkgpath) as pkg:
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

                pkgpath, *flavors = port.fullpkgpath.split(',')
                stem, version, _ = _split_packagename(port.fullpkgname)

                stripped_stem = _strip_flavors_from_stem(stem, flavors)

                pkg.add_name(stem, NameType.OPENBSD_STEM)
                pkg.add_name(pkgpath, NameType.OPENBSD_PKGPATH)
                pkg.add_name(stripped_stem, NameType.OPENBSD_STRIPPED_STEM)
                pkg.add_flavors(flavors)
                pkg.set_version(version, _normalize_version)
                pkg.set_summary(port.comment)
                pkg.add_links(LinkType.UPSTREAM_HOMEPAGE, port.homepage)
                if port.gh_account and port.gh_project:
                    pkg.add_links(LinkType.UPSTREAM_HOMEPAGE, f'https://github.com/{port.gh_account}/{port.gh_project}')
                pkg.add_maintainers(extract_maintainers(port.maintainer))
                pkg.add_categories(port.categories.split())
                pkg.add_categories(port.categories.split())
                pkg.add_links(LinkType.UPSTREAM_DOWNLOAD, _iter_distfiles(port))

                yield pkg
