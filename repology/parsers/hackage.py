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
import re
import sys

from repology.package import Package
from repology.version import VersionCompare


class HackageParser():
    def __init__(self):
        pass

    def ParseCabal(self, path):
        cabaldata = {}
        offset = None
        key = None

        with open(path) as cabalfile:
            for line in cabalfile:
                line = line.rstrip()

                # offset is needed to be calculated first, from first non-whitespace line
                if offset is None:
                    match = re.match('([ ]*)[^ ]', line)
                    if match:
                        offset = len(match.group(1))
                    else:
                        continue

                line = line[offset:]

                # ignore comments
                if line.startswith('--'):
                    continue

                # process multiline keys
                if key:
                    if line.startswith(' '):
                        cabaldata[key] = cabaldata[key] + ' ' + line.strip() if key in cabaldata else line.strip()
                        continue
                    else:
                        key = None

                # process singleline key or start of a multiline key
                match = re.fullmatch('([a-zA-Z-]+)[ \t]*:[ \t]*(.*?)', line)
                if not match:
                    continue

                if match.group(2):
                    cabaldata[match.group(1).lower()] = match.group(2)
                else:
                    key = match.group(1).lower()

        return cabaldata

    def Parse(self, path):
        packages = []

        for moduledir in os.listdir(path):
            modulepath = os.path.join(path, moduledir)

            cabalpath = None
            maxversion = None

            for versiondir in os.listdir(modulepath):
                if versiondir == 'preferred-versions':
                    continue

                if maxversion is None or VersionCompare(versiondir, maxversion) > 0:
                    maxversion = versiondir
                    cabalpath = os.path.join(path, moduledir, maxversion, moduledir + '.cabal')

            pkg = Package()

            pkg.name = moduledir
            pkg.version = maxversion
            pkg.homepage = 'http://hackage.haskell.org/package/' + moduledir

            cabaldata = self.ParseCabal(cabalpath)

            if cabaldata['name'] == pkg.name and VersionCompare(cabaldata['version'], pkg.version) == 0:
                if 'synopsis' in cabaldata and cabaldata['synopsis']:
                    pkg.comment = cabaldata['synopsis'].strip()
                # XXX: leave for later, need extra postprocessing, too much obfuscation
                #if 'maintainer' in cabaldata:
                #    pkg.maintainers = GetMaintainers(cabaldata['maintainer'])
                if 'license' in cabaldata:
                    pkg.licenses = [cabaldata['license']]
                if 'homepage' in cabaldata and (cabaldata['homepage'].startswith('http://') or cabaldata['homepage'].startswith('https://')):
                    pkg.homepage = cabaldata['homepage']
                if 'category' in cabaldata:
                    pkg.category = cabaldata['category']
            else:
                print('WARNING: cabal data sanity check failed for {}, ignoring cabal data'.format(cabalpath), file=sys.stderr)

            packages.append(pkg)

        return packages
