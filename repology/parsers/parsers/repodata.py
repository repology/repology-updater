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

import re
from typing import Dict, Iterable, List, Optional

from repology.logger import Logger
from repology.package import PackageFlags
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers
from repology.parsers.nevra import nevra_construct
from repology.parsers.sqlite import iter_sqlite
from repology.parsers.versions import VersionStripper
from repology.parsers.xml import iter_xml_elements_at_level, safe_findtext
from repology.transformer import PackageTransformer


class RepodataParser(Parser):
    def __init__(self, allowed_archs: Optional[List[str]] = None) -> None:
        self.allowed_archs = allowed_archs

    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        normalize_version = VersionStripper().strip_right_greedy('+')

        skipped_archs: Dict[str, int] = {}

        for entry in iter_xml_elements_at_level(path, 1, ['{http://linux.duke.edu/metadata/common}package']):
            with factory.begin() as pkg:
                arch = safe_findtext(entry, '{http://linux.duke.edu/metadata/common}arch')

                if self.allowed_archs and arch not in self.allowed_archs:
                    skipped_archs[arch] = skipped_archs.get(arch, 0) + 1
                    continue

                name = safe_findtext(entry, '{http://linux.duke.edu/metadata/common}name')
                if '%{' in name:
                    pkg.log('incorrect package name (unexpanded substitution)', severity=Logger.ERROR)
                    continue

                pkg.add_name(name, NameType.GENERIC_PKGNAME)

                version_elt = entry.find('{http://linux.duke.edu/metadata/common}version')
                if version_elt is None:
                    raise RuntimeError('Cannot find <version> element')

                epoch = version_elt.attrib['epoch']
                version = version_elt.attrib['ver']
                release = version_elt.attrib['rel']

                match = re.match('0\\.[0-9]+\\.((?:alpha|beta|rc)[0-9]+)\\.', release)
                if match:
                    # known pre-release schema: https://fedoraproject.org/wiki/Packaging:Versioning#Prerelease_versions
                    version += '-' + match.group(1)
                elif release < '1':
                    # unknown pre-release schema: https://fedoraproject.org/wiki/Packaging:Versioning#Some_definitions
                    # most likely a snapshot
                    pkg.set_flags(PackageFlags.IGNORE)

                pkg.set_version(version, normalize_version)
                pkg.set_rawversion(nevra_construct(None, epoch, version, release))

                pkg.set_summary(entry.findtext('{http://linux.duke.edu/metadata/common}summary'))
                pkg.add_homepages(entry.findtext('{http://linux.duke.edu/metadata/common}url'))
                pkg.add_categories(entry.findtext('{http://linux.duke.edu/metadata/common}format/'
                                                  '{http://linux.duke.edu/metadata/rpm}group'))
                pkg.add_licenses(entry.findtext('{http://linux.duke.edu/metadata/common}format/'
                                                '{http://linux.duke.edu/metadata/rpm}license'))
                pkg.set_arch(entry.findtext('{http://linux.duke.edu/metadata/common}arch'))

                packager = entry.findtext('{http://linux.duke.edu/metadata/common}packager')
                if packager:
                    pkg.add_maintainers(extract_maintainers(packager))

                yield pkg

        for arch, numpackages in sorted(skipped_archs.items()):
            factory.log('skipped {} packages(s) with disallowed architecture {}'.format(numpackages, arch))


class RepodataSqliteParser(Parser):

    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        normalize_version = VersionStripper().strip_right_greedy('+')

        for pkgdata in iter_sqlite(path, 'packages',
                                   ['name', 'version', 'arch', 'epoch',
                                    'release', 'summary', 'url', 'rpm_group',
                                    'rpm_license', 'arch', 'rpm_packager']):
            with factory.begin() as pkg:
                pkg.add_name(pkgdata['name'], NameType.GENERIC_PKGNAME)

                version = pkgdata['version']

                match = re.match('0\\.[0-9]+\\.((?:alpha|beta|rc)[0-9]+)\\.', pkgdata['release'])
                if match:
                    # known pre-release schema: https://fedoraproject.org/wiki/Packaging:Versioning#Prerelease_versions
                    version += '-' + match.group(1)
                elif pkgdata['release'] < '1':
                    # unknown pre-release schema: https://fedoraproject.org/wiki/Packaging:Versioning#Some_definitions
                    # most likely a snapshot
                    pkg.set_flags(PackageFlags.IGNORE)

                pkg.set_version(version, normalize_version)
                pkg.set_rawversion(nevra_construct(None, pkgdata['epoch'], pkgdata['version'], pkgdata['release']))

                pkg.set_arch(pkgdata['arch'])
                pkg.set_summary(pkgdata['summary'])
                pkg.add_homepages(pkgdata['url'])
                pkg.add_categories(pkgdata['rpm_group'])
                pkg.add_licenses(pkgdata['rpm_license'])
                pkg.set_arch(pkgdata['arch'])
                pkg.add_maintainers(extract_maintainers(pkgdata['rpm_packager']))

                yield pkg
