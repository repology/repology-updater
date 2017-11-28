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
import plistlib

from repology.package import Package


def parse_maintainer(maintainerstr):
    if not maintainerstr:
        return []
    return [maintainerstr.split()[-1].lstrip('<').rstrip('>')]


class VoidLinuxParser():

    def __init__(self):
        pass

    def Parse(self, path):
        index_path = os.path.join(path, 'index.plist')
        plist_index = plistlib.load(open(index_path, 'rb'),
                                    fmt=plistlib.FMT_XML)

        return [Package(name=pkgname,
                        version=props['pkgver'].split('-')[-1].replace('_', '-'),
                        maintainers=parse_maintainer(props.get('maintainer')),
                        comment=props['short_desc'],
                        homepage=props['homepage'],
                        licenses=[l.strip() for l in props['license'].split(',')])
                for pkgname, props in plist_index.items()]
