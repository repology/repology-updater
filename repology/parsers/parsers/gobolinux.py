# Copyright (C) 2016-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from libversion import version_compare

from repology.logger import Logger
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.patches import add_patch_files


def _expand_mirrors(url: str) -> str:
    # see Resources/Defaults/Settings/Compile/Compile.conf from https://github.com/gobolinux/Compile
    http_sourceforge = 'http://downloads.sourceforge.net'
    ftp_gnu = 'ftp://ftp.gnu.org/gnu'
    ftp_alpha_gnu = 'ftp://alpha.gnu.org/gnu'
    return url.replace('$httpSourceforge', http_sourceforge) \
              .replace('${httpSourceforge}', http_sourceforge) \
              .replace('$ftpGnu', ftp_gnu) \
              .replace('${ftpGnu}', ftp_gnu) \
              .replace('$ftpAlphaGnu', ftp_alpha_gnu)


class GoboLinuxGitParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        for recipe_name in os.listdir(path):
            if recipe_name.startswith('.'):
                continue

            pkg = factory.begin()

            pkg.add_name(recipe_name, NameType.GOBOLINUX_RECIPE)

            package_path = os.path.join(path, recipe_name)

            maxversion: str | None = None
            for version_name in os.listdir(package_path):
                if maxversion is None or version_compare(version_name, maxversion) > 0:
                    maxversion = version_name

            if maxversion is None:
                pkg.log('no usable versions found', severity=Logger.ERROR)
                continue

            pkg.set_version(maxversion)

            recipe_path = os.path.join(package_path, maxversion, 'Recipe')
            description_path = os.path.join(package_path, maxversion, 'Resources', 'Description')

            if os.path.isfile(recipe_path):
                with open(recipe_path, 'r', encoding='utf-8', errors='ignore') as recipe:
                    for line in recipe:
                        line = line.strip()
                        if line.startswith('url='):
                            download = _expand_mirrors(line[4:])
                            if '$' not in download:
                                pkg.add_downloads(download.strip('"'))
                            else:
                                factory.log('Recipe for {}/{} skipped, unhandled URL substitute found'.format(recipe_name, maxversion), severity=Logger.ERROR)

            if os.path.isfile(description_path):
                with open(description_path, 'r', encoding='utf-8', errors='ignore') as description:
                    data = {}
                    current_tag = None
                    for line in description:
                        line = line.strip()
                        match = re.match('^\\[([A-Z][a-z]+)\\] *(.*?)$', line)
                        if match:
                            current_tag = match.group(1)
                            data[current_tag] = match.group(2)
                        elif current_tag is None:
                            factory.log('Description for {}/{} skipped, dumb format'.format(recipe_name, maxversion), severity=Logger.ERROR)
                            break
                        elif line:
                            if data[current_tag]:
                                data[current_tag] += ' '
                            data[current_tag] += line

                    pkg.set_summary(data.get('Summary'))
                    pkg.add_licenses(data.get('License'))
                    pkg.add_homepages(data.get('Homepage', '').strip('"'))

            add_patch_files(pkg, os.path.join(package_path, maxversion), '*.patch*')

            yield pkg
