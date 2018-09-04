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

from libversion import version_compare

from repology.logger import Logger
from repology.package import Package
from repology.parsers import Parser


def ExpandDownloadUrlTemplates(url):
    http_sourceforge = 'http://downloads.sourceforge.net'
    ftp_gnu = 'ftp://ftp.gnu.org/gnu'
    return url.replace('$httpSourceforge', http_sourceforge) \
              .replace('${httpSourceforge}', http_sourceforge) \
              .replace('$ftpGnu', ftp_gnu) \
              .replace('${ftpGnu}', ftp_gnu) \
              .replace('$ftpAlphaGnu', ftp_gnu)


class GoboLinuxGitParser(Parser):
    def iter_parse(self, path, logger):
        trunk_path = os.path.join(path, 'trunk')
        for package_name in os.listdir(trunk_path):
            package_path = os.path.join(trunk_path, package_name)

            maxversion = None
            for version_name in os.listdir(package_path):
                if maxversion is None or version_compare(version_name, maxversion) > 0:
                    maxversion = version_name

            if maxversion is None:
                logger.log('no usable versions for package {}'.format(package_name), severity=Logger.ERROR)
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
                            if '$' not in download:
                                pkg.downloads.append(download.strip('"'))
                            else:
                                logger.log('Recipe for {}/{} skipped, unhandled URL substitude found'.format(package_name, maxversion), severity=Logger.ERROR)

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
                            logger.log('Description for {}/{} skipped, dumb format'.format(package_name, maxversion), severity=Logger.ERROR)
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

            yield pkg
