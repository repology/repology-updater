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

from repology.version import VersionCompare


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

    def __init__(self, **args):
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

        for k, v in args.items():
            setattr(self, k, v)

    @property
    def __dict__(self):
        return {slot: getattr(self, slot) for slot in self.__slots__}


def MergeMetapackages(*packagesets):
    metapackages = {}

    for packageset in packagesets:
        for package in packageset:
            if package.effname not in metapackages:
                metapackages[package.effname] = []
            metapackages[package.effname].append(package)

    return metapackages


def CheckFilters(packages, *filters):
    for filt in filters:
        if not filt.Check(packages):
            return False

    return True


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


def FillVersionInfos(packages):
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


def FillMetapackagesVersionInfos(metapackages):
    for packages in metapackages.values():
        FillVersionInfos(packages)


def ProduceRepositorySummary(packages):
    summary = {}

    state_by_repo = {}
    families = set()

    for package in packages:
        families.add(package.family)

        if package.repo not in state_by_repo:
            state_by_repo[package.repo] = {
                'has_outdated': False,
                'bestpackage': None,
                'count': 0
            }

        if package.versionclass == PackageVersionClass.outdated:
            state_by_repo[package.repo]['has_outdated'] = True,

        if state_by_repo[package.repo]['bestpackage'] is None or VersionCompare(package.version, state_by_repo[package.repo]['bestpackage'].version) > 0:
            state_by_repo[package.repo]['bestpackage'] = package

        state_by_repo[package.repo]['count'] += 1

    for repo, state in state_by_repo.items():
        resulting_class = None

        # XXX: lonely ignored package is currently lonely; should it be ignored instead?
        if state['bestpackage'].versionclass == PackageVersionClass.outdated:
            resulting_class = RepositoryVersionClass.outdated
        elif len(families) == 1:
            resulting_class = RepositoryVersionClass.lonely
        elif state['bestpackage'].versionclass == PackageVersionClass.newest:
            if state['has_outdated']:
                resulting_class = RepositoryVersionClass.mixed
            else:
                resulting_class = RepositoryVersionClass.newest
        elif state['bestpackage'].versionclass == PackageVersionClass.ignored:
            resulting_class = RepositoryVersionClass.ignored

        summary[repo] = {
            'version': state['bestpackage'].version,
            'bestpackage': state['bestpackage'],
            'versionclass': resulting_class,
            'numpackages': state['count']
        }

    return summary


def ProduceMetapackagesRepositorySummaries(metapackages):
    summaries = {}

    for name, packages in metapackages.items():
        summaries[name] = ProduceRepositorySummary(packages)

    return summaries
