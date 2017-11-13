# Copyright (C) 2017 Dingyuan Wang <gumblex@aosc.io>
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

import json
import sys

from repology.package import Package


def SanitizeVersion(version):
    origversion = version

    pos = version.rfind(':')
    if pos != -1:
        version = version[pos + 1:]

    if version != origversion:
        return version, origversion
    else:
        return version, None


class AoscPkgsParser():
    def __init__(self):
        pass

    def Parse(self, path):
        result = []

        with open(path, 'r', encoding='utf-8') as jsonfile:
            for package in json.load(jsonfile)['packages']:
                pkg = Package()

                pkg.name = package['name']

                if package['version'] is None:
                    print('no version: {}'.format(pkg.name), file=sys.stderr)
                    continue

                pkg.version, _ = SanitizeVersion(package['version'])
                pkg.origversion = package['full_version']
                pkg.category = package['pkg_section'] or package['section']
                pkg.comment = package['description']

                if pkg.version == '999':
                    pkg.ignoreversion = True

                result.append(pkg)

        return result
