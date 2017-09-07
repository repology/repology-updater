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

import json
#import os
#import re
#import sys

from repology.package import Package
#from repology.util import GetMaintainers


class HomebrewJsonParser():
    def __init__(self):
        pass

    def Parse(self, path):
        result = []

        with open(path, 'r', encoding='utf-8') as jsonfile:
            for package in json.load(jsonfile):
                pkg = Package()

                pkg.name = package['name']
                atpos = pkg.name.find('@')
                if atpos != -1:
                    pkg.name = pkg.name[:atpos]
                pkg.version = package['versions']['stable']
                pkg.comment = package['desc']
                pkg.homepage = package['homepage']

                if pkg.name and pkg.version:
                    result.append(pkg)

        return result
