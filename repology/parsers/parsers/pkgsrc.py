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

from typing import Iterable

from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.package import LinkType
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers
from repology.parsers.versions import VersionStripper


class PkgsrcIndexParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        normalize_version = VersionStripper().strip_right('nb')

        with open(path, encoding='utf-8') as indexfile:
            for line in indexfile:
                with factory.begin() as pkg:
                    fields = line.strip().split('|')
                    if len(fields) != 12:
                        raise RuntimeError(f'unexpected number of fields {len(fields)} != 12')
                    if not fields[0]:
                        raise RuntimeError('empty package name')

                    name, version = fields[0].rsplit('-', 1)

                    pkg.add_name(name, NameType.BSD_PKGNAME)
                    pkg.add_name(fields[1], NameType.BSD_ORIGIN)
                    pkg.set_version(version, normalize_version)
                    pkg.set_summary(fields[3])

                    # sometimes OWNER variable is used in which case
                    # there's no MAINTAINER OWNER doesn't get to INDEX
                    pkg.add_maintainers(extract_maintainers(fields[5]))

                    pkg.add_categories(fields[6].split())
                    pkg.add_links(LinkType.UPSTREAM_HOMEPAGE, fields[11].split())

                    yield pkg
