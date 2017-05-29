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

import json
import os
import re
import sys

from repology.package import Package
from repology.util import GetMaintainers


def ExtractLicenses(whatever):
    if isinstance(whatever, str):
        return [whatever]
    elif isinstance(whatever, list):
        return sum(map(ExtractLicenses, whatever), [])
    elif isinstance(whatever, dict) and 'spdxId' in whatever:
        return [whatever['spdxId']]
    elif isinstance(whatever, dict) and 'fullName' in whatever:
        return [whatever['fullName']]
    elif isinstance(whatever, dict) and 'fullname' in whatever:
        return [whatever['fullname']]
    else:
        raise RuntimeError('unparsable license info')


class NixJsonParser():
    def __init__(self):
        pass

    def Parse(self, path):
        result = []

        with open(path, 'r', encoding='utf-8') as jsonfile:
            for key, packagedata in sorted(json.load(jsonfile)['packages'].items()):
                # see how Nix parses 'derivative' names in
                # https://github.com/NixOS src/libexpr/names.cc, DrvName::DrvName
                # it just splits on dash followed by non-letter
                #
                # this doesn't work well on 100% cases, it's an upstream problem
                match = re.match('(.+?)-([^a-zA-Z].*)$', packagedata['name'])
                if not match:
                    print('cannot extract version: {}/{}'.format(key, packagedata['name']), file=sys.stderr)
                    continue

                pkg = Package()
                pkg.name = match.group(1)
                pkg.version = match.group(2)

                # some exceptions
                for prefix in ('75dpi', '100dpi'):
                    if pkg.version.startswith(prefix):
                        pkg.name += '-' + prefix
                        pkg.version = pkg.version[len(prefix) + 1:]

                for pkgname in ('liblqr', ):
                    if pkg.name == pkgname:
                        dashpos = pkg.version.find('-')
                        pkg.name = pkg.name + '-' + pkg.version[0:dashpos]
                        pkg.version = pkg.version[dashpos + 1:]

                if pkg.name.endswith('-git'):
                    pkg.name = pkg.name[:-4]
                    print('ignoring version for git snapshot: {}/{}'.format(key, packagedata['name']), file=sys.stderr)
                    pkg.ignoreversion = True

                if re.match('.*20[0-9]{2}-[0-9]{2}-[0-9]{2}', pkg.version):
                    print('ignoring version which is a date: {}/{}'.format(key, packagedata['name']), file=sys.stderr)
                    pkg.ignoreversion = True

                if re.match('[0-9a-f]*[a-f][0-9a-f]*$', pkg.version) and len(pkg.version) >= 7:
                    print('ignoring version which looks like commit hash: {}/{}'.format(key, packagedata['name']), file=sys.stderr)
                    pkg.ignoreversion = True

                meta = packagedata['meta']

                if 'homepage' in meta:
                    pkg.homepage = meta['homepage']
                    if isinstance(pkg.homepage, list):  # XXX: remove after adding support for homepages array
                        pkg.homepage = pkg.homepage[0]

                if 'description' in meta:
                    pkg.comment = meta['description']

                if 'maintainers' in meta:
                    maintainers = meta['maintainers']
                    if not isinstance(meta['maintainers'], list):
                        print('maintainers is not a list: {}/{}'.format(key, packagedata['name']), file=sys.stderr)
                    else:
                        maintainers = ', '.join(maintainers)
                    pkg.maintainers = GetMaintainers(maintainers)

                if 'license' in meta:
                    pkg.licenses = ExtractLicenses(meta['license'])

                result.append(pkg)

        return result
