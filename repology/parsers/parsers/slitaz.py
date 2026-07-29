# Copyright (C) 2018-2026 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from repology.package import LinkType
from repology.package import PackageFlags
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser


class SliTazInfoParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        with open(path, encoding='utf-8') as infofile:
            for line in infofile:
                with factory.begin() as pkg:
                    fields = line.strip().split('\t')
                    if len(fields) < 5:
                        raise RuntimeError(f'unexpected number of fields {len(fields)} < 5')

                    pkg.add_name(fields[0], NameType.GENERIC_SRCBIN_NAME)
                    pkg.set_version(fields[1])
                    pkg.add_categories(fields[2]) # also tags from [5]?
                    pkg.set_summary(fields[3])
                    pkg.add_links(LinkType.UPSTREAM_HOMEPAGE, fields[4])

                    yield pkg
