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
from dataclasses import dataclass, field
from functools import cmp_to_key
from typing import Callable, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple, cast

from repology.package import Package, PackageFlags, PackageStatus


def packageset_deduplicate(packages: Sequence[Package]) -> List[Package]:
    aggregated: Dict[Tuple[str, Optional[str], Optional[str], str], List[Package]] = defaultdict(list)

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


def is_packageset_unique(packages: Sequence[Package]) -> bool:
    if len(packages) <= 1:
        return True

    for package in packages[1:]:
        if package.family != packages[0].family:
            return False

    return True


def should_suppress_ignore(packages: Sequence[Package]) -> bool:
    if len(packages) <= 1:
        return True

    for package in packages:
        # condition 1: must be unique
        if package.family != packages[0].family:
            return False
        # condition 2: must consist of ignored packages only
        if not package.has_flag(PackageFlags.ANY_IGNORED):
            return False
        # condition 3: must not be noscheme
        if package.has_flag(PackageFlags.NOSCHEME):
            return False

    return True


def aggregate_by_same_version(packages: Iterable[Package]) -> Iterable[List[Package]]:
    current: List[Package] = []

    for package in packages:
        if not current:
            current = [package]
        elif current[0].version_compare(package) == 0:
            current.append(package)
        else:
            yield current
            current = [package]

    if current:
        yield current


@dataclass
class VersionGroup:
    all_flags: int = 0
    is_devel: bool = False
    totally_ignored: bool = False
    packages: list[Package] = field(default_factory=list)
    branches: set[Optional[str]] = field(default_factory=set)


def group_packages(packages: Sequence[Package], suppress_ignore: bool = True) -> Iterator[VersionGroup]:
    for verpackages in aggregate_by_same_version(packages):
        all_flags = 0
        has_non_devel = False
        totally_ignored = not suppress_ignore
        branches = set()

        for package in verpackages:
            all_flags |= package.flags

            if not package.has_flag(PackageFlags.ANY_IGNORED):
                totally_ignored = False

            if not package.has_flag(PackageFlags.DEVEL | PackageFlags.WEAK_DEVEL):
                has_non_devel = True

            branches.add(package.branch)

        if all_flags & PackageFlags.RECALLED:
            totally_ignored = True

        is_devel = cast(
            bool,
            (
                all_flags & PackageFlags.DEVEL or (
                    all_flags & PackageFlags.WEAK_DEVEL and not has_non_devel
                )
            ) and not all_flags & PackageFlags.STABLE
        )

        yield VersionGroup(
            all_flags=all_flags,
            is_devel=is_devel,
            totally_ignored=totally_ignored,
            packages=verpackages,
            branches=branches,
        )


@dataclass
class Section:
    GuardFn = Callable[[VersionGroup], bool]

    name: str
    newest_status: int
    guard: Optional[GuardFn] = None
    next_section: Optional['Section'] = None

    first_package: Optional[Package] = None
    first_package_alt: Optional[Package] = None
    last_package: Optional[Package] = None

    def add_package(self, package: Package, alt: bool = False) -> None:
        if self.first_package_alt is None:
            self.first_package_alt = package
        if self.first_package is None and not alt:
            self.first_package = package

        self.last_package = package

    def preceeds_package(self, package: Package) -> bool:
        return self.last_package.version_compare(package) > 0 if self.last_package else False

    def follows_package(self, package: Package, alt: bool = False) -> bool:
        first_package = self.first_package_alt if alt else self.first_package
        return first_package.version_compare(package) < 0 if first_package else False

    def contains_package(self, package: Package, alt: bool = False) -> bool:
        first_package = self.first_package_alt if alt else self.first_package
        return (
            first_package is not None
            and first_package.version_compare(package) >= 0
            and self.last_package.version_compare(package) <= 0  # type: ignore  # (last_package is always set if any of first_package* is)
        )

    def is_empty(self) -> bool:
        return self.last_package is None

    def compared_to_best(self, package: Package, alt: bool = False) -> int:
        if alt:
            return package.version_compare(self.first_package_alt) if self.first_package_alt else 1
        else:
            return package.version_compare(self.first_package) if self.first_package else 1

    def is_suitable_for_group(self, group: VersionGroup) -> bool:
        return not self.guard or self.guard(group)

    def get_next_section(self) -> 'Section':
        assert(self.next_section)
        return self.next_section

    def __repr__(self) -> str:
        if self.first_package is not None and self.first_package is self.first_package_alt:
            assert(self.last_package)
            return f'Section("{self.name}", versions=[{self.first_package.version}, {self.last_package.version}])'
        elif self.first_package is not None:
            assert(self.last_package)
            assert(self.first_package_alt)
            return f'Section("{self.name}", versions=[{self.first_package.version} ({self.first_package_alt.version}), {self.last_package.version}])'
        elif self.first_package_alt is not None:
            assert(self.last_package)
            return f'Section("{self.name}", versions=[({self.first_package_alt.version}), {self.last_package.version}])'
        else:
            return f'Section("{self.name}", empty)'


def generate_sections() -> List[Section]:
    sections = [
        Section(
            'devel',
            PackageStatus.DEVEL,
            lambda section: section.is_devel
        ),
        Section(
            'stable',
            PackageStatus.NEWEST,
        ),
    ]

    for section, next_section in zip(sections, sections[1:]):
        section.next_section = next_section

    # last section must not have a guard as there's no more
    # sections to fall through to
    assert sections[-1].guard is None

    return sections


def _fill_packageset_versions(packages: Sequence[Package], project_is_unique: bool, suppress_ignore: bool) -> None:
    # preparation
    groups = list(group_packages(packages, suppress_ignore=suppress_ignore))

    sections = generate_sections()

    best_package_in_branch: Dict[Optional[str], Package] = {}
    packages_by_repo: Dict[str, list[tuple[Package, Section]]] = defaultdict(list)

    # Pass 1: calculate section boundaries based on not ignored versions
    current_section = sections[0]
    for group in (group for group in groups if not group.totally_ignored):
        for branch in group.branches:
            if branch not in best_package_in_branch and not group.is_devel:
                best_package_in_branch[branch] = group.packages[0]

        while not current_section.is_suitable_for_group(group):
            current_section = current_section.get_next_section()

        current_section.add_package(group.packages[0], cast(bool, group.all_flags & PackageFlags.ALTVER))

    # Pass 2: assign sections for all groups
    current_section = sections[0]
    for group in groups:
        while not (
            current_section.contains_package(group.packages[0], cast(bool, group.all_flags & PackageFlags.ALTVER))
            or current_section.is_suitable_for_group(group)
            or current_section.follows_package(group.packages[0], cast(bool, group.all_flags & PackageFlags.ALTVER))
        ):
            current_section = current_section.get_next_section()

        for package in group.packages:
            packages_by_repo[package.repo].append((package, current_section))

    # Pass 3: fill version classes
    for repo, repo_packages in packages_by_repo.items():
        first_package_in_section: Dict[str, Package] = {}  # by flavor
        first_package_in_branch: Dict[Tuple[Optional[str], str], Package] = {}  # by branch, flavor

        prev_section = None
        for package, section in repo_packages:  # these are still sorted by version
            if section is not prev_section:
                # handle section change
                first_package_in_section = {}
                prev_section = section

            current_comparison = section.compared_to_best(package, cast(bool, package.flags & PackageFlags.ALTVER))

            if current_comparison > 0:
                # Note that the order here determines class priority when multiple
                # flags are present
                # - noscheme beats everything else - if there's no versioning scheme,
                #   it's meaningless to talk about any kind of version correctness
                # - incorrect beats untrusted as more specific
                # - ignored is most generic
                # - without any ignored status, treat as outdated
                if package.has_flag(PackageFlags.NOSCHEME):
                    package.versionclass = PackageStatus.NOSCHEME
                elif package.has_flag(PackageFlags.INCORRECT):
                    package.versionclass = PackageStatus.INCORRECT
                elif package.has_flag(PackageFlags.UNTRUSTED):
                    package.versionclass = PackageStatus.UNTRUSTED
                elif package.has_flag(PackageFlags.IGNORE):
                    package.versionclass = PackageStatus.IGNORED
                else:
                    package.versionclass = PackageStatus.OUTDATED
            else:
                flavor = '_'.join(package.flavors)  # already sorted and unicalized in RepoProcessor
                branch_key = (package.branch, flavor)

                if current_comparison == 0:
                    package.versionclass = PackageStatus.UNIQUE if project_is_unique else section.newest_status
                else:
                    non_first_in_section = (
                        flavor in first_package_in_section
                        and first_package_in_section[flavor].version_compare(package) != 0
                    )

                    first_but_not_best_in_branch = (
                        (
                            branch_key not in first_package_in_branch
                            or first_package_in_branch[branch_key].version_compare(package) == 0
                        )
                        and package.branch in best_package_in_branch
                        and best_package_in_branch[package.branch].version_compare(package) > 0
                    )

                    legacy_allowed = (
                        (
                            non_first_in_section
                            and not first_but_not_best_in_branch
                            and not package.has_flag(PackageFlags.NOLEGACY)
                        ) or package.has_flag(PackageFlags.LEGACY)
                    )

                    package.versionclass = PackageStatus.LEGACY if legacy_allowed else PackageStatus.OUTDATED

                if flavor not in first_package_in_section:
                    first_package_in_section[flavor] = package

                if branch_key is not None and branch_key not in first_package_in_branch:
                    first_package_in_branch[branch_key] = package

            if package.has_flag(PackageFlags.OUTDATED) and package.versionclass in (PackageStatus.UNIQUE, PackageStatus.NEWEST, PackageStatus.DEVEL):
                package.versionclass = PackageStatus.OUTDATED


def fill_packageset_versions(packages: Sequence[Package]) -> None:
    # global flags #1
    is_unique = is_packageset_unique(packages)

    # preprocessing: rolling versions
    packages_to_process = []

    for package in packages:
        if package.has_flag(PackageFlags.ROLLING):
            package.versionclass = PackageStatus.ROLLING
        else:
            packages_to_process.append(package)

    # we always work on packages sorted by version
    packages = packageset_sort_by_version(packages_to_process)

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
    suppress_ignore = should_suppress_ignore(packages)

    # Process altscheme and normal packages independently
    altscheme_packages = [package for package in packages if package.flags & PackageFlags.ALTSCHEME]
    if altscheme_packages:
        _fill_packageset_versions(altscheme_packages, is_unique, suppress_ignore)

    normal_packages = [package for package in packages if not package.flags & PackageFlags.ALTSCHEME]
    if normal_packages:
        _fill_packageset_versions(normal_packages, is_unique, suppress_ignore)


def packageset_sort_by_version(packages: Sequence[Package]) -> List[Package]:
    def compare(p1: Package, p2: Package) -> int:
        return p2.version_compare(p1)

    return sorted(packages, key=cmp_to_key(compare))
