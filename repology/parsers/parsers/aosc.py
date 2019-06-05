# Copyright (C) 2017 Dingyuan Wang <gumblex@aosc.io>
# Copyright (C) 2018-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
from typing import Iterable

from repology.package import PackageFlags
from repology.packagemaker import PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers
from repology.parsers.versions import VersionStripper
from repology.transformer import PackageTransformer


class AoscPkgsParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        normalize_version = VersionStripper().strip_left(':')

        with open(path, 'r', encoding='utf-8') as jsonfile:
            for package in json.load(jsonfile)['packages']:
                pkg = factory.begin()

                pkg.set_name(package['name'])
                pkg.set_version(package['version'], normalize_version)

                if not pkg.check_sanity(verbose=True):
                    continue

                pkg.set_rawversion(package['full_version'])
                pkg.add_categories(package['pkg_section'], package['section'])
                pkg.set_summary(package['description'])
                pkg.add_maintainers(extract_maintainers(package['committer']))

                if pkg.version == '999':
                    pkg.set_flags(PackageFlags.ignore)  # XXX: rolling? revisit

                yield pkg
