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

import sys

from functools import cmp_to_key

from repology.package import *
from repology.version import VersionCompare


def PackagesMerge(packages):
    aggregated = {}

    # aggregate by subrepo/name/version
    # this is just to make merging faster, as packages
    # with same subrepo/name/version may or may not merge
    for package in packages:
        key = (package.subrepo, package.name, package.version)
        aggregated.setdefault(key, []).append(package)

    outpkgs = []
    for packages in aggregated.values():
        while packages:
            nextpackages = []
            merged = packages[0]
            for package in packages[1:]:
                if not merged.TryMerge(package):
                    nextpackages.append(package)

            outpkgs.append(merged)
            packages = nextpackages

    return outpkgs


def PackagesetCheckFilters(packages, *filters):
    for filt in filters:
        if not filt.Check(packages):
            return False

    return True


def FillPackagesetVersions(packages):
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
            # XXX: if len(families) == 1 -> PackageVersionClass.unique
            package.versionclass = PackageVersionClass.newest
        else:
            package.versionclass = PackageVersionClass.outdated


def PackagesetToSummaries(packages):
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


def PackagesetSortByVersions(packages):
    def packages_version_cmp_reverse(p1, p2):
        return VersionCompare(p2.version, p1.version)

    return sorted(packages, key=cmp_to_key(packages_version_cmp_reverse))


def PackagesetToFamilies(packages):
    return set([package.family for package in packages])


def PackagesetAggregateByVersions(packages):
    versions = {}
    for package in packages:
        key = (package.version, package.versionclass)
        if key not in versions:
            versions[key] = []
        versions[key].append(package)

    def key_cmp_reverse(v1, v2):
        return VersionCompare(v2[0], v1[0])

    return [
        {
            'version': key[0],
            'versionclass': key[1],
            'packages': versions[key]
        } for key in sorted(versions.keys(), key=cmp_to_key(key_cmp_reverse))
    ]
