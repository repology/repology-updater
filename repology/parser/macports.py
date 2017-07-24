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

import json
import os
import subprocess

import repology.config

from repology.package import Package
from repology.util import SplitPackageNameVersion


def SanitizeVersion(version):
    origversion = version

    pos = version.rfind('+')
    if pos != -1:
        version = version[0:pos]

    if version != origversion:
        return version, origversion
    else:
        return version, None


class MacPortsParser():
    def __init__(self):
        self.helperpath = os.path.join(repology.config.HELPERS_DIR, 'portindex2json', 'portindex2json.tcl')
        pass

    def Parse(self, path):
        result = []

        with subprocess.Popen(
            [repology.config.TCLSH, self.helperpath, path],
            errors='ignore',
            stdout=subprocess.PIPE,
            universal_newlines=True
        ) as macportsjson:
            for pkgdata in json.load(macportsjson.stdout):
                pkg = Package()

                pkg.name = pkgdata['name']
                pkg.version = pkgdata['version']

                # drop obsolete ports (see #235)
                if 'replaced_by' in pkgdata:
                    continue

                if 'description' in pkgdata:
                    pkg.comment = pkgdata['description']

                if 'homepage' in pkgdata:
                    pkg.homepage = pkgdata['homepage']

                if 'categories' in pkgdata:
                    pkg.category = pkgdata['categories'].split()[0]

                if 'license' in pkgdata:
                    pkg.licenses = [pkgdata['license']]  # XXX: properly handle braces

                if 'maintainers' in pkgdata:
                    for maintainer in pkgdata['maintainers'].replace('{', '').replace('}', '').lower().split():
                        if maintainer.startswith('@'):
                            # @foo means github user foo
                            pkg.maintainers.append(maintainer[1:] + '@github')
                        elif '@' in maintainer:
                            # plain email
                            pkg.maintainers.append(maintainer)
                        elif ':' in maintainer:
                            # foo.com:bar means bar@foo.com
                            host, user = maintainer.split(':', 1)
                            pkg.maintainers.append(user + '@' + host)
                        elif maintainer == 'openmaintainer':
                            # ignore, this is a flag that minor changes to a port
                            # are allowed without involving the maintainer
                            pass
                        else:
                            # otherwise it's username@macports.org
                            pkg.maintainers.append(maintainer + '@macports.org')

                pkg.extrafields['portdir'] = pkgdata['portdir']
                pkg.extrafields['portname'] = pkgdata['portdir'].split('/')[1]

                result.append(pkg)

        return result
