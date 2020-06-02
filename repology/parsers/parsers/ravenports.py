# Copyright (C) 2017-2020 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
from repology.transformer import PackageTransformer


class RavenportsJsonParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        for packagedata in iter_json_list(path, ('ravenports', None)):
            with factory.begin() as pkg:
                pkg.add_name(packagedata['namebase'], NameType.RAVENPORTS_NAMEBASE)
                pkg.set_version(packagedata['version'])
                pkg.add_categories(packagedata['keywords'])
                pkg.add_homepages(packagedata.get('homepage'))

                pkg.add_downloads(packagedata['distfile'])
                pkg.set_summary(packagedata['variants'][0]['sdesc'])
                pkg.add_maintainers(map(lambda contact: contact.get('email'), packagedata.get('contacts', [])))  # type: ignore

                pkg.set_extra_field('bucket', packagedata['bucket'])
                pkg.set_extra_field('variant', packagedata['variants'][0]['label'])

                if 'cpe' in packagedata:
                    pkg.add_cpe(**{
                        key: packagedata['cpe'].get(key)
                        for key in ['vendor', 'product', 'edition', 'lang', 'sw_edition', 'target_sw', 'target_hw', 'other']
                    })

                yield pkg
