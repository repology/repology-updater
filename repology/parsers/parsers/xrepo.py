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

from repology.package import LinkType
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

                homepage: str | None = pkgdata.get('homepage')
                if homepage:
                    pkg.add_links(LinkType.UPSTREAM_HOMEPAGE, homepage)

                description: str | None = pkgdata.get('description')
                if description:
                    pkg.set_summary(description)

                license_: str | None = pkgdata.get('license')
                if license_:
                    pkg.add_licenses(license_)

                repo_urls: list[str] = pkgdata.get('repo_urls', [])
                if repo_urls:
                    pkg.add_links(LinkType.UPSTREAM_REPOSITORY, repo_urls[0])

                download_direct: list[str] = pkgdata.get('download_direct', [])
                download_templates: list[str] = pkgdata.get('download_templates', [])

                for version in versions:
                    verpkg = pkg.clone(append_ident=':' + version)
                    verpkg.set_version(version, _normalize_version)

                    normalized = _normalize_version(version)

                    for url in download_direct:
                        verpkg.add_links(LinkType.UPSTREAM_DOWNLOAD, url)

                    for template in download_templates:
                        verpkg.add_links(LinkType.UPSTREAM_DOWNLOAD, template.replace('$(version)', normalized))

                    yield verpkg
