# Copyright (C) 2016-2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
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


def normalize_version(version):
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

    return version


class DebianSourcesParser(Parser):
    def __init__(self, project_name_from_source=False):
        self.project_name_from_source = project_name_from_source

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

                    def get_field(key, type_=str, default=None):
                        if key in current_data:
                            if type_ is None or isinstance(current_data[key], type_):
                                return current_data[key]
                            else:
                                pkg.log('unable to parse field {}'.format(key), severity=Logger.ERROR)
                                return default
                        else:
                            return default

                    pkg.set_name(get_field('Package'))
                    pkg.set_version(get_field('Version'), normalize_version)
                    pkg.add_maintainers(extract_maintainers(get_field('Maintainer', default='')))
                    pkg.add_maintainers(extract_maintainers(get_field('Uploaders', default='')))
                    pkg.add_categories(get_field('Section'))
                    pkg.add_homepages(get_field('Homepage'))

                    # This is long description
                    #pkg.comment = get_field('Description', type_=None)
                    #if isinstance(pkg.comment, list):
                    #    pkg.set_summary(' '.join(pkg.comment))

                    source = get_field('Source')
                    if source:
                        pkg.set_extra_field('source', source)

                        # XXX: this is only used in OpenWRT ATM
                        # We assume that Source field is a package name or something path-like
                        if self.project_name_from_source:
                            srcname = source.split('/')[-1]
                            pkg.set_effname(srcname)
                            pkg.set_extra_field('srcname', srcname)

                    yield pkg

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
