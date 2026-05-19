# Copyright (C) 2026 Aleksandr Kovalko <gistrec@gmail.com>
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

from typing import Iterable

from repology.package import LinkType
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.json import iter_json_list


def _normalize_version(version: str) -> str:
    if version.startswith('v') and len(version) > 1 and version[1].isdigit():
        return version[1:]
    return version


class XrepoJsonParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        for pkgdata in iter_json_list(path, ('packages', None)):
            name = pkgdata.get('name')
            version = pkgdata.get('version')
            if not name or not version:
                continue

            with factory.begin(name) as pkg:
                pkg.add_name(name, NameType.XREPO_NAME)
                pkg.set_version(version, _normalize_version)
                pkg.set_extra_field('xrepo_package_path', f'packages/{name[0]}/{name}')

                if (summary := pkgdata.get('description')):
                    pkg.set_summary(summary)
                if (homepage := pkgdata.get('homepage')):
                    pkg.add_links(LinkType.UPSTREAM_HOMEPAGE, homepage)
                if (license_ := pkgdata.get('license')):
                    pkg.add_licenses(license_)
                if (repo_url := pkgdata.get('repository_url')):
                    pkg.add_links(LinkType.UPSTREAM_REPOSITORY, repo_url)

                download_url = pkgdata.get('download_url')
                if download_url and not download_url.endswith('.git'):
                    pkg.add_links(LinkType.UPSTREAM_DOWNLOAD, download_url)

                yield pkg
