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

import os
import re
from typing import Iterable

from repology.logger import Logger
from repology.package import PackageFlags
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.transformer import PackageTransformer


def normalize_version(version: str) -> str:
    version = re.sub('[^0-9]*vcpkg.*$', '', version)  # vcpkg stuff
    version = re.sub('(alpha|beta|rc|patch)-([0-9]+)$', '\\1\\2', version)  # save from the following rule
    version = re.sub('-[0-9]+$', '', version)  # cut off revision
    version = re.sub('-[0-9a-f]{6,}$', '', version)  # drop commits

    return version


class VcpkgGitParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        for pkgdir in os.listdir(os.path.join(path, 'ports')):
            controlpath = os.path.join(path, 'ports', pkgdir, 'CONTROL')
            if not os.path.exists(controlpath):
                continue

            pkg = factory.begin()

            pkg.add_name(pkgdir, NameType.GENERIC_PKGNAME)

            with open(controlpath, 'r', encoding='utf-8', errors='ignore') as controlfile:
                for line in controlfile:
                    line = line.strip()
                    if line.startswith('Version:') and not pkg.version:
                        version = line[8:].strip()
                        if re.match('[0-9]{4}[.-][0-9]{1,2}[.-][0-9]{1,2}', version):
                            pkg.set_version(version)
                            pkg.set_flags(PackageFlags.IGNORE)
                        else:
                            pkg.set_version(version, normalize_version)
                    elif line.startswith('Description:') and not pkg.summary:
                        pkg.set_summary(line[12:])
                    elif line.startswith('Homepage:'):
                        pkg.add_homepages(line[9:])

                if pkg.version is None:
                    pkg.log('empty version', Logger.ERROR)
                    continue

            # pretty much a hack to shut a bunch of fake versions up
            portfilepath = os.path.join(path, 'ports', pkgdir, 'portfile.cmake')
            if os.path.exists(portfilepath):
                with open(portfilepath, 'r', encoding='utf-8', errors='ignore') as portfile:
                    for line in portfile:
                        if 'libimobiledevice-win32' in line:
                            pkg.log('marking as untrusted, https://github.com/libimobiledevice-win32 accused of version faking', severity=Logger.WARNING)
                            pkg.set_flags(PackageFlags.UNTRUSTED)
                            break

            yield pkg
