# Copyright 2021 Ismael Luceno <ismael@iodev.co.uk>
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

import lzma

from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.transformer import PackageTransformer


class SourcemagePkglistParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        with lzma.open(path, 'r', encoding='utf-8') as data:
            for line in data:
                if line[0] == '-':
                    continue
                name, version = line.split(' ', 1)
                pkg = factory.begin(line)
                pkg.add_name(name, NameType.UNSUPPORTED)
                pkg.set_version(version)
                yield pkg
