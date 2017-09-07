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

import xml.etree.ElementTree

from repology.package import Package


class FDroidParser():
    def __init__(self):
        pass

    def Parse(self, path):
        result = []

        root = xml.etree.ElementTree.parse(path)

        for application in root.findall('application'):
            pkg = Package()
            pkg.name = application.find('name').text
            pkg.version = application.find('marketversion').text
            pkg.licenses.append(application.find('license').text)
            pkg.category = application.find('category').text

            www = application.find('web').text

            if www:
                pkg.homepage = www

            pkg.extrafields['id'] = application.find('id').text

            if pkg.name and pkg.version:
                result.append(pkg)

        return result
