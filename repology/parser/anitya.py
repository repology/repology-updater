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
import os
import re
import sys

from repology.package import Package
from repology.util import GetMaintainers


class AnityaApiParser():
    def __init__(self):
        pass

    def Parse(self, path):
        result = []

        with open(path, 'r', encoding='utf-8') as jsonfile:
            for project in json.load(jsonfile)['projects']:
                pkg = Package()

                pkg.name = project['name']
                pkg.version = project['version']
                pkg.homepage = project['homepage']

                if pkg.version is None:
                    print('no version: {}'.format(pkg.name), file=sys.stderr)
                    continue

                if pkg.version.startswith('v'):
                    pkg.version = pkg.version[1:]

                if project['backend'] == 'CPAN (perl)':
                    pkg.name = 'perl:' + pkg.name
                elif project['backend'] == 'Rubygems':
                    pkg.name = 'ruby:' + pkg.name

                result.append(pkg)

        return result
