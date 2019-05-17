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

import json
import os
from typing import Generator

from repology.packagemaker import PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers
from repology.parsers.versions import VersionStripper
from repology.transformer import PackageTransformer


class AURParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Generator[PackageMaker, None, None]:
        normalize_version = VersionStripper().strip_right_greedy('-').strip_left(':').strip_right_greedy('+')

        for filename in os.listdir(path):
            if not filename.endswith('.json'):
                continue

            with open(os.path.join(path, filename), 'r') as jsonfile:
                for result in json.load(jsonfile)['results']:
                    pkg = factory.begin()

                    pkg.set_name(result['Name'])

                    pkg.set_version(result['Version'], normalize_version)
                    pkg.set_summary(result['Description'])
                    pkg.add_homepages(result['URL'])
                    pkg.add_licenses(result.get('License'))

                    if 'Maintainer' in result and result['Maintainer']:
                        pkg.add_maintainers(extract_maintainers(result['Maintainer'] + '@aur'))

                    if 'PackageBase' in result and result['PackageBase']:
                        pkg.set_basename(result['PackageBase'])

                    # XXX: enable when we support multiple categories
                    #if 'Keywords' in result and result['Keywords']:
                    #    pkg.add_categories(result['Keywords'])

                    yield pkg
