# Copyright (C) 2016-2021 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
from collections import Counter
from typing import Any, Iterable

from repology.logger import Logger
from repology.package import PackageFlags
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers
from repology.parsers.nevra import nevra_construct, nevra_parse
from repology.parsers.sqlite import iter_sqlite
from repology.parsers.versions import VersionStripper, parse_rpm_version, parse_rpm_vertags
from repology.parsers.xml import iter_xml_elements_at_level, safe_findtext, safe_getattr
from repology.transformer import PackageTransformer


class RepodataParser(Parser):
    _src: bool
    _binary: bool

    # hack for openmandriva 3 which for some reason specifies binary
    # architectures in '<arch></arch>' for source packages
    _arch_from_filename: bool

    _vertags: list[str]

    def __init__(self, src: bool = True, binary: bool = False, arch_from_filename: bool = False, vertags: Any = None) -> None:
        if not src and not binary:
            raise RuntimeError('at least one of "src" and "binary" modes for RepodataParser must be enabled')

        self._src = src
        self._binary = binary
        self._arch_from_filename = arch_from_filename
        self._vertags = parse_rpm_vertags(vertags)

    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        normalize_version = VersionStripper().strip_right_greedy('+')

        skipped_archs: dict[str, int] = Counter()

        if self._arch_from_filename:
            factory.log('mitigation for incorrect <arch></arch> enabled', severity=Logger.WARNING)

        for entry in iter_xml_elements_at_level(path, 1, ['{http://linux.duke.edu/metadata/common}package']):
            if self._arch_from_filename:
                # XXX: openmandriva 3 hack, to be removed when it EoLs
                location_elt = entry.find('{http://linux.duke.edu/metadata/common}location')
                if location_elt is None:
                    raise RuntimeError('Cannot find <location> element')
                arch = nevra_parse(safe_getattr(location_elt, 'href'))[4]
            else:
                arch = safe_findtext(entry, '{http://linux.duke.edu/metadata/common}arch')

            is_src = arch == 'src'

            if (is_src and not self._src) or (not is_src and not self._binary):
                skipped_archs[arch] += 1
                continue

            with factory.begin() as pkg:
                name = safe_findtext(entry, '{http://linux.duke.edu/metadata/common}name')
                if '%{' in name:
                    pkg.log('incorrect package name (unexpanded substitution)', severity=Logger.ERROR)
                    continue

                if is_src:
                    pkg.add_name(name, NameType.SRCRPM_NAME)
                else:
                    pkg.add_name(name, NameType.BINRPM_NAME)
                    sourcerpm = safe_findtext(
                        entry,
                        '{http://linux.duke.edu/metadata/common}format/'
                        '{http://linux.duke.edu/metadata/rpm}sourcerpm'
                    )
                    pkg.add_name(nevra_parse(sourcerpm)[0], NameType.BINRPM_SRCNAME)

                version_elt = entry.find('{http://linux.duke.edu/metadata/common}version')
                if version_elt is None:
                    raise RuntimeError('Cannot find <version> element')

                epoch = version_elt.attrib['epoch']
                version = version_elt.attrib['ver']
                release = version_elt.attrib['rel']

                fixed_version, flags = parse_rpm_version(self._vertags, version, release)

                pkg.set_version(fixed_version, normalize_version)
                pkg.set_rawversion(nevra_construct(None, epoch, version, release))
                pkg.set_flags(flags)

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
    def __init__(self, src: bool = True, binary: bool = False) -> None:
        if not src and not binary:
            raise RuntimeError('at least one of "src" and "binary" modes for RepodataParser must be enabled')

        self._src = src
        self._binary = binary

    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        normalize_version = VersionStripper().strip_right_greedy('+')

        skipped_archs: dict[str, int] = Counter()

        wanted_columns = ['name', 'version', 'arch', 'epoch', 'release',
                          'summary', 'url', 'rpm_group', 'rpm_license',
                          'arch', 'rpm_packager', 'rpm_sourcerpm']

        for pkgdata in iter_sqlite(path, 'packages', wanted_columns):
            is_src = pkgdata['arch'] == 'src'

            if (is_src and not self._src) or (not is_src and not self._binary):
                skipped_archs[pkgdata['arch']] += 1
                continue

            with factory.begin() as pkg:
                if is_src:
                    pkg.add_name(pkgdata['name'], NameType.SRCRPM_NAME)
                else:
                    pkg.add_name(pkgdata['name'], NameType.BINRPM_NAME)
                    pkg.add_name(nevra_parse(pkgdata['rpm_sourcerpm'])[0], NameType.BINRPM_SRCNAME)

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
