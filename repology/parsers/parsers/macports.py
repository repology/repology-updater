# Copyright (C) 2016-2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from repology.config import config
from repology.parsers import Parser
from repology.parsers.versions import VersionStripper


class MacPortsParser(Parser):
    def __init__(self):
        self.helperpath = os.path.join(config['HELPERS_DIR'], 'portindex2json', 'portindex2json.tcl')

    def iter_parse(self, path, factory, transformer):
        normalize_version = VersionStripper().strip_right('+')

        with subprocess.Popen(
            [config['TCLSH'], self.helperpath, path],
            errors='ignore',
            stdout=subprocess.PIPE,
            universal_newlines=True
        ) as macportsjson:
            for pkgdata in json.load(macportsjson.stdout):
                pkg = factory.begin()

                pkg.set_name(pkgdata['name'])
                pkg.set_version(pkgdata['version'], normalize_version)

                # drop obsolete ports (see #235)
                if 'replaced_by' in pkgdata:
                    continue

                pkg.set_summary(pkgdata.get('description'))
                pkg.add_homepages(pkgdata.get('homepage'))
                pkg.add_categories(pkgdata.get('categories', '').split())
                pkg.add_licenses(pkgdata.get('license'))  # XXX: properly handle braces

                if 'maintainers' in pkgdata:
                    for maintainer in pkgdata['maintainers'].replace('{', '').replace('}', '').lower().split():
                        if maintainer.startswith('@'):
                            # @foo means github user foo
                            pkg.add_maintainers(maintainer[1:] + '@github')
                        elif '@' in maintainer:
                            # plain email
                            pkg.add_maintainers(maintainer)
                        elif ':' in maintainer:
                            # foo.com:bar means bar@foo.com
                            # ignore, since it's considered a form of email obfuscation
                            pass
                        elif maintainer == 'openmaintainer':
                            # ignore, this is a flag that minor changes to a port
                            # are allowed without involving the maintainer
                            pass
                        else:
                            # otherwise it's username@macports.org
                            pkg.add_maintainers(maintainer + '@macports.org')

                pkg.set_extra_field('portdir', pkgdata['portdir'])
                pkg.set_extra_field('portname', pkgdata['portdir'].split('/')[1])

                yield pkg
