# Copyright (C) 2016-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.json import iter_json_list
from repology.parsers.versions import VersionStripper
from repology.transformer import PackageTransformer


class MacPortsJsonParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        normalize_version = VersionStripper().strip_right('+')

        for pkgdata in iter_json_list(path, ('ports', None)):
            with factory.begin() as pkg:
                # drop obsolete ports (see #235)
                if 'replaced_by' in pkgdata:
                    continue

                pkg.add_name(pkgdata['name'], NameType.GENERIC_PKGNAME)
                pkg.set_version(pkgdata['version'], normalize_version)
                pkg.set_summary(pkgdata.get('description'))
                pkg.add_homepages(pkgdata.get('homepage'))
                pkg.add_categories(pkgdata.get('categories'))
                pkg.add_licenses(pkgdata['license'])  # XXX: properly handle braces

                for maintainerdata in pkgdata['maintainers']:
                    # macports decided not to publish raw maintainer emails
                    #if 'email' in maintainerdata:
                    #    pkg.add_maintainers(maintainerdata['email']['name'] + '@' + maintainerdata['email']['domain'])
                    # provide fallback with macports accounts
                    if 'email' in maintainerdata and maintainerdata['email']['domain'] == 'macports.org':
                        pkg.add_maintainers(maintainerdata['email']['name'] + '@macports')
                    if 'github' in maintainerdata:
                        pkg.add_maintainers(maintainerdata['github'] + '@github')
                if not pkgdata['maintainers']:
                    pkg.add_maintainers('nomaintainer@macports.org')

                pkg.set_extra_field('portdir', pkgdata['portdir'])
                pkg.set_extra_field('portname', pkgdata['portdir'].split('/')[1])

                yield pkg
