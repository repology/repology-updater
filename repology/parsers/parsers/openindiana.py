# Copyright (C) 2018-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import shlex
from typing import Dict, Iterable, Tuple

from jsonslicer import JsonSlicer

from repology.logger import Logger
from repology.packagemaker import PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.transformer import PackageTransformer


def _iter_packages(path: str) -> Iterable[Tuple[str, Dict[str, str]]]:
    with open(path, 'rb') as jsonfile:
        for summary_key, fmri, _, pkgdata in JsonSlicer(jsonfile, (None, None, None), path_mode='full'):
            if summary_key.startswith('_'):  # e.g. _SIGNATURE
                continue

            # else summary_key is something like "openindiana.org"
            # or "hipster-encumbered"

            yield fmri, pkgdata


class OpenIndianaSummaryJsonParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        for fmri, pkgdata in _iter_packages(path):
            pkg = factory.begin('{} {}'.format(fmri, pkgdata['version']))

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

            # these are entries without name, likely not really packages
            # skip these early to avoid parsing other stuff and polluting logs with warnings
            if 'com.oracle.info.name' not in variables or 'com.oracle.info.version' not in variables:
                continue

            # Regarding comment requirement: there are some packages which lack it,
            # however for ALL of them have counterparts with comment and some
            # additional fields (category, homepage, downloads). Packages without
            # comment look like legacy, and it's OK and desirable to drop them here
            if 'pkg.summary' not in variables:
                continue

            pkg.set_name(variables['com.oracle.info.name'][0])
            pkg.set_version(variables['com.oracle.info.version'][0])
            pkg.set_summary(variables['pkg.summary'][0])

            for category in variables.get('info.classification', []):
                if category.startswith('org.opensolaris.category.2008:'):
                    pkg.add_categories(category.split(':', 1)[1])

            pkg.add_homepages(variables.get('info.upstream-url'))
            pkg.add_downloads(variables.get('info.source-url'))

            yield pkg
