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
from typing import Dict, Iterable

from repology.logger import Logger
from repology.packagemaker import PackageFactory, PackageMaker
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
def _iter_sqlports(path: str) -> Iterable[Dict[str, str]]:
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
        'pkgname',
        'pkgpath',
        'pkgspec',
        'pkgstem',
    ]

    db = sqlite3.connect(os.path.join(path + '/share/sqlports'))
    cur = db.cursor()
    cur.execute('SELECT {} FROM Ports LEFT JOIN Paths USING(fullpkgpath)'.format(','.join(columns)))

    while True:
        row = cur.fetchone()
        if row is None:
            break

        yield dict(zip(columns, row))


class OpenBSDsqlportsParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        for row in _iter_sqlports(path):
            pkg = factory.begin(row['fullpkgpath'])

            # strip flavors (see https://man.openbsd.org/packages-specs)
            pkgname = re.sub('(-[^0-9][^-]*)+$', '', row['fullpkgname'])

            pkg.set_name_and_version(pkgname, _normalize_version)
            pkg.set_keyname(row['fullpkgpath'].split(',', 1)[0])
            pkg.set_summary(row['comment'])
            pkg.add_homepages(row['homepage'])
            pkg.add_maintainers(extract_maintainers(row['maintainer']))
            pkg.add_categories(row['categories'].split())

            pkg.set_extra_field('pkgpath', row['pkgpath'])
            pkg.set_extra_field('fullpkgpath', row['fullpkgpath'])

            if row['distfiles']:
                for distfile in row['distfiles'].split():
                    # process distfile renames
                    # Example: deco-{deco/archive/}1.6.4.tar.gz is downloaded as deco/archive/1.6.4.tar.gz
                    # but saved as deco-1.6.4.tar.gz
                    match = re.fullmatch('(.*)\\{(.*)\\}(.*)', distfile)
                    if match:
                        distfile = match.group(2) + match.group(3)

                    # determine master_sites
                    master_sites = row['master_sites']

                    match = re.fullmatch('(.*):([0-9]+)', distfile)
                    if match:
                        distfile = match.group(1)
                        master_sites = row['master_sites' + match.group(2)]

                    # done
                    if not master_sites:
                        pkg.log('distfiles without master_sites'.format(distfile, master_sites), severity=Logger.ERROR)
                        break

                    pkg.add_downloads((master_site + distfile for master_site in master_sites.split()))

            yield pkg


class OpenBSDIndexParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        with open(path, encoding='utf-8') as indexfile:
            for line in indexfile:
                pkg = factory.begin()

                fields = line.strip().split('|')
                if len(fields) < 7:  # varies
                    pkg.log('skipping, unexpected number of fields {}'.format(len(fields)), severity=Logger.ERROR)
                    continue

                pkgname = fields[0]

                # cut away string suffixes which come after version
                match = re.match('(.*?)(-[a-z_]+[0-9]*)+$', pkgname)
                if match:
                    pkgname = match.group(1)

                pkg.set_name_and_version(pkgname, _normalize_version)
                pkg.set_keyname(fields[1].split(',', 1)[0])
                pkg.set_summary(fields[3])
                pkg.add_maintainers(extract_maintainers(fields[5]))
                pkg.add_categories(fields[6].split())

                yield pkg
