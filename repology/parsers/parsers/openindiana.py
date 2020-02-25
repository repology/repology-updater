# Copyright (C) 2018-2020 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Tuple

from jsonslicer import JsonSlicer

from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.transformer import PackageTransformer


def _iter_packages(path: str) -> Iterable[Tuple[str, Dict[str, Any]]]:
    with open(path, 'rb') as jsonfile:
        for summary_key, fmri, _, pkgdata in JsonSlicer(jsonfile, (None, None, None), path_mode='full'):
            if summary_key.startswith('_'):  # e.g. _SIGNATURE
                continue

            # else summary_key is something like "openindiana.org"
            # or "hipster-encumbered"

            yield fmri, pkgdata


def _parse_actions(actions: List[str]) -> Dict[str, List[str]]:
    variables: Dict[str, List[str]] = defaultdict(list)

    for action in actions:
        match = re.fullmatch('set(?: last-fmri=[^ ]+)? name=([^ ]+)(?: refresh_fmri=[^ ]+)?( value=.*)', action)
        if match is None:
            raise RuntimeError(f'cannot parse action "{action}"')

        for value in match.group(2).split(' value=')[1:]:
            if value.startswith('"') and value.endswith('"') or value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            variables[match.group(1)].append(value)

    return variables


class OpenIndianaSummaryJsonParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        for fmri, pkgdata in _iter_packages(path):
            with factory.begin(f'{fmri} {pkgdata["version"]}') as pkg:
                variables = _parse_actions(pkgdata['actions'])

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

                pkg.add_name(variables['com.oracle.info.name'][0], NameType.OPENINDIANA_NAME)
                pkg.add_name(fmri, NameType.OPENINDIANA_FMRI)

                pkg.set_version(variables['com.oracle.info.version'][0])
                pkg.set_summary(variables['pkg.summary'][0])
                pkg.add_categories(cat.rsplit(':', 1)[-1] for cat in variables.get('info.classification', []))

                pkg.add_homepages(variables.get('info.upstream-url'))
                pkg.add_downloads(variables.get('info.source-url'))

                yield pkg
