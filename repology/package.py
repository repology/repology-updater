# Copyright (C) 2016 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from repology.version import VersionCompare, MaxVersion


class PackageVersionClass:
    newest = 1,
    outdated = 2,
    ignored = 3

    @staticmethod
    def ToChar(value):
        if value == PackageVersionClass.newest:
            return 'N'
        elif value == PackageVersionClass.outdated:
            return 'O'
        elif value == PackageVersionClass.ignored:
            return 'I'
        else:
            return '?'

class RepositoryVersionClass:
    newest = 1,
    outdated = 2,
    mixed = 3,
    ignored = 4,
    lonely = 5

    @staticmethod
    def ToChar(value):
        if value == RepositoryVersionClass.newest:
            return 'N'
        elif value == RepositoryVersionClass.outdated:
            return 'O'
        elif value == RepositoryVersionClass.mixed:
            return 'M'
        elif value == RepositoryVersionClass.ignored:
            return 'I'
        elif value == RepositoryVersionClass.lonely:
            return 'L'
        else:
            return '?'


class Package:
    __slots__ = [
        'repo',
        'family',

        'name',
        'effname',

        'version',
        'origversion',
        'effversion',
        'versionclass',

        'maintainers',
        'category',
        'comment',
        'homepage',
        'licenses',
        'downloads',

        'ignore',
        'shadow',
        'ignoreversion',
    ]

    def __init__(self):
        self.repo = None
        self.family = None

        self.name = None
        self.effname = None

        self.version = None
        self.origversion = None
        self.effversion = None
        self.versionclass = None

        self.maintainers = []
        self.category = None
        self.comment = None
        self.homepage = None
        self.licenses = []
        self.downloads = []

        self.ignore = False
        self.shadow = False
        self.ignoreversion = False

    @property
    def __dict__(self):
        return {slot: getattr(self, slot) for slot in self.__slots__}


def MergeMetapackages(*packagesets, enable_shadows=True):
    metapackages = {}

    for packageset in packagesets:
        for package in packageset:
            if package.effname not in metapackages:
                metapackages[package.effname] = []
            metapackages[package.effname].append(package)

    # process shadows
    # XXX: move this below, into summary processing
    def CheckShadows(packages):
        nonshadow = False
        for package in packages:
            if not package.shadow:
                return True
        return False

    if enable_shadows:
        metapackages = { metaname: packages for metaname, packages in metapackages.items() if CheckShadows(packages) }

    return metapackages


def FilterMetapackages(metapackages, *filters):
    filtered_metapackages = {}

    for name, packages in metapackages.items():
        passes = True
        for filt in filters:
            if not filt.Check(packages):
                passes = False
                break
        if passes:
            filtered_metapackages[name] = packages

    return filtered_metapackages


def FillMetapackagesVersionInfos(metapackages):
    for name, packages in metapackages.items():
        versions = set()
        families = set()

        for package in packages:
            if not package.ignoreversion:
                versions.add(package.version)
            families.add(package.family)

        bestversion = None
        for version in versions:
            if bestversion is None or VersionCompare(version, bestversion) > 0:
                bestversion = version

        for package in packages:
            result = VersionCompare(package.version, bestversion) if bestversion is not None else 1
            if result > 0:
                package.versionclass = PackageVersionClass.ignored
            elif result == 0:
                package.versionclass = PackageVersionClass.newest
            else:
                package.versionclass = PackageVersionClass.outdated


def ProduceMetapackagesSummaries(metapackages):
    metasummaries = {}

    for name, packages in metapackages.items():
        metasummaries[name] = {}

        state_by_repo = {}
        families = set()

        for package in packages:
            if package.repo not in state_by_repo:
                state_by_repo[package.repo] = {
                    'newest': False,
                    'outdated': False,
                    'ignored': False,
                    'bestversion': None,
                    'count': 0
                }

            families.add(package.family)

            if package.versionclass == PackageVersionClass.ignored:
                state_by_repo[package.repo]['ignored'] = True,
            else:
                if package.versionclass == PackageVersionClass.newest:
                    state_by_repo[package.repo]['newest'] = True,
                if package.versionclass == PackageVersionClass.outdated:
                    state_by_repo[package.repo]['outdated'] = True,
                state_by_repo[package.repo]['bestversion'] = MaxVersion(state_by_repo[package.repo]['bestversion'], package.version)
                state_by_repo[package.repo]['count'] += 1

        for repo, state in state_by_repo.items():
            resulting_class = None

            if state['newest']:
                if len(families) == 1:
                    resulting_class = RepositoryVersionClass.lonely
                elif state['outdated']:
                    resulting_class = RepositoryVersionClass.mixed
                else:
                    resulting_class = RepositoryVersionClass.newest
            elif state['outdated']:
                resulting_class = RepositoryVersionClass.outdated
            elif state['ignored']:
                resulting_class = RepositoryVersionClass.ignored

            metasummaries[name][repo] = {
                'version': state['bestversion'],
                'versionclass': resulting_class,
                'numpackages': state['count']
            }

    return metasummaries
