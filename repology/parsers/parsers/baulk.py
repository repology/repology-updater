# Copyright (C) 2021 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
from typing import Iterable

from repology.logger import Logger
from repology.package import PackageFlags
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser


class BaulkGitParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        bucket_path = os.path.join(path, 'bucket')

        for filename in os.listdir(bucket_path):
            if not filename.endswith('.json'):
                continue

            with factory.begin(filename) as pkg:
                with open(os.path.join(bucket_path, filename)) as fd:
                    pkgdata = json.load(fd)

                pkg.add_name(filename.removesuffix('.json'), NameType.BAULK_NAME)
                pkg.set_version(pkgdata['version'])
                pkg.set_summary(pkgdata['description'])

                homepage = pkgdata.get('homepage')
                if homepage and 'baulk' in homepage:
                    pkg.log('Not trusting package with baulk upstream', severity=Logger.ERROR)
                    pkg.set_flags(PackageFlags.UNTRUSTED)

                pkg.add_homepages(homepage)

                for architecture in pkgdata['architecture'].values():
                    pkg.add_downloads(architecture['url'])

                yield pkg
