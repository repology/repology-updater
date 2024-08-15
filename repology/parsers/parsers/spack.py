# Copyright (C) 2021 Vanessa Sochat, Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from typing import Any, Iterable

from libversion import version_compare

from repology.package import LinkType, PackageFlags
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.json import iter_json_dict
from repology.parsers.versions import VersionStripper


class SpackJsonParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        normalize_version = VersionStripper().strip_left(':')

        for key, pkgdata in iter_json_dict(path, ('packages', None)):
            with factory.begin(key) as pkg:
                pkg.add_name(pkgdata['name'], NameType.SPACK_NAME)
                pkg.add_homepages(pkgdata['homepages'])
                pkg.add_maintainers(f'{m}@spack' for m in pkgdata['maintainers'])
                pkg.add_categories(pkgdata['categories'])
                pkg.add_licenses(pkgdata['licenses'])
                pkg.set_extra_field('patch', [patch.split()[0] for patch in pkgdata['patches'] if '://' not in patch])

                # - no usable keywords/categories (yet)
                # - summaries are multiline, so ignored
                # - dependencies info is available, not used yet

                # spack may contain a lot of versions for a single project,
                # we don't handle that very well, so pick greatest release
                # version and all rolling versions
                picked_verdatas: list[dict[str, Any]] = []
                latest_release_verdata: dict[str, Any] | None = None

                for pkgverdata in pkgdata['version']:
                    if 'branch' in pkgverdata:
                        picked_verdatas.append(pkgverdata)
                    elif latest_release_verdata is None or version_compare(pkgverdata['version'], latest_release_verdata['version']) > 0:
                        latest_release_verdata = pkgverdata

                if latest_release_verdata:
                    picked_verdatas.append(latest_release_verdata)

                for pkgverdata in picked_verdatas:
                    verpkg = pkg.clone()

                    if 'branch' in pkgverdata:
                        verpkg.set_flags(PackageFlags.ROLLING)

                    verpkg.set_version(pkgverdata['version'], normalize_version)

                    if downloads := pkgverdata.get('downloads'):
                        verpkg.add_links(LinkType.UPSTREAM_DOWNLOAD, downloads)
                    elif repositories := pkgverdata.get('repositories'):
                        if isinstance(repositories, dict):
                            # XXX: legacy, repositories are expected to be a list https://github.com/spack/packages.spack.io/pull/24
                            verpkg.add_links(LinkType.UPSTREAM_REPOSITORY, repositories['url'])
                        elif isinstance(repositories, list):
                            verpkg.add_links(LinkType.UPSTREAM_REPOSITORY, [repository['url'] for repository in repositories])

                    yield verpkg
