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

from repology.packagemaker import PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.transformer import PackageTransformer


class AnityaApiParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        with open(path, 'r', encoding='utf-8') as jsonfile:
            for project in json.load(jsonfile)['projects']:
                pkg = factory.begin()

                pkg.set_name(project['name'])
                pkg.set_version(project['version'])

                pkg.add_homepages(project['homepage'])
                pkg.set_version(pkg.version[1:])

                if project['backend'] == 'CPAN (perl)':
                    pkg.prefix_name('perl:')
                elif project['backend'] == 'Rubygems':
                    pkg.prefix_name('ruby:')

                yield pkg
