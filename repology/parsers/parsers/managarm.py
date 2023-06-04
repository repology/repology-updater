# Copyright (C) 2017-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
# Copyright (C) 2017 Felix Van der Jeugt <felix.vanderjeugt@gmail.com>
# Copyright (C) 2023 Alexander Richards <electrodeyt@gmail.com>
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

import os
import plistlib
from typing import Iterable

from repology.logger import Logger
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers
from repology.parsers.versions import VersionStripper


class ManagarmPlistParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        normalize_version = VersionStripper().strip_right_greedy('_')

        with open(os.path.join(path, 'index.plist'), 'rb') as plistfile:
            plist_index: dict[str, dict[str, str]] = plistlib.load(plistfile, fmt=plistlib.FMT_XML)

        for pkgname, props in plist_index.items():
            with factory.begin(pkgname) as pkg:
                if not props['pkgver'].startswith(pkgname + '-'):
                    pkg.log('pkgver is expected to start with package name', severity=Logger.ERROR)
                    continue

                # Managarm packages have one unique name, and while the recipe files are sorted into seperate
                # directories, the package names themselves are the only unique identifer that a package has.
                pkg.add_name(pkgname, NameType.GENERIC_SRCBIN_NAME)
                pkg.set_version(props['pkgver'][len(pkgname) + 1:], normalize_version)
                pkg.add_maintainers(extract_maintainers(props.get('maintainer', '')))

                pkg.set_arch(props['architecture'])

                # At present, not all packages have these.
                if 'short_desc' in props:
                    pkg.set_summary(props['short_desc'])
                if 'homepage' in props:
                    pkg.add_homepages(props['homepage'])
                if 'licenses' in props:
                    pkg.add_licenses(props['license'].split(','))

                yield pkg
