# Copyright (C) 2016-2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from repology.logger import Logger
from repology.parsers import Parser
from repology.parsers.versions import VersionStripper


def _iter_cygports(path):
    for package in os.listdir(path):
        package_path = os.path.join(path, package)
        if not os.path.isdir(package_path):
            continue

        for cygport in os.listdir(package_path):
            if not cygport.endswith('.cygport'):
                continue

            yield os.path.join(package_path, cygport), cygport


class YACPGitParser(Parser):
    def iter_parse(self, path, factory):
        normalize_version = VersionStripper().strip_right('+')

        for cygport_path, cygport_name in _iter_cygports(path):
            pkg = factory.begin(cygport_name)

            # XXX: save *bl* to origversion
            match = re.match('(.*)-[0-9]+bl[0-9]+\.cygport$', cygport_name)
            if not match:
                pkg.log('unable to parse cygport name', severity=Logger.ERROR)
                continue

            pkg.set_name_and_version(match.group(1), normalize_version)

            # these fields not contain variables (for now), so are safe to extract
            with open(path, 'r') as cygdata:
                for line in cygdata:
                    match = re.match('CATEGORY="([^"$]+)"', line)
                    if match:
                        pkg.add_categories(match.group(1))

                    match = re.match('SUMMARY="([^"$]+)"', line)
                    if match:
                        pkg.set_summary(match.group(1))

            yield pkg
