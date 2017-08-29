# Copyright (C) 2016-2017 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from repology.package import Package


class HaikuPortsFilenamesParser():
    def __init__(self):
        pass

    def Parse(self, path):
        result = []

        for category in os.listdir(path):
            category_path = os.path.join(path, category)
            if not os.path.isdir(category_path):
                continue

            for package in os.listdir(category_path):
                package_path = os.path.join(category_path, package)
                if not os.path.isdir(package_path):
                    continue

                for recipe in os.listdir(package_path):
                    if not recipe.endswith('.recipe'):
                        continue

                    pkg = Package()

                    pkg.name = package
                    pkg.category = category

                    # may want to shadow haiku-only ports
                    #if pkg.category.startswith('haiku-'):
                    #    pkg.shadow = True

                    # it seems to be guaranteed there's only one hyphen in recipe filename
                    name, version = recipe[:-7].split('-', 1)

                    if package.replace('-', '_') != name:
                        print('WARNING: mismatch for package directory and recipe name: {} != {}'.format(package, name), file=sys.stderr)

                    pkg.version = version

                    result.append(pkg)

        return result
