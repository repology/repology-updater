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
from pkg_resources import parse_version

from ..util import VersionCompare
from ..package import Package

def SanitizeVersion(version):
    pos = version.find('-')
    if pos != -1:
        version = version[0:pos]

    pos = version.find('_')
    if pos != -1:
        version = version[0:pos]

    return version

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

                maxversion = None
                bestebuild = None
                for ebuild in os.listdir(package_path):
                    if not ebuild.endswith(".ebuild"):
                        continue
                    ebuild_path = os.path.join(package_path, ebuild)

                    version = ebuild[len(package)+1:-7]

                    if IsBetterVersion(version, maxversion):
                        maxversion = version
                        bestebuild = ebuild

                if not maxversion is None:
                    pkg = Package()
                    pkg.name = package
                    pkg.fullversion = maxversion
                    pkg.version = SanitizeVersion(pkg.fullversion)
                    pkg.category = category

                    result.append(pkg)

        return result
