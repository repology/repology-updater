# Copyright (C) 2017 Dingyuan Wang <gumblex@aosc.io>
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

from typing import Iterable

from repology.logger import Logger
from repology.package import LinkType, PackageFlags
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.json import iter_json_list
from repology.parsers.versions import VersionStripper


class AoscPkgsParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        normalize_version = VersionStripper().strip_left(':')

        for pkgdata in iter_json_list(path, ('packages', None)):
            if pkgdata['category'] == 'meta' and pkgdata['section'] == 'bases':
                # skip dummy packages in meta-bases section
                continue
            with factory.begin() as pkg:
                pkg.add_name(pkgdata['name'], NameType.AOSC_NAME)
                pkg.add_name(pkgdata['directory'], NameType.AOSC_DIRECTORY)
                pkg.add_name(
                    '{}-{}/{}'.format(
                        pkgdata['category'],
                        pkgdata['section'],
                        pkgdata['directory'],
                    ),
                    NameType.AOSC_FULLPATH
                )

                pkg.set_extra_field('tree', pkgdata['tree'])
                pkg.set_extra_field('branch', pkgdata['branch'])

                if pkgdata['version'] is None:
                    pkg.log('no version defined', Logger.ERROR)
                    continue

                pkg.set_version(pkgdata['version'], normalize_version)

                pkg.set_rawversion(pkgdata['full_version'])
                pkg.add_categories(pkgdata['pkg_section'], pkgdata['section'])
                pkg.set_summary(pkgdata['description'])

                srctype = pkgdata['srctype']
                if srctype == 'Git' or srctype == 'Svn' or srctype == 'Bzr':
                    pkg.add_links(LinkType.UPSTREAM_REPOSITORY, pkgdata['srcurl'])
                elif srctype == 'Tarball':
                    pkg.add_links(LinkType.UPSTREAM_DOWNLOAD, pkgdata['srcurl'])

                # just a committer, doesn't seem suitable
                #pkg.add_maintainers(extract_maintainers(pkgdata['committer']))

                if pkg.version == '999':
                    pkg.set_flags(PackageFlags.IGNORE)  # XXX: rolling? revisit

                yield pkg
