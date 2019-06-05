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

import xml.etree.ElementTree
from typing import Iterable

from repology.package import PackageFlags
from repology.packagemaker import PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.transformer import PackageTransformer


class FDroidParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        root = xml.etree.ElementTree.parse(path)

        for application in root.findall('application'):
            app = factory.begin()

            app.set_name(application.find('name').text)  # type: ignore
            app.add_licenses(application.find('license').text)  # type: ignore
            app.add_categories(application.find('category').text)  # type: ignore
            app.add_homepages(application.find('web').text)  # type: ignore
            app.set_extra_field('id', application.find('id').text)  # type: ignore

            upstream_version_code = int(application.find('marketvercode').text)  # type: ignore
            for package in application.findall('package'):
                version_code = int(package.find('versioncode').text)  # type: ignore
                version = package.find('version').text  # type: ignore

                if version:
                    pkg = app.clone()

                    pkg.set_version(version)
                    pkg.set_flags(PackageFlags.devel if version_code > upstream_version_code else 0)

                    yield pkg
