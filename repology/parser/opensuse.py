# Copyright (C) 2016 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from ..util import SplitPackageNameVersion
from ..package import Package

class OpenSUSEPackageListParser():
    def __init__(self):
        pass

    def Parse(self, path):
        result = []

        with open(path, encoding="utf-8") as file:
            for line in file:
                line = line.strip()

                if line.find('/icons/rpm.png') == -1:
                    continue

                match = re.search("<a href=\"([^\"]+)-[0-9]+\.[0-9]+\.[^.]+\.rpm\">", line)

                if match:
                    pkg = Package()

                    pkg.name, pkg.fullversion = SplitPackageNameVersion(match.group(1))
                    pkg.version = pkg.fullversion

                    result.append(pkg)

        return result
