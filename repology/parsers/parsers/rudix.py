# Copyright (C) 2017 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
from repology.parsers import Parser


class RudixHTMLParser(Parser):
    def Parse(self, path):
        result = []

        for row in lxml.html.parse(path).getroot().xpath('.//table')[0].xpath('./tbody/tr'):
            pkg = Package()

            pkg.name = row.xpath('./td[1]/a')[0].text
            pkg.version = row.xpath('./td[2]')[0].text
            pkg.comment = row.xpath('./td[3]')[0].text
            pkg.licenses = [row.xpath('./td[4]')[0].text]

            result.append(pkg)

        return result
