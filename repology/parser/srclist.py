# Copyright (C) 2016-2017 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import repology.config

from repology.package import Package
from repology.util import GetMaintainers


class SrcListParser():
    def __init__(self):
        self.helperpath = os.path.join(repology.config.HELPERS_DIR, 'rpmcat', 'rpmcat')

        if not os.path.exists(self.helperpath):
            raise RuntimeError('{} does not exist, please run `make\' in project root directory to build it'.format(self.helperpath))

    def Parse(self, path):
        result = []

        with subprocess.Popen([self.helperpath, path], errors='ignore', stdout=subprocess.PIPE, universal_newlines=True) as proc:
            for line in proc.stdout:
                fields = line.strip().split('|')

                pkg = Package()

                pkg.name = fields[0]
                pkg.version = fields[1]
                pkg.maintainers = GetMaintainers(fields[2])  # XXX: may have multiple maintainers
                pkg.category = fields[3]
                pkg.comment = fields[4]

                result.append(pkg)

        return result
