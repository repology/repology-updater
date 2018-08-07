# Copyright (C) 2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import sys

from repology.package import Package
from repology.parsers import Parser


class SliTazInfoParser(Parser):
    def __init__(self):
        pass

    def iter_parse(self, path, logger):
        result = []

        with open(path, encoding='utf-8') as indexfile:
            for line in indexfile:
                fields = line.split('\t')
                if len(fields) != 9:
                    print('WARNING: package {} skipped, incorrect number of fields in INDEX'.format(fields[0]), file=sys.stderr)
                    continue

                pkg = Package()

                pkg.name = fields[0]
                pkg.version = fields[1]
                pkg.category = fields[2]
                pkg.comment = fields[3]
                pkg.homepage = fields[4]

                result.append(pkg)

        return result
