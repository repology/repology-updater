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

import configparser
import os
from typing import Iterable

from repology.logger import Logger
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser


class RappsParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        for filename in os.listdir(os.path.join(path)):
            if not filename.endswith('.txt'):
                continue

            with factory.begin(filename) as pkg:
                config = configparser.ConfigParser(interpolation=None)

                with open(os.path.join(path, filename), 'r', encoding='utf_8_sig') as f:
                    config.readfp(f)  # type: ignore

                section = config['Section']

                pkg.add_name(filename[:-4], NameType.REACTOS_FILENAME)

                if section.get('Version') is None:
                    pkg.log('no version defined', Logger.ERROR)
                    continue

                pkg.set_version(section['Version'])
                pkg.set_summary(section['Description'])
                pkg.add_homepages(section.get('URLSite'))
                pkg.add_downloads(section['URLDownload'])
                pkg.add_licenses(section.get('License'))

                pkg.add_name(section['Name'], NameType.REACTOS_NAME)

                yield pkg
