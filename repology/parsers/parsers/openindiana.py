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

from repology.logger import Logger
from repology.parsers import Parser


def _iter_packages(path):
    with open(path, 'r', encoding='utf-8') as jsonfile:
        summary_json = json.load(jsonfile)

        for summary_key in summary_json.keys():
            if summary_key.startswith('_'):  # _SIGNATURE
                continue

            # else summary_key is someting like "openindiana.org"
            # or "hipster-encumbered"

            for fmri, pkgdatas in summary_json[summary_key].items():
                for pkgdata in pkgdatas:
                    yield fmri, pkgdata


class OpenIndianaSummaryJsonParser(Parser):
    def iter_parse(self, path, factory):
        for fmri, pkgdata in _iter_packages(path):
            pkg = factory.begin(fmri)

            pkg.set_extra_field('fmri', fmri)

            variables = {}
            for action in pkgdata['actions']:
                tokens = shlex.split(action)

                if not tokens or tokens.pop(0) != 'set':
                    factory.log('unrecognized action ' + action, severity=Logger.ERROR)
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
                        factory.log('unrecognized token ' + token, severity=Logger.ERROR)
                        continue

                if key and value:
                    variables[key] = value

            if 'com.oracle.info.name' in variables:
                pkg.set_name(variables['com.oracle.info.name'][0])

            if 'com.oracle.info.version' in variables:
                pkg.set_version(variables['com.oracle.info.version'][0])

            if 'pkg.summary' in variables:
                pkg.set_summary(variables['pkg.summary'][0])

            if 'info.classification' in variables:
                for category in variables['info.classification']:
                    if category.startswith('org.opensolaris.category.2008:'):
                        pkg.add_categories(category.split(':', 1)[1])

            if 'info.upstream-url' in variables:
                pkg.add_homepages(variables['info.upstream-url'])

            if 'info.source-url' in variables:
                pkg.add_downloads(variables['info.source-url'])

            # Regarding comment requirement: there are some packages which lack it,
            # however for ALL of them have counterparts with comment and some
            # additional fields (category, homepage, downloads). Packages without
            # comment look like legacy, and it's OK and desirable to drop them here
            if pkg.comment:
                yield pkg
