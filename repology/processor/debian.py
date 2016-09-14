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

from .common import RepositoryProcessor
from ..package import Package

def SanitizeVersion(version):
    pos = version.find(':')
    if pos != -1:
        version = version[pos+1:]

    pos = version.find('-')
    if pos != -1:
        version = version[0:pos]

    pos = version.find('+')
    if pos != -1:
        version = version[0:pos]

    pos = version.find('~')
    if pos != -1:
        version = version[0:pos]

    match = re.match("(.*[0-9])[^0-9]*dfsg[0-9]*$", version)
    if not match is None:
        version = match.group(1)

    return version

class DebianSourcesProcessor(RepositoryProcessor):
    def __init__(self, path, *sources):
        self.path = path
        self.sources = sources

    def IsUpToDate(self):
        return False

    def Download(self, update = True):
        if os.path.isfile(self.path):
            if not update:
                return
            os.remove(self.path)
        for source in self.sources:
            subprocess.check_call("wget -qO- %s | gunzip >> %s" % (source, self.path), shell = True)

    def Parse(self):
        result = []

        with open(self.path, encoding='utf-8') as file:
            pkg = Package()
            for line in file:
                if line == "\n":
                    result.append(pkg)
                    pkg = Package()
                elif line.startswith('Package: '):
                    pkg.name = line[9:-1]
                elif line.startswith('Version: '):
                    pkg.fullversion = line[9:-1]
                    pkg.version = SanitizeVersion(pkg.fullversion)
                elif line.startswith('Maintainer: '):
                    pkg.maintainer = line[12:-1]
                elif line.startswith('Section: '):
                    pkg.category = line[9:-1]
                elif line.startswith('Homepage: '):
                    pkg.homepage = line[10:-1]

        return result
