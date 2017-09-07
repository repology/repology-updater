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
import shlex
import sys

from repology.package import Package


class OpenIndianaSummaryJsonParser():
    def __init__(self):
        pass

    def ParsePackage(self, pkgpath, pkgdata):
        variables = {}
        for action in pkgdata['actions']:
            tokens = shlex.split(action)

            if not tokens or tokens.pop(0) != 'set':
                print('WARNING: unrecognized action ' + action, file=sys.stderr)
                continue

            key = None
            value = []

            for token in tokens:
                if token.startswith('name='):
                    key = token[5:]
                elif token.startswith('value='):
                    value.append(token[6:])
                elif token.startswith('last-fmri='):
                    pass
                else:
                    print('WARNING: unrecognized token ' + token, file=sys.stderr)
                    continue

            if key and value:
                variables[key] = value

        pkg = Package()

        if 'com.oracle.info.name' in variables:
            pkg.name = variables['com.oracle.info.name'][0]

        if 'com.oracle.info.version' in variables:
            pkg.version = variables['com.oracle.info.version'][0]

        if 'pkg.summary' in variables:
            pkg.comment = variables['pkg.summary'][0]

        if 'info.classification' in variables:
            pkg.category = variables['info.classification'][0]
            if pkg.category.startswith('org.opensolaris.category.2008:'):
                pkg.category = pkg.category.split(':', 1)[1]

        if 'info.upstream-url' in variables:
            pkg.homepage = variables['info.upstream-url'][0]

        if 'info.source-url' in variables:
            pkg.downloads = variables['info.source-url']

        if pkg.name and pkg.version:
            return pkg

        return None

    def Parse(self, path):
        result = []

        with open(path, 'r', encoding='utf-8') as jsonfile:
            summary_json = json.load(jsonfile)

            for summary_key in summary_json.keys():
                if summary_key.startswith('_'):  # _SIGNATURE
                    continue

                # else summary_key is someting like "openindiana.org"
                # or "hipster-encumbered"

                for pkgpath, pkgdatas in summary_json[summary_key].items():
                    for pkgdata in pkgdatas:
                        pkg = self.ParsePackage(pkgpath, pkgdata)

                        if pkg:
                            result.append(pkg)

        return result
