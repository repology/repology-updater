# Copyright (C) 2017 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import sys
import xml.etree.ElementTree

from repology.package import Package


class RosaInfoXmlParser():
    def __init__(self):
        pass

    def Parse(self, path):
        result = []

        root = xml.etree.ElementTree.parse(path)

        for info in root.findall('./info'):
            pkg = Package()

            fn = info.attrib['fn'].rsplit('-', 2)
            if len(fn) < 3:
                print('WARNING: unable to parse fn: {}'.format(fn), file=sys.stderr)
                continue

            pkg.name = fn[0]
            pkg.origversion = '-'.join(fn[1:])
            pkg.version = fn[1]

            url = info.attrib['url']
            if url:
                pkg.homepage = url

            license_ = info.attrib['license']
            pkg.licenses = [license_]

            result.append(pkg)

        return result
