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

import re
import xml.etree.ElementTree

from repology.package import PackageFlags
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers
from repology.parsers.nevra import nevra_construct
from repology.parsers.versions import VersionStripper


def _iter_package_entries(path):
    """Return all <package> elements from XML.

    The purpose is to clear the element after processing, so
    processed elements don't fill up the memory
    """
    for _, elem in xml.etree.ElementTree.iterparse(path):
        if elem.tag == '{http://linux.duke.edu/metadata/common}package':
            yield elem
            elem.clear()


class RepodataParser(Parser):
    def __init__(self, allowed_archs=None):
        self.allowed_archs = allowed_archs

    def iter_parse(self, path, factory, transformer):
        normalize_version = VersionStripper().strip_right_greedy('+')

        skipped_archs = {}

        for entry in _iter_package_entries(path):
            pkg = factory.begin()

            arch = entry.find('{http://linux.duke.edu/metadata/common}arch').text
            if self.allowed_archs and arch not in self.allowed_archs:
                skipped_archs[arch] = skipped_archs.get(arch, 0) + 1
                continue

            pkg.set_name(entry.find('{http://linux.duke.edu/metadata/common}name').text)
            epoch = entry.find('{http://linux.duke.edu/metadata/common}version').attrib['epoch']
            version = entry.find('{http://linux.duke.edu/metadata/common}version').attrib['ver']
            release = entry.find('{http://linux.duke.edu/metadata/common}version').attrib['rel']

            match = re.match('0\\.[0-9]+\\.((?:alpha|beta|rc)[0-9]+)\\.', release)
            if match:
                # known pre-release schema: https://fedoraproject.org/wiki/Packaging:Versioning#Prerelease_versions
                version += '-' + match.group(1)
            elif release < '1':
                # unknown pre-release schema: https://fedoraproject.org/wiki/Packaging:Versioning#Some_definitions
                # most likely a snapshot
                pkg.set_flags(PackageFlags.ignore)

            pkg.set_version(version, normalize_version)
            pkg.set_rawversion(nevra_construct(None, epoch, version, release))

            pkg.set_summary(entry.find('{http://linux.duke.edu/metadata/common}summary').text)
            pkg.add_homepages(entry.find('{http://linux.duke.edu/metadata/common}url').text)
            pkg.add_categories(entry.find('{http://linux.duke.edu/metadata/common}format/'
                                          '{http://linux.duke.edu/metadata/rpm}group').text)
            pkg.add_licenses(entry.find('{http://linux.duke.edu/metadata/common}format/'
                                        '{http://linux.duke.edu/metadata/rpm}license').text)

            packager = entry.find('{http://linux.duke.edu/metadata/common}packager').text
            if packager:
                pkg.add_maintainers(extract_maintainers(packager))

            yield pkg

        for arch, numpackages in sorted(skipped_archs.items()):
            factory.log('skipped {} packages(s) with disallowed architecture {}'.format(numpackages, arch))
