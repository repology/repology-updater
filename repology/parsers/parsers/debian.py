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

from repology.logger import Logger
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers


def SanitizeVersion(version):
    origversion = version

    # epoch
    pos = version.find(':')
    if pos != -1:
        version = version[pos + 1:]

    # revision
    pos = version.rfind('-')
    if pos != -1:
        version = version[0:pos]

    # garbage debian/ubuntu addendums
    version = re.sub('[.~+-]?(dfsg|ubuntu|mx).*', '', version, re.IGNORECASE)

    # remove suffixes
    version, *suffixes = re.split('[~+-]', version)

    # append useful suffixes
    good_suffixes = []
    for suffix in suffixes:
        match = re.match('((?:a|b|r|alpha|beta|rc|rcgit|pre|patch|git|svn|cvs|hg|bzr|nmu|darcs|dev)[.-]?[0-9]+(?:\\.[0-9]+)*|(?:alpha|beta|rc))', suffix, re.IGNORECASE)
        if match:
            good_suffixes.append(match.group(1))

    version += '.'.join(good_suffixes)

    if version != origversion:
        return version, origversion
    else:
        return version, None


class DebianSourcesParser(Parser):
    def iter_parse(self, path, factory):
        with open(path, encoding='utf-8', errors='ignore') as file:
            current_data = {}
            last_key = None

            for line in file:
                line = line.rstrip('\n')

                # empty line, dump package
                if line == '':
                    if not current_data:
                        continue  # may happen on empty package list

                    pkg = factory.begin()

                    def GetField(key, type_=str, default=None):
                        if key in current_data:
                            if type_ is None or isinstance(current_data[key], type_):
                                return current_data[key]
                            else:
                                factory.log('unable to parse field {}'.format(key), severity=Logger.ERROR)
                                return default
                        else:
                            return default

                    pkg.name = GetField('Package')
                    pkg.version, pkg.origversion = SanitizeVersion(GetField('Version'))
                    pkg.maintainers += extract_maintainers(GetField('Maintainer', default=''))
                    pkg.maintainers += extract_maintainers(GetField('Uploaders', default=''))
                    pkg.category = GetField('Section')
                    pkg.homepage = GetField('Homepage')

                    # This is long description
                    #pkg.comment = GetField('Description', type_=None)
                    #if isinstance(pkg.comment, list):
                    #    pkg.comment = ' '.join(pkg.comment)

                    if pkg.name and pkg.version:
                        yield pkg
                    else:
                        factory.log('unable to parse package {}'.format(str(current_data)), severity=Logger.ERROR)

                    current_data = {}
                    last_key = None
                    continue

                # key - value pair
                match = re.fullmatch('([A-Za-z0-9-]+):(.*?)', line)
                if match:
                    key = match.group(1)
                    value = match.group(2).strip()
                    current_data[key] = value
                    last_key = key
                    continue

                # continuation of previous key
                match = re.fullmatch(' (.*)', line)
                if match:
                    value = match.group(1).strip()
                    if not isinstance(current_data[last_key], list):
                        current_data[last_key] = [current_data[last_key]]
                    current_data[last_key].append(value)
                    continue

                factory.log('unable to parse line: {}'.format(line), severity=Logger.ERROR)
