# Copyright (C) 2017-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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


class HomebrewJsonParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        for packagedata in iter_json_list(path, (None,)):
            with factory.begin() as pkg:
                pkg.add_name(packagedata['name'], NameType.HOMEBREW_NAME)
                pkg.add_name(packagedata['name'].split('@', 1)[0], NameType.HOMEBREW_NAME_PRE_AT)
                pkg.add_name(packagedata['oldname'], NameType.HOMEBREW_OLDNAME)
                pkg.add_name(packagedata['full_name'], NameType.HOMEBREW_FULL_NAME)
                pkg.set_version(packagedata['versions']['stable'])
                pkg.set_summary(packagedata['desc'])
                pkg.add_homepages(packagedata['homepage'])

                yield pkg


class HomebrewCaskJsonParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        for packagedata in iter_json_list(path, (None,)):
            with factory.begin(packagedata['token']) as pkg:
                pkg.add_name(packagedata['token'], NameType.HOMEBREW_CASK_TOKEN)
                pkg.add_name(packagedata['name'][0], NameType.HOMEBREW_CASK_FIRST_NAME)

                pkg.set_version(packagedata['version'].split(',')[0])
                pkg.add_homepages(packagedata['homepage'])
                pkg.add_downloads(packagedata['url'])

                yield pkg
