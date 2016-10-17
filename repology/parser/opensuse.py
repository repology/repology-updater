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

from ..package import Package


class OpenSUSERepodataParser():
    def __init__(self):
        pass

    def Parse(self, path):
        result = []

        root = xml.etree.ElementTree.parse(path)

        for entry in root.findall("{http://linux.duke.edu/metadata/common}package"):
            pkg = Package()

            pkg.name = entry.find("{http://linux.duke.edu/metadata/common}name").text
            pkg.fullversion = entry.find("{http://linux.duke.edu/metadata/common}version").attrib['ver']
            pkg.version = pkg.fullversion
            pkg.comment = entry.find("{http://linux.duke.edu/metadata/common}summary").text
            pkg.homepage = entry.find("{http://linux.duke.edu/metadata/common}url").text
            pkg.category = entry.find("{http://linux.duke.edu/metadata/common}format/"
                                      "{http://linux.duke.edu/metadata/rpm}group").text
            pkg.licenses.append(entry.find("{http://linux.duke.edu/metadata/common}format/"
                                           "{http://linux.duke.edu/metadata/rpm}license").text)

            result.append(pkg)

        return result
