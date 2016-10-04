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
import subprocess

from ..package import Package

class SrcListClassicParser():
    def __init__(self):
        pass

    def Parse(self, path):
        result = []

        with subprocess.Popen(["/tmp/pkglist-query", "%{name}|%{version}|%{packager}\\n", path], stdout = subprocess.PIPE, universal_newlines = True) as proc:
            for line in proc.stdout:
                fields = line.split('|')

                pkg = Package()

                pkg.name = fields[0]
                pkg.version = fields[1]
                pkg.maintainer = fields[2].strip()

                result.append(pkg)

        return result
