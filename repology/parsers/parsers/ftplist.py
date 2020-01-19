# Copyright (C) 2018-2020 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
from repology.parsers import Parser
from repology.parsers.nevra import nevra_construct, nevra_parse
from repology.transformer import PackageTransformer


class RPMFTPListParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        with open(path) as listfile:
            for line in listfile:
                with factory.begin() as pkg:
                    filename = line.strip().split()[-1]

                    name, epoch, version, release, arch = nevra_parse(filename)

                    assert(arch == 'src')

                    pkg.add_name(name, NameType.SRCRPM_NAME)
                    pkg.set_version(version)
                    pkg.set_rawversion(nevra_construct(None, epoch, version, release))
                    pkg.set_arch(arch)

                    pkg.set_extra_field('nevr', filename.rsplit('.', 2)[0])

                    yield pkg
