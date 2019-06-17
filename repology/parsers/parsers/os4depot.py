# Copyright (C) 2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from typing import Iterable, Tuple

from repology.logger import Logger
from repology.packagemaker import PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.transformer import PackageTransformer


def _iter_index(path: str) -> Iterable[Tuple[str, str, int, str, str, str]]:
    with open(path, encoding='latin-1') as listfile:
        for line in listfile:
            if line.startswith(';'):
                continue

            category, filename, size, date, version, description = line.rstrip().split(' ', 5)

            if not description.startswith(':'):
                raise RuntimeError('cannot parse line: {}'.format(line))

            yield category, filename, int(size), date, version, description[1:]


class OS4DepotIndexParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        for category, filename, size, date, version, description in _iter_index(path):
            with factory.begin(filename) as pkg:
                pkg.set_extra_field('filename', filename)

                pkg.set_name(filename.rsplit('.', 1)[0])

                if not version:
                    pkg.log('skipping, no version', Logger.ERROR)
                    continue

                pkg.set_version(version)
                pkg.set_summary(description)
                pkg.add_categories(category)
                yield pkg
