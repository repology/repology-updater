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
import sys
import json

from ..package import Package


def SanitizeVersion(version):
    pos = version.find('-')
    if pos != -1:
        version = version[0:pos]

    pos = version.find(':')
    if pos != -1:
        version = version[pos+1:]

    pos = version.find('+')
    if pos != -1:
        version = version[pos+1:]

    return version


class AURParser():
    def __init__(self):
        pass

    def Parse(self, path):
        packages = []

        for filename in os.listdir(path):
            if not filename.endswith(".json"):
                continue

            with open(os.path.join(path, filename), "r") as jsonfile:
                for result in json.load(jsonfile)["results"]:
                    pkg = Package()

                    pkg.name = result["Name"]

                    has_badsuffix = False
                    for badsuffix in ["-cvs", "-svn", "-hg", "-darcs", "-bzr", "-git", "-bin"]:
                        if pkg.name.endswith(badsuffix):
                            has_badsuffix = True
                            break

                    if has_badsuffix:
                        continue

                    pkg.fullversion = result["Version"]
                    pkg.version = SanitizeVersion(pkg.fullversion)
                    pkg.comment = result["Description"]
                    pkg.homepage = result["URL"]

                    if "License" in result:
                        for license in result["License"]:
                            pkg.licenses.append(license)

                    if "Maintainer" in result and result["Maintainer"]:
                        pkg.maintainer = result["Maintainer"] + "@aur"

                    packages.append(pkg)

        return packages
