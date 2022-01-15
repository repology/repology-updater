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

from typing import Iterable

from repology.logger import Logger
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers


class CPANPackagesParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
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
        with open(path) as packagesfile:
            skipping_header = True
            for nline, line in enumerate(packagesfile, 1):
                line = line.strip()

                if skipping_header:
                    if line == '':
                        skipping_header = False
                    continue

                pkg = factory.begin('line {}'.format(nline))

                module, version, package = line.split(None, 2)

                package_path, package_file = package.rsplit('/', 1)
                package_name = None

                for ext in ['.tar.gz', '.tar.bz2', '.zip', '.tgz']:
                    if package_file.endswith(ext):
                        package_name = package_file[0:-len(ext)]
                        break

                if package_name is None or '-' not in package_name:
                    pkg.log('unable to parse package name', Logger.ERROR)
                    continue

                package_name, package_version = package_name.rsplit('-', 1)
                if package_version.startswith('v') or package_version.startswith('V'):
                    package_version = package_version[1:]

                if not package_version[0].isdecimal():
                    pkg.log('skipping bad version {}'.format(package_version), Logger.ERROR)
                    continue

                if module.replace('::', '-').lower() != package_name.lower():
                    pkg.log('skipping submodule {}'.format(module), Logger.WARNING)
                    continue

                pkg.add_name(package_name, NameType.CPAN_NAME)
                pkg.set_version(package_version)

                pkg.add_maintainers(extract_maintainers(package_path.split('/')[2].lower() + '@cpan'))
                pkg.add_homepages('http://search.cpan.org/dist/' + package_name + '/')

                yield pkg
