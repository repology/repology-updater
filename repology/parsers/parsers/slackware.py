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

from typing import Iterable

from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.transformer import PackageTransformer


def _iterate_packages(path: str) -> Iterable[tuple[str, str]]:
    with open(path, encoding='utf-8', errors='ignore') as packagesfile:
        current_name = None

        for line in packagesfile:
            line = line.strip()
            if line.startswith('PACKAGE NAME:'):
                current_name = line.split(':', 1)[1].strip()
            elif line.startswith('PACKAGE LOCATION:'):
                if not current_name:
                    raise RuntimeError('"{}" encountered without preceding PACKAGE NAME: line'.format(line))
                yield current_name, line.split(':', 1)[1].strip()
            elif not line:
                current_name = None


class SlackwarePackagesParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        for pkgname, pkglocation in _iterate_packages(path):
            pkg = factory.begin(pkgname)

            name, version, arch, rest = pkgname.rsplit('-', 3)

            pkg.add_name(name, NameType.SLACKWARE_NAME)
            pkg.add_name(pkglocation + '/' + pkgname, NameType.SLACKWARE_FULL_NAME)
            pkg.add_name(pkglocation + '/' + name, NameType.SLACKWARE_PSEUDO_FULL_NAME)
            pkg.set_version(version)
            pkg.set_arch(arch)

            # Don't waste cycles: slackware repositories have no structure,
            # so we can't construct links to sources anyway

            #locationcomps = pkglocation.split('/')

            #if len(locationcomps) == 3:
            #    pkg.set_extra_field('loc_subrepo', locationcomps[-2])
            #    pkg.set_extra_field('loc_category', locationcomps[-1])
            #else:
            #    pkg.log('unexpected location format: {}'.format(pkglocation), Logger.WARNING)

            # single letter garbage in slackware/, and has different
            # meaning in extras/ and patches/
            #pkg.add_categories(pkglocation.split('/')[-1])

            yield pkg
