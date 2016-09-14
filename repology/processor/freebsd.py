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
import csv
import subprocess

from .common import RepositoryProcessor
from ..util import SplitPackageNameVersion
from ..package import Package

def SanitizeVersion(version):
    pos = version.rfind(',')
    if pos != -1:
        version = version[0:pos]

    pos = version.rfind('_')

    if pos != -1:
        version = version[0:pos]

    return version

class FreeBSDIndexProcessor(RepositoryProcessor):
    def __init__(self, path, src):
        self.path = path
        self.src = src

    def IsUpToDate(self):
        return False

    def Download(self, update = True):
        if os.path.isfile(self.path) and not update:
            return
        subprocess.check_call("wget -qO- %s | bunzip2 > %s" % (self.src, self.path), shell = True)

    def Parse(self):
        result = []

        with open(self.path) as file:
            reader = csv.reader(file, delimiter='|')
            for row in reader:
                pkg = Package()

                pkg.name, pkg.fullversion = SplitPackageNameVersion(row[0])
                pkg.version = SanitizeVersion(pkg.fullversion)
                pkg.comment = row[3]
                pkg.maintainer = row[5]
                pkg.category = row[6].split(' ')[0]

                result.append(pkg)

        return result
