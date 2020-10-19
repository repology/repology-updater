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

import json
import os
import re
from typing import Any, Dict, Iterable, cast

from repology.logger import Logger
from repology.package import PackageFlags
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers
from repology.transformer import PackageTransformer


def _normalize_version(version: str) -> str:
    version = re.sub('[^0-9]*vcpkg.*$', '', version)  # vcpkg stuff
    version = re.sub('(alpha|beta|rc|patch)-([0-9]+)$', '\\1\\2', version)  # save from the following rule
    version = re.sub('-[0-9]+$', '', version)  # cut off revision
    version = re.sub('-[0-9a-f]{6,}$', '', version)  # drop commits

    return version


def _read_control_file(path: str) -> Dict[str, Any]:
    control_to_manifest_key_map = {
        'Source': 'name',
        'Version': 'version-string',
        'Description': 'description',
        'Homepage': 'homepage',
    }

    res: Dict[str, Any] = {}

    with open(path, 'r', encoding='utf-8', errors='ignore') as controlfile:
        for line in controlfile:
            key, *rest = map(str.strip, line.strip().split(':', 1))

            if len(rest) == 1 and key in control_to_manifest_key_map and control_to_manifest_key_map[key] not in res:
                res[control_to_manifest_key_map[key]] = rest[0]

    return res


def _read_manifest_file(path: str) -> Dict[str, Any]:
    with open(path) as manifestfile:
        return cast(Dict[str, Any], json.load(manifestfile))


def _grep_file(path: str, sample: str) -> bool:
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8', errors='ignore') as fd:
            for line in fd:
                if sample in line:
                    return True

    return False


class VcpkgGitParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        has_control_files = False

        for pkgdir in os.listdir(os.path.join(path, 'ports')):
            with factory.begin(pkgdir) as pkg:
                controlpath = os.path.join(path, 'ports', pkgdir, 'CONTROL')
                manifestpath = os.path.join(path, 'ports', pkgdir, 'vcpkg.json')

                # read either of old-style control (CONTROL) or new-style manifest (vcpkg.json) file
                if os.path.exists(manifestpath):
                    pkgdata = _read_manifest_file(manifestpath)
                elif os.path.exists(controlpath):
                    has_control_files = True
                    pkgdata = _read_control_file(controlpath)
                else:
                    pkg.log('neither control nor manifest file found', Logger.ERROR)
                    continue

                if pkgdata['name'] != pkgdir:
                    raise RuntimeError(f'sanity check failed: source {pkgdata["name"]} != directory {pkgdir}')

                pkg.add_name(pkgdata['name'], NameType.VCPKG_SOURCE)

                version = pkgdata['version-string']

                if re.match('[0-9]{4}[.-][0-9]{1,2}[.-][0-9]{1,2}', version):
                    pkg.set_version(version)
                    pkg.set_flags(PackageFlags.IGNORE)
                else:
                    pkg.set_version(version, _normalize_version)

                # handle description which may be either a string or a list of strings
                description = pkgdata.get('description')

                if isinstance(description, str):
                    pkg.set_summary(description)
                elif isinstance(description, list):
                    pkg.set_summary(description[0])

                pkg.add_homepages(pkgdata.get('homepage'))

                for maintainer in pkgdata.get('maintainers', []):
                    pkg.add_maintainers(extract_maintainers(maintainer))

                # pretty much a hack to shut a bunch of fake versions up
                portfilepath = os.path.join(path, 'ports', pkgdir, 'portfile.cmake')
                if _grep_file(portfilepath, 'libimobiledevice-win32'):
                    pkg.log('marking as untrusted, https://github.com/libimobiledevice-win32 accused of version faking', severity=Logger.WARNING)
                    pkg.set_flags(PackageFlags.UNTRUSTED)

                yield pkg

        if not has_control_files:
            factory.log("No CONTROL files seen in the repository, seems like it's time to refactor vcpkg parser and remove legacy bits")
