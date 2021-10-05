# Copyright (C) 2016-2019,2021 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
import re
from typing import Iterable

from repology.logger import Logger
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.patches import add_patch_files


class HaikuPortsFilenamesParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
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

                    pkg = factory.begin()

                    pkg.add_name(package, NameType.HAIKUPORTS_NAME)
                    pkg.add_name(f'{category}/{package}', NameType.HAIKUPORTS_FULL_NAME)
                    pkg.add_categories(category)

                    # may want to shadow haiku-only ports
                    #if pkg.category.startswith('haiku-'):
                    #    pkg.shadow = True

                    # it seems to be guaranteed there's only one hyphen in recipe filename
                    name, version = recipe[:-7].split('-', 1)

                    if package.replace('-', '_') != name:
                        pkg.log('mismatch for package directory and recipe name: {} != {}'.format(package, name), severity=Logger.WARNING)

                    pkg.set_version(version)

                    with open(os.path.join(category_path, package, recipe), 'r', encoding='utf-8') as fd:
                        recipefile = fd.read()

                        # XXX: we rely on the fact that no substitutions happen in these
                        # variables. That's true as of 2018-05-14.
                        if (match := re.search('^HOMEPAGE="([^"]+)"', recipefile, re.MULTILINE)):
                            pkg.add_homepages(match.group(1).split())

                        # XXX: this is not really precise, as we list all patches if there's
                        # suspiction that a recipe uses any of them
                        if re.search('^PATCHES=', recipefile, re.MULTILINE):
                            add_patch_files(pkg, os.path.join(package_path, 'patches'))

                    yield pkg
