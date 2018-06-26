# Copyright (C) 2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import lxml.html

from repology.package import Package


class SophieHTMLParser():
    def __init__(self):
        pass

    def Parse(self, path):
        result = []

        for item in lxml.html.parse(path).getroot().xpath('.//div[@id="rpms_list"]/ul/li/a'):
            rpminfo, arch, ext = item.text.rsplit('.', 2)

            name, versioninfo, revision = rpminfo.rsplit('-', 2)

            version = versioninfo.rsplit(':', 2)[-1]

            pkg = Package()

            pkg.name = name
            pkg.version = version

            result.append(pkg)

        return result
