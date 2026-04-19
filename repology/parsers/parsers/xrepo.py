# Copyright (C) 2024 Repology contributors
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
from typing import Any, Iterable

from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser


def _normalize_version(version: str) -> str:
    if version.startswith('v') and len(version) > 1 and version[1].isdigit():
        return version[1:]
    return version


class XrepoAPIParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        with open(path, encoding='utf-8') as f:
            data: dict[str, Any] = json.load(f)

        for pkgname, pkgdata in data.items():
            versions: list[str] = pkgdata.get('versions', [])
            if not versions:
                continue

            with factory.begin(pkgname) as pkg:
                pkg.add_name(pkgname, NameType.XREPO_NAME)
                pkg.set_extra_field('xrepo_package_path', pkgdata.get('packagedir', ''))

                description: str | None = pkgdata.get('description')
                if description:
                    pkg.set_summary(description)

                license_: str | None = pkgdata.get('license')
                if license_:
                    pkg.add_licenses(license_)

                for version in versions:
                    verpkg = pkg.clone(append_ident=':' + version)
                    verpkg.set_version(version, _normalize_version)
                    yield verpkg
