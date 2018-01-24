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

import sys
import xml.etree.ElementTree

from repology.package import Package
from repology.util import GetMaintainers


def SanitizeVersion(version):
    origversion = version

    pos = version.find('+')
    if pos != -1:
        version = version[:pos]

    if version != origversion:
        return version, origversion
    else:
        return version, None


class RepodataParser():
    def __init__(self, allowed_archs=None):
        self.allowed_archs = allowed_archs

    def ParsePackagesEntriesFromXml(self, path):
        """Return all <package> elements from XML.

        The purpose is to clear the element after processing, so
        processed elements don't fill up the memory
        """
        for _, elem in xml.etree.ElementTree.iterparse(path):
            if elem.tag == '{http://linux.duke.edu/metadata/common}package':
                yield elem
                elem.clear()

    def Parse(self, path):
        result = []
        skipped_archs = {}

        for entry in self.ParsePackagesEntriesFromXml(path):
            pkg = Package()

            arch = entry.find('{http://linux.duke.edu/metadata/common}arch').text
            if self.allowed_archs and arch not in self.allowed_archs:
                skipped_archs[arch] = skipped_archs.get(arch, 0) + 1
                continue

            pkg.name = entry.find('{http://linux.duke.edu/metadata/common}name').text
            version = entry.find('{http://linux.duke.edu/metadata/common}version').attrib['ver']
            pkg.version, pkg.origversion = SanitizeVersion(version)
            pkg.comment = entry.find('{http://linux.duke.edu/metadata/common}summary').text
            pkg.homepage = entry.find('{http://linux.duke.edu/metadata/common}url').text
            pkg.category = entry.find('{http://linux.duke.edu/metadata/common}format/'
                                      '{http://linux.duke.edu/metadata/rpm}group').text
            pkg.licenses.append(entry.find('{http://linux.duke.edu/metadata/common}format/'
                                           '{http://linux.duke.edu/metadata/rpm}license').text)

            packager = entry.find('{http://linux.duke.edu/metadata/common}packager').text
            if packager:
                pkg.maintainers = GetMaintainers(packager)

            result.append(pkg)

        for arch, numpackages in sorted(skipped_archs.items()):
            print('WARNING: skipping {} packages(s) with disallowed architecture {}'.format(numpackages, arch), file=sys.stderr)

        return result
