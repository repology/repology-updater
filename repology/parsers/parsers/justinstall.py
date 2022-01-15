# Copyright (C) 2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
from repology.parsers.json import iter_json_dict


class JustInstallJsonParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        for packagename, packagedata in iter_json_dict(path, ('packages', None)):
            with factory.begin() as pkg:
                pkg.add_name(packagename, NameType.JUSTINSTALL_NAME)
                pkg.set_version(packagedata['version'])

                for arch in ['x86', 'x86_64']:
                    if arch in packagedata['installer']:
                        installer = packagedata['installer'][arch]

                        # https://github.com/just-install/registry/blob/master/docs/registry.md#placeholders
                        installer = installer.replace('{{.version}}', packagedata['version'])

                        if '{{.' in installer:
                            raise RuntimeError('Unhandled replacement: {}'.format(installer))

                        pkg.add_downloads(installer)

                yield pkg
