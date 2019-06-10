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

from collections import defaultdict
from functools import cmp_to_key
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from repology.package import Package, PackageFlags, PackageStatus


def PackagesetDeduplicate(packages: Sequence[Package]) -> List[Package]:
    aggregated: Dict[Tuple[str, Optional[str], str, str], List[Package]] = defaultdict(list)

    # aggregate by subset of fields to make O(n²) merge below faster
    for package in packages:
        key = (package.repo, package.subrepo, package.name, package.version)
        aggregated[key].append(package)

    outpkgs = []
    for packages in aggregated.values():
        while packages:
            nextpackages = []
            for package in packages[1:]:
                if package != packages[0]:
                    nextpackages.append(package)

            outpkgs.append(packages[0])
            packages = nextpackages

    return outpkgs


def packageset_is_unique(packages: Sequence[Package]) -> bool:
    if len(packages) <= 1:
        return True

    for package in packages[1:]:
        if package.family != packages[0].family:
            return False

    return True


def packageset_may_be_unignored(packages: Sequence[Package]) -> bool:
    if len(packages) <= 1:
        return True

    for package in packages:
        # condition 1: must be unique
        if package.family != packages[0].family:
            return False
        # condition 2: must consist of ignored packages only
        if not package.HasFlag(PackageFlags.ANY_IGNORED):
            return False

    return True


def FillPackagesetVersions(packages: Sequence[Package]) -> None:
    # helpers
    def AggregateBySameVersion(packages: Iterable[Package]) -> Iterable[List[Package]]:
        current: List[Package] = []

        for package in packages:
            if not current:
                current = [package]
            elif current[0].VersionCompare(package) == 0:
                current.append(package)
            else:
                yield current
                current = [package]

        if current:
            yield current

    class Branch:
        __slots__ = ['versionclass', 'bestpackage', 'lastpackage']

        versionclass: int
        bestpackage: Optional[Package]
        lastpackage: Optional[Package]

        def __init__(self, versionclass: int, bestpackage: Optional[Package] = None):
            self.versionclass = versionclass
            self.bestpackage = bestpackage
            self.lastpackage = bestpackage

        def SetLastPackage(self, lastpackage: Package) -> None:
            self.lastpackage = lastpackage

        def BestPackageCompare(self, package: Package) -> int:
            return package.VersionCompare(self.bestpackage) if self.bestpackage is not None else 1

        def IsAfterBranch(self, package: Package) -> bool:
            return package.VersionCompare(self.lastpackage) == -1 if self.lastpackage is not None else False

    class BranchPrototype:
        __slots__ = ['_versionclass', '_check']

        _versionclass: int
        #_check: Callable[[Package], bool]  # mypy goes mad

        def __init__(self, versionclass: int, check: Callable[[Package], bool]) -> None:
            self._versionclass = versionclass
            self._check = check

        def Check(self, package: Package) -> bool:
            return self._check(package)

        def CreateBranch(self, bestpackage: Optional[Package] = None) -> 'Branch':
            return Branch(self._versionclass, bestpackage)

    # global flags #1
    metapackage_is_unique = packageset_is_unique(packages)

    # preprocessing: rolling versions
    packages_to_process = []

    for package in packages:
        if package.HasFlag(PackageFlags.ROLLING):
            package.versionclass = PackageStatus.ROLLING
        else:
            packages_to_process.append(package)

    # we always work on packages sorted by version
    packages = PackagesetSortByVersion(packages_to_process)

    # global flags #2

    # The idea here is that if package versions are compared only within a single family
    # (so this is calculated after rolling packages are removed, since they do not
    # participate in comparison), and all versions are ignored, it makes sense to unignore
    # them, because unique/latest/outdated versions are more informative than just ignored
    # (the best part is actually a possibility of outdated packages)
    #
    # Actually, this is a hack to partially revert the effect of global ignore of .*git.*
    # versions. That is why I couldn't decide on whether only `ignored` status or all ignored-
    # like statuses may be unignored.
    #
    # The proper solution would be to allow rules decide whether they may be unignored. This,
    # however, brings in more complex flag handling, as in `soft` and `hard` ignores, so I'd
    # like to postpone it for now
    metapackage_should_unignore = packageset_may_be_unignored(packages)

    # branch prototypes
    default_branchproto = BranchPrototype(PackageStatus.NEWEST, lambda package: True)

    branchprotos = [
        BranchPrototype(PackageStatus.DEVEL, lambda package: package.HasFlag(PackageFlags.DEVEL)),
        default_branchproto,
    ]

    default_branchproto_idx = branchprotos.index(default_branchproto)

    #
    # Pass 1: discover branches
    #
    branches: List[Branch] = []
    packages_by_repo: Dict[str, List[Package]] = defaultdict(list)
    current_branchproto_idx = None
    for verpackages in AggregateBySameVersion(packages):
        version_totally_ignored = True
        matching_branchproto_indexes = set()

        if metapackage_should_unignore:
            version_totally_ignored = False

        for package in verpackages:
            packages_by_repo[package.repo].append(package)

            if not package.HasFlag(PackageFlags.ANY_IGNORED):
                version_totally_ignored = False

            for branchproto_idx in range(0, len(branchprotos)):
                if branchprotos[branchproto_idx].Check(package):
                    matching_branchproto_indexes.add(branchproto_idx)

        # if there's at least one package with a non-default branch, that branch is a candidate
        # if there's only one such candidate branch (not counting the default branch), choose it
        # this works when there are 1.0r1 (not devel) and 1.0rc1 (devel) versions
        matching_branchproto_indexes.discard(default_branchproto_idx)
        final_branchproto_idx = list(matching_branchproto_indexes)[0] if len(matching_branchproto_indexes) == 1 else default_branchproto_idx

        if final_branchproto_idx == current_branchproto_idx:
            branches[-1].SetLastPackage(verpackages[0])
        elif (current_branchproto_idx is None or final_branchproto_idx > current_branchproto_idx) and not version_totally_ignored:
            branches.append(branchprotos[final_branchproto_idx].CreateBranch(verpackages[0]))
            current_branchproto_idx = final_branchproto_idx

    # we should always have at least one branch
    if not branches:
        branches = [default_branchproto.CreateBranch()]

    #
    # Pass 2: fill version classes
    #
    for repo, repo_packages in packages_by_repo.items():
        current_branch_idx = 0
        first_package_in_branch_per_flavor: Dict[str, Package] = {}

        for package in repo_packages:  # these are still sorted by version
            # switch to next branch when the current one is over, but not past the last branch
            while current_branch_idx < len(branches) - 1 and branches[current_branch_idx].IsAfterBranch(package):
                current_branch_idx += 1
                first_package_in_branch_per_flavor = {}

            # chose version class based on comparison to branch best version
            current_comparison = branches[current_branch_idx].BestPackageCompare(package)

            if current_comparison > 0:
                # Note that the order here determines class priority when multiple
                # flags are present
                # - noscheme beats everything else - if there's no versioning scheme,
                #   it's meaningless to talk about any kind of version correctness
                # - incorrect beats untrusted as more specific
                # - everything else is generic ignored
                if package.HasFlag(PackageFlags.NOSCHEME):
                    package.versionclass = PackageStatus.NOSCHEME
                elif package.HasFlag(PackageFlags.INCORRECT):
                    package.versionclass = PackageStatus.INCORRECT
                elif package.HasFlag(PackageFlags.UNTRUSTED):
                    package.versionclass = PackageStatus.UNTRUSTED
                else:
                    package.versionclass = PackageStatus.IGNORED
            else:
                flavor = '_'.join(package.flavors)  # already sorted and unicalized in RepoProcessor

                if current_comparison == 0:
                    package.versionclass = PackageStatus.UNIQUE if metapackage_is_unique else branches[current_branch_idx].versionclass
                else:
                    non_first_in_branch = flavor in first_package_in_branch_per_flavor and first_package_in_branch_per_flavor[flavor].VersionCompare(package) != 0

                    if non_first_in_branch or package.HasFlag(PackageFlags.LEGACY):
                        package.versionclass = PackageStatus.LEGACY
                    else:
                        package.versionclass = PackageStatus.OUTDATED

                if flavor not in first_package_in_branch_per_flavor:
                    first_package_in_branch_per_flavor[flavor] = package


def PackagesetSortByVersion(packages: Sequence[Package]) -> List[Package]:
    def compare(p1: Package, p2: Package) -> int:
        return p2.VersionCompare(p1)

    return sorted(packages, key=cmp_to_key(compare))
