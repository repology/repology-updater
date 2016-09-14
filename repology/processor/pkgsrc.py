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
import re
import subprocess
import sys

from .common import RepositoryProcessor
from ..util import SplitPackageNameVersion
from ..package import Package

def SanitizeVersion(version):
    match = re.match("(.*)nb[0-9]+", version)
    if not match is None:
        version = match.group(1)

    return version

class PkgSrcPackagesSHA512Processor(RepositoryProcessor):
    def __init__(self, path, src):
        self.path = path
        self.src = src

    def GetRepoType(self):
        return 'pkgsrc'

    def IsUpToDate(self):
        return False

    def Download(self, update = True):
        if os.path.isfile(self.path) and not update:
            return
        subprocess.check_call("wget -qO- %s | bunzip2 > %s" % (self.src, self.path), shell = True)

    def Parse(self):
        result = []

        with open(self.path) as file:
            pkg = Package()
            for line in file:
                pkgname = line[12:-137]

                if pkgname.find('-') == -1:
                    continue

                pkg.name, pkg.fullversion = SplitPackageNameVersion(pkgname)
                pkg.version = SanitizeVersion(pkg.fullversion)

                result.append(pkg)
                pkg = Package()

        return result
