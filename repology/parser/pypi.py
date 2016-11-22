# Copyright (C) 2016 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
import xml.etree.ElementTree
import html.parser

from ..package import Package


class PyPiHTMLParser():
    def __init__(self):
        pass

    def Parse(self, path):
        packages = {}

        with open(path, "r", encoding="utf-8") as htmlfile:
            for match in re.findall("<td><a href=\"/pypi/([^\"]+)/([^\"]+)\">[^<>]*</a></td>[ \n]*<td>([^<>]*)</td>", htmlfile.read(), flags=re.MULTILINE):
                pkg = Package()
                pkg.name = match[0]
                pkg.version = match[1]
                pkg.comment = match[2]

                packages[pkg.name] = pkg

        return [package for package in packages.values()]
