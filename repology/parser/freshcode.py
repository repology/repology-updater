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

import json
import os

from repology.package import Package


class FreshcodeParser():
    def __init__(self):
        pass

    def Parse(self, path):
        result = []

        # note that we actually parse database prepared by
        # fetcher, not the file we've downloaded
        with open(path, 'r', encoding='utf-8') as jsonfile:
            for entry in json.load(jsonfile).values():
                pkg = Package()

                pkg.name = entry['name']
                pkg.version = entry['version']
                pkg.homepage = entry['homepage']
                pkg.comment = entry['description']

                result.append(pkg)

        return result
