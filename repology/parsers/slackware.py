# Copyright (C) 2016 Dmitry Marakasov <amdmi3@amdmi3.ru>
# Copyright (C) 2017 David Spencer <idlemoor@slackbuilds.org>
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

import re
import sys

from repology.package import Package


class SlackwareParser():
    def __init__(self):
        pass

# pylint: disable=R0201
    def Parse(self, path):
        result = []

        # Look for packages in these subrepositories:
        subrepolist = ['slackware', 'slackware64', 'patches', 'extra']
        # Everything else is ignored.

        with open(path, 'r') as filelisttxt:
            for line in filelisttxt.readlines():
                components = line.strip().split('/')
                if len(components) < 4:
                    # ignore lines that are not deep enough in the hierarchy (containing dirs etc)
                    continue
                topdir = components[1]
                if topdir not in subrepolist:
                    continue
                basename = components[-1]
                if re.search('\.t.z$', basename):
                    parsedbasename = basename.rsplit('-', 3)
                    if len(parsedbasename) != 4:
                        print('WARNING: unable to parse package name {}'.format(basename), file=sys.stderr)
                        continue

                    pkg = Package()
                    pkg.name = parsedbasename[0]
                    pkg.version = parsedbasename[1]
                    pkg.subrepo = topdir
                    if pkg.subrepo == 'patches' or pkg.subrepo == 'extra':
                        pkg.category = pkg.subrepo
                        pkg.extrafields['sourcedir'] = '{}/source/{}'.format(pkg.category, pkg.name)
                    else:
                        pkg.category = components[2]
                        pkg.extrafields['sourcedir'] = 'source/{}/{}'.format(pkg.category, pkg.name)
                    result.append(pkg)

        return result
