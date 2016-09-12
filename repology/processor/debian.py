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

class DebianSourcesProcessor(RepositoryProcessor):
    sources = []
    path = None

    def __init__(self, path, *sources):
        self.path = path
        self.sources = sources

    def IsUpToDate(self):
        return os.path.isfile(self.path)

    def Download(self):
        if os.path.isfile(self.path):
            os.remove(self.path)
        for source in self.sources:
            subprocess.check_call("wget -qO- %s | gunzip >> %s" % (source, self.path), shell = True)

    @staticmethod
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

    def Parse(self):
        result = []

        with open(self.path) as file:
            data = {}
            for line in file:
                if line == "\n":
                    result.append(data)
                    data = {}
                elif line.startswith('Package: '):
                    data['name'] = line[9:-1]
                elif line.startswith('Version: '):
                    data['version'] = self.SanitizeVersion(line[9:-1])
                elif line.startswith('Maintainer: '):
                    data['maintainer'] = line[12:-1]
                elif line.startswith('Section: '):
                    data['category'] = line[9:-1]
                elif line.startswith('Homepage: '):
                    data['homepage'] = line[10:-1]

        return result
