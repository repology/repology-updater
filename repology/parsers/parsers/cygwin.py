# Copyright (C) 2019 Jon Turney <jon.turney@dronecode.org.uk>
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
from typing import Iterable

from repology.package import PackageFlags
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.json import iter_json_list
from repology.transformer import PackageTransformer


class CygwinParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        for packagedata in iter_json_list(path, ('packages', None)):
            with factory.begin() as pkg:
                # packages with names starting with an underscore are
                # uninteresting as they contain cygwin-specific
                # installation helper scripts
                if packagedata['name'].startswith('_'):
                    continue

                pkg.add_name(packagedata['name'], NameType.CYGWIN_PACKAGE_NAME)
                pkg.set_summary(packagedata['summary'])

                if 'maintainers' in packagedata:
                    pkg.add_maintainers([m.replace('.', '').replace(' ', '.') + '@cygwin' for m in packagedata['maintainers']])

                if 'homepage' in packagedata:
                    pkg.add_homepages(packagedata['homepage'])

                for maturity in ['stable', 'test']:
                    if maturity not in packagedata['versions']:
                        continue

                    verpkg = pkg.clone()
                    verpkg.set_flags(PackageFlags.IGNORE, maturity == 'test')  # XXX: weak_devel

                    raw_version = packagedata['versions'][maturity][-1]
                    (version, release) = raw_version.rsplit('-', 1)

                    # If release is just '0', that means someone
                    # forgot it counts from 1, but if it starts with
                    # '0', the rest indicates the pre-release version
                    # (as per Fedora/repodata.py)
                    if release.startswith('0') and len(release) > 1:
                        match = re.fullmatch(r'.*((?:alpha|beta|rc)(?:\.?[0-9]+)?|(?<![a-z])[ab]\.?[0-9]+)', release)
                        if match:
                            # known pre-release schema
                            version += '-' + match.group(1)
                            verpkg.set_flags(PackageFlags.DEVEL)
                        else:
                            # unknown pre-release schema
                            verpkg.set_flags(PackageFlags.IGNORE)

                    verpkg.set_version(version)
                    verpkg.set_rawversion(raw_version)

                    for subpackagedata in packagedata['subpackages']:
                        if '_obsolete' in subpackagedata['categories']:
                            continue

                        subpkg = verpkg.clone()

                        subpkg.add_name(subpackagedata['name'], NameType.CYGWIN_SUBPACKAGE_NAME)
                        subpkg.add_categories(subpackagedata['categories'])

                        yield subpkg
