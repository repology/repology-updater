# Copyright (C) 2016-2017 Dmitry Marakasov <amdmi3@amdmi3.ru>
# Copyright (C) 2017 Felix Van der Jeugt <felix.vanderjeugt@gmail.com>
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

import collections
import os
import plistlib

from repology.package import Package
from repology.util import GetMaintainers
from repology.version import VersionCompare


class VoidParser():

    def __init__(self):
        pass

    def Parse(self, path):
        packages = []

        archpath = os.path.join(path, 'arches')
        repopath = os.path.join(path, 'repo', 'srcpkgs')

        indices = {arch: plistlib.load(open(os.path.join(archpath, arch), 'rb'),
                                       fmt=plistlib.FMT_XML)
                   for arch in os.listdir(archpath)}

        for srcdir in os.scandir(repopath):
            if srcdir.is_symlink() and '/python3-' not in srcdir.name:
                # Skip subpackages unless they're python3 subpackages
                continue

            pkgname = os.path.basename(srcdir.name)

            # collect all different versions of this pkgname
            versions = collections.defaultdict(list)
            for arch, plist in indices.items():
                if pkgname in plist:
                    version = plist[pkgname]['pkgver'].split('-')[-1]
                    versions[version].append(arch)

            # create a Package for each version with corresponding arch/flavors
            for version, flavors in versions.items():
                # properties are shared among flavors in a version
                props = indices[flavors[0]][pkgname]

                pkg = Package()
                pkg.name = pkgname
                pkg.version = '_'.join(version.split('_')[:-1])
                pkg.origversion = version
                pkg.licenses = [l.strip() for l in props['license'].split(',')]
                pkg.comment = props['short_desc']
                pkg.homepage = props['homepage']
                pkg.maintainers = GetMaintainers(props.get('maintainer', ''))
                pkg.flavors = [tag
                               for flavor in flavors
                               for tag in set(flavor.split(' '))]

                packages.append(pkg)

        return packages
