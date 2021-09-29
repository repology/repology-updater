# Copyright (C) 2017 Steve Wills <steve@mouf.net>
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

from collections import Counter
from typing import Iterable

import rubymarshal.reader

from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.transformer import PackageTransformer


class RubyGemParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        skipped_gemplats: dict[str, int] = Counter()

        with open(path, 'rb') as fd:
            for gemname, gemversion, gemplat in rubymarshal.reader.load(fd):
                gemname = str(gemname)

                with factory.begin(gemname) as pkg:
                    if gemplat != 'ruby':
                        skipped_gemplats[gemplat] += 1
                        continue

                    gemversion = str(gemversion.marshal_dump()[0])

                    pkg.add_name(gemname, NameType.RUBYGEMS_NAME)
                    pkg.set_version(gemversion)

                    yield pkg

        for gemplat, count in sorted(skipped_gemplats.items()):
            factory.log(f'skipped {count} occurrence(s) of gemplat {gemplat}')
