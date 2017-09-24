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
    # helpers
    def AggregateBySameVersion(packages):
        current = None
        for package in packages:
            if current is None:
                current = [package]
            elif VersionCompare(current[0].version, package.version) == 0:
                current.append(package)
            else:
                yield current
                current = [package]

        if current is not None:
            yield current

    class BranchPrototype:
        __slots__ = ['versionclass', 'check']

        def __init__(self, versionclass, check):
            self.versionclass = versionclass
            self.check = check

        def Materialize(self, bestversion=None):
            return Branch(self.versionclass, bestversion)

    class Branch:
        __slots__ = ['versionclass', 'bestversion', 'lastversion']

        def __init__(self, versionclass, bestversion = None):
            self.versionclass = versionclass
            self.bestversion = bestversion
            self.lastversion = bestversion

        def SetLastVersion(self, lastversion):
            self.lastversion = lastversion

        def BestVersionCompare(self, version):
            return VersionCompare(version, self.bestversion) if self.bestversion is not None else 1

        def IsAfterBranch(self, version):
            return VersionCompare(version, self.lastversion) == -1 if self.lastversion is not None else False

    # we always work on packages sorted by version
    packages = PackagesetSortByVersions(packages)

    # possible branches
    default_branch = BranchPrototype(VersionClass.newest, lambda package: not package.devel)

    branch_prototypes = [
        BranchPrototype(VersionClass.devel, lambda package: package.devel),
        default_branch,
    ]

    # first, determine best version for each branch and # of families
    branches = []
    families = set()
    packages_by_repo = {}
    current_branch = None
    for verpackages in AggregateBySameVersion(packages):
        has_non_ignored = False
        matching_branches = set()

        for package in verpackages:
            families.add(package.family)
            packages_by_repo.setdefault(package.repo, []).append(package)

            if not package.ignoreversion:
                has_non_ignored = True

            for nbranch in range(0, len(branch_prototypes)):
                if branch_prototypes[nbranch].check(package):
                    matching_branches.add(nbranch)

        nbranch = list(matching_branches)[0] if len(matching_branches) == 1 else 1

        if nbranch == current_branch:
            branches[-1].SetLastVersion(verpackages[0].version)
        elif (current_branch is None or nbranch > current_branch) and has_non_ignored:
            branches.append(branch_prototypes[nbranch].Materialize(verpackages[0].version))
            current_branch = nbranch

    # handle unique package
    metapackage_is_unique = len(families) == 1

    # we should always have at least one branch
    if not branches:
        branches = [default_branch.Materialize(None)]

    # now fill in classes
    for repo, repo_packages in packages_by_repo.items():
        current_branch = 0
        first_in_branch = True

        for package in repo_packages:  # these are still sorted by version
            # switch to next branch when it's time
            while current_branch < len(branches) - 1 and branches[current_branch].IsAfterBranch(package.version):
                current_branch += 1
                first_in_branch = True

            current_comparison = branches[current_branch].BestVersionCompare(package.version)

            if current_comparison > 0:
                package.versionclass = VersionClass.ignored
            elif current_comparison == 0:
                package.versionclass = VersionClass.unique if metapackage_is_unique else branches[current_branch].versionclass
                first_in_branch = False
            else:
                package.versionclass = VersionClass.outdated if first_in_branch else VersionClass.legacy
                first_in_branch = False


def PackagesetToBestByRepo(packages):
    state_by_repo = {}

    for package in PackagesetSortByVersions(packages):
        if package.repo not in state_by_repo or (state_by_repo[package.repo].versionclass == VersionClass.ignored and package.versionclass != VersionClass.ignored):
            state_by_repo[package.repo] = package

    return state_by_repo


def PackagesetSortByVersions(packages):
    def packages_version_cmp_reverse(p1, p2):
        return VersionCompare(p2.version, p1.version)

    return sorted(packages, key=cmp_to_key(packages_version_cmp_reverse))


def PackagesetToFamilies(packages):
    return set([package.family for package in packages])


def PackagesetAggregateByVersions(packages, classmap={}):
    def MapClass(versionclass):
        return classmap.get(versionclass, versionclass)

    versions = {}
    for package in packages:
        key = (package.version, MapClass(package.versionclass))
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
