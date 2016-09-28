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

import os
import sys

from ..package import Package

class SpecParser():
    def __init__(self):
        pass

    def Parse(self, path):
        result = []

        for root, dirs, files in os.walk(path):
            for filename in files:
                if not filename.endswith(".spec"):
                    continue

                with open(os.path.join(root, filename), encoding='utf-8', errors='ignore') as specfile:
                    pkg = Package()

                    for line in specfile:
                        line = line.strip()

                        if line.find("%") != -1: # substitudes: ignore
                            continue

                        if line.startswith('Name:'):
                            pkg.name = line[5:].strip()
                        elif line.startswith('Version:'):
                            pkg.fullversion = line[8:].strip()
                            pkg.version = pkg.fullversion
                        elif line.startswith('Url:'):
                            pkg.homepage = line[4:].strip()
                        elif line.startswith('License:'):
                            pkg.license = line[8:].strip()
                        elif line.startswith('Group:'):
                            pkg.category = line[6:].strip().lower()
                        elif line.startswith('Summary:'):
                            pkg.comment = line[8:].strip()

                    if pkg.name is not None and pkg.version is not None:
                        result.append(pkg)
                    else:
                        print("WARNING: %s skipped, likely due to parsing problems" % filename, file=sys.stderr)

        return result
