# Copyright (C) 2016-2017 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import re

from repology.package import Package
from repology.util import GetMaintainers, SplitPackageNameVersion


class CPANPackagesParser():
    def __init__(self):
        pass

    def Parse(self, path):
        # Since data we get from CPAN is somewhat lacking, we need
        # somewhat complex parsing. Here's the example of what we get
        # in 02packages.details.txt package index downloaded from CPAN:
        #
        # Acme::constant                 0.001003  G/GL/GLITCHMR/Acme-constant-0.1.3.tar.gz
        # Acme::Constructor::Pythonic       0.002  T/TO/TOBYINK/Acme-Constructor-Pythonic-0.002.tar.gz
        # Acme::Continent                   undef  P/PE/PERIGRIN/XML-Toolkit-0.15.tar.gz
        #
        # 1. Module version (second column) does not always correspond
        #    to package version (which we need), so we need to parse
        #    package filename. The version may also be undefined.
        # 2. All package modules are listed, and we don't need them
        #    (which is not the problem as CPAN repo is shadow anyway)
        #
        # So we do out best to parse filename into package name and
        # actual version, and filter entries where module name is
        # equal to package name. Some entries are lost, some entries
        # are not even in 02packages.details.txt, some are unparsable
        # (no version, or garbage in version) but these are negligible.
        result = []

        with open(path) as packagesfile:
            parsing = False
            for line in packagesfile:
                line = line.strip()

                if not parsing:
                    if line == '':
                        parsing = True
                    continue

                module, version, package = re.split(r'[ \t]+', line)

                package_path, package_file = package.rsplit('/', 1)
                package_name = None

                if package_file.endswith('.tar.gz'):
                    package_name = package_file[0:-7]
                elif package_file.endswith('.tar.bz2'):
                    package_name = package_file[0:-8]
                elif package_file.endswith('.zip') or package_file.endswith('.tgz'):
                    package_name = package_file[0:-4]

                if package_name is None or package_name.find('-') == -1:
                    # Bad package name; XXX: log?
                    continue

                package_name, package_version = SplitPackageNameVersion(package_name)
                if package_version.startswith('v') or package_version.startswith('V'):
                    package_version = package_version[1:]

                if not re.match('[0-9]', package_version):
                    # Bad version; XXX: log?
                    continue

                if module.replace('::', '-').lower() != package_name.lower():
                    # Submodules not really needed
                    continue

                pkg = Package()
                pkg.name = package_name
                pkg.version = package_version

                pkg.maintainers = GetMaintainers(package_path.split('/')[2].lower() + '@cpan')
                pkg.homepage = 'http://search.cpan.org/dist/' + package_name + '/'

                result.append(pkg)

        return result
