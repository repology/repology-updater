# Copyright (C) 2016 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
import xml.etree.ElementTree

from repology.version import VersionCompare
from repology.package import Package
from repology.util import GetMaintainers


def SanitizeVersion(version):
    origversion = version

    pos = version.find('-')
    if pos != -1:
        version = version[0:pos]

    pos = version.find('_')
    if pos != -1:
        version = version[0:pos]

    if version != origversion:
        return version, origversion
    else:
        return version, None


def IsBetterVersion(version, maxversion):
    # if we have no best version, take any
    if maxversion is None:
        return True

    # prefer version without 9999 to version with 9999
    if version.endswith("9999") == maxversion.endswith("9999"):
        return VersionCompare(version, maxversion) > 0

    return not version.endswith("9999")


class GentooGitParser():
    def __init__(self):
        pass

    def Parse(self, path):
        result = []

        for category in os.listdir(path):
            category_path = os.path.join(path, category)
            if not os.path.isdir(category_path):
                continue
            if category == 'virtual':
                continue

            for package in os.listdir(category_path):
                package_path = os.path.join(category_path, package)
                if not os.path.isdir(package_path):
                    continue

                metadata_path = os.path.join(package_path, "metadata.xml")

                pkg = Package()

                if os.path.isfile(metadata_path):
                    with open(os.path.join(package_path, "metadata.xml"), 'r', encoding='utf-8') as metafile:
                        meta = xml.etree.ElementTree.parse(metafile)

                        for entry in meta.findall("maintainer"):
                            name_node = entry.find("name")
                            email_node = entry.find("email")

                            if email_node is not None:
                                pkg.maintainers += GetMaintainers(email_node.text)

                maxorigversion = None
                maxversion = None
                for ebuild in os.listdir(package_path):
                    if not ebuild.endswith(".ebuild"):
                        continue

                    version, origversion = SanitizeVersion(ebuild[len(package)+1:-7])

                    if IsBetterVersion(version, maxversion):
                        maxorigversion = origversion
                        maxversion = version

                if maxversion is not None:
                    pkg.name = package
                    pkg.version = maxversion
                    pkg.origversion = maxorigversion
                    pkg.category = category

                    result.append(pkg)

        return result
