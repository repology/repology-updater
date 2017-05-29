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

from repology.package import Package
from repology.version import VersionCompare


class HackageParser():
    def __init__(self):
        pass

    def Parse(self, path):
        packages = []

        for moduledir in os.listdir(path):
            modulepath = os.path.join(path, moduledir)

            maxversion = None

            for versiondir in os.listdir(modulepath):
                if versiondir == 'preferred-versions':
                    continue

                if maxversion is None or VersionCompare(versiondir, maxversion) > 0:
                    maxversion = versiondir

            pkg = Package()

            # XXX: parse .cabal file

            pkg.name = moduledir
            pkg.version = maxversion
            pkg.homepage = 'http://hackage.haskell.org/package/' + moduledir

            packages.append(pkg)

        return packages
