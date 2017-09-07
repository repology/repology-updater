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
import re
import sys

from repology.package import Package
from repology.version import VersionCompare


def ExpandDownloadUrlTemplates(url):
    httpSourceforge = 'http://downloads.sourceforge.net'
    ftpGnu = 'ftp://ftp.gnu.org/gnu'
    return url.replace('$httpSourceforge', httpSourceforge) \
              .replace('${httpSourceforge}', httpSourceforge) \
              .replace('$ftpGnu', ftpGnu) \
              .replace('${ftpGnu}', ftpGnu) \
              .replace('$ftpAlphaGnu', ftpGnu)


class GoboLinuxGitParser():
    def __init__(self):
        pass

    def Parse(self, path):
        result = []

        trunk_path = os.path.join(path, 'trunk')
        for package_name in os.listdir(trunk_path):
            package_path = os.path.join(trunk_path, package_name)

            maxversion = None
            for version_name in os.listdir(package_path):
                if maxversion is None or VersionCompare(version_name, maxversion) > 0:
                    maxversion = version_name

            if maxversion is None:
                print('WARNING: no usable versions for package {}'.format(package_name), file=sys.stderr)
                continue

            recipe_path = os.path.join(package_path, maxversion, 'Recipe')
            description_path = os.path.join(package_path, maxversion, 'Resources', 'Description')

            pkg = Package()

            pkg.name = package_name
            pkg.version = maxversion

            if os.path.isfile(recipe_path):
                with open(recipe_path, 'r', encoding='utf-8', errors='ignore') as recipe:
                    for line in recipe:
                        line = line.strip()
                        if line.startswith('url='):
                            download = ExpandDownloadUrlTemplates(line[4:])
                            if download.find('$') == -1:
                                pkg.downloads.append(download.strip('"'))
                            else:
                                print('WARNING: Recipe for {}/{} skipped, unhandled URL substitude found'.format(package_name, maxversion), file=sys.stderr)

            if os.path.isfile(description_path):
                with open(description_path, 'r', encoding='utf-8', errors='ignore') as description:
                    data = {}
                    current_tag = None
                    for line in description:
                        line = line.strip()
                        match = re.match('^\[([A-Z][a-z]+)\] *(.*?)$', line)
                        if match:
                            current_tag = match.group(1)
                            data[current_tag] = match.group(2)
                        elif current_tag is None:
                            print('WARNING: Description for {}/{} skipped, dumb format'.format(package_name, maxversion), file=sys.stderr)
                            break
                        elif line:
                            if data[current_tag]:
                                data[current_tag] += ' '
                            data[current_tag] += line

                    if 'Summary' in data:
                        pkg.comment = data['Summary']
                    if 'License' in data:
                        pkg.licenses = [data['License']]
                    if 'Homepage' in data:
                        pkg.homepage = data['Homepage'].strip('"')

            result.append(pkg)

        return result
