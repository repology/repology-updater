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

import re

from repology.logger import Logger
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers


def _normalize_version(version):
    match = re.match('(.*)v[0-9]+$', version)
    if match is not None:
        version = match.group(1)

    match = re.match('(.*)p[0-9]+$', version)
    if match is not None:
        version = match.group(1)

    return version


class OpenBSDIndexParser(Parser):
    def iter_parse(self, path, factory):
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
                pkg.set_summary(fields[3])
                pkg.add_maintainers(extract_maintainers(fields[5]))
                pkg.add_categories(fields[6].split())

                origin = fields[1].rsplit(',', 1)[0]
                pkg.set_origin(origin)
                pkg.set_extra_field('portname', origin.split('/')[1])

                yield pkg
