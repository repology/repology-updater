# Copyright (C) 2017-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from typing import Iterable

from repology.logger import Logger
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers
from repology.parsers.versions import VersionStripper


class DPortsIndexParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        normalize_version = VersionStripper().strip_right(',').strip_right('_')

        with open(path, encoding='utf-8') as indexfile:
            for line in indexfile:
                pkg = factory.begin()

                fields = line.strip().split('|')
                if len(fields) != 13:
                    pkg.log('skipping, unexpected number of fields {}'.format(len(fields)), severity=Logger.ERROR)
                    continue

                name, version = fields[0].rsplit('-', 1)

                pkg.add_name(name, NameType.BSD_PKGNAME)
                pkg.add_name('/'.join(fields[1].rsplit('/', 2)[1:]), NameType.BSD_ORIGIN)
                pkg.set_version(version, normalize_version)
                pkg.set_summary(fields[3])
                pkg.add_maintainers(extract_maintainers(fields[5]))
                pkg.add_categories(fields[6].split())
                pkg.add_homepages(fields[12])

                yield pkg
