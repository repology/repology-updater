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

from repology.package import Package
from repology.parsers.nevra import filename2nevra


class RPMFTPListParser():
    def __init__(self):
        pass

    def Parse(self, path):
        result = []

        with open(path) as listfile:
            for line in listfile:
                filename = line.strip().split()[-1]

                nevra = filename2nevra(filename)

                pkg = Package()

                pkg.name = nevra[0]
                pkg.version = nevra[2]

                pkg.extrafields['nevr'] = filename.rsplit('.', 2)[0]

                result.append(pkg)

        return result
