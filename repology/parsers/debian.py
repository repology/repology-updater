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

import re
import sys

from repology.package import Package
from repology.util import GetMaintainers


def SanitizeVersion(version):
    origversion = version

    pos = version.find(':')
    if pos != -1:
        version = version[pos + 1:]

    pos = version.find('-')
    if pos != -1:
        version = version[0:pos]

    pos = version.find('+')
    if pos != -1:
        version = version[0:pos]

    pos = version.find('~')
    if pos != -1:
        version = version[0:pos]

    match = re.match('(.*[0-9])[^0-9]*dfsg\\.?[0-9]*$', version)
    if match is not None:
        version = match.group(1)

    match = re.match('(.*[0-9])ubuntu[0-9.]+$', version)
    if match is not None:
        version = match.group(1)

    if version != origversion:
        return version, origversion
    else:
        return version, None


class DebianSourcesParser():
    def __init__(self):
        pass

    def Parse(self, path):
        result = []

        with open(path, encoding='utf-8') as file:
            current_data = {}
            last_key = None

            for line in file:
                line = line.rstrip('\n')

                # empty line, dump package
                if line == '':
                    pkg = Package()

                    def GetField(key, type_=str, default=None):
                        if key in current_data:
                            if type_ is None or isinstance(current_data[key], type_):
                                return current_data[key]
                            else:
                                print('WARNING: unable to parse field {}'.format(key), file=sys.stderr)
                                return default
                        else:
                            return default

                    pkg.name = GetField('Package')
                    pkg.version, pkg.origversion = SanitizeVersion(GetField('Version'))
                    pkg.maintainers += GetMaintainers(GetField('Maintainer', default=''))
                    pkg.maintainers += GetMaintainers(GetField('Uploaders', default=''))
                    pkg.category = GetField('Section')
                    pkg.homepage = GetField('Homepage')

                    # This is long description
                    #pkg.comment = GetField('Description', type_=None)
                    #if isinstance(pkg.comment, list):
                    #    pkg.comment = ' '.join(pkg.comment)

                    if pkg.name and pkg.version:
                        result.append(pkg)
                    else:
                        print('WARNING: unable to parse package {}'.format(str(current_data)), file=sys.stderr)

                    current_data = {}
                    last_key = None
                    continue

                # key - value pair
                match = re.match('([A-Za-z0-9-]+):(.*?)$', line)
                if match:
                    key = match.group(1)
                    value = match.group(2).strip()
                    current_data[key] = value
                    last_key = key
                    continue

                # continuation of previous key
                match = re.match(' (.*)$', line)
                if match:
                    value = match.group(1).strip()
                    if not isinstance(current_data[last_key], list):
                        current_data[last_key] = [current_data[last_key]]
                    current_data[last_key].append(value)
                    continue

                print('WARNING: unable to parse line: {}'.format(line), file=sys.stderr)

        return result
