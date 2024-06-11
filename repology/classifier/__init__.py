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

from collections import defaultdict
from functools import cmp_to_key
from typing import Iterable, Iterator, Sequence, cast

from repology.classifier.group import group_packages
from repology.classifier.section import Section, generate_sections
from repology.package import Package, PackageFlags, PackageStatus


__all__ = ['classify_packages']


def _classify_packages_inner(packages: Iterable[Package], project_is_unique: bool, suppress_ignore: bool) -> None:
    # preparation
    groups = list(group_packages(packages, suppress_ignore=suppress_ignore))

    sections = generate_sections()

    best_package_in_branch: dict[str | None, Package] = {}
    packages_by_repo: dict[str, list[tuple[Package, Section]]] = defaultdict(list)

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
        first_package_in_section: dict[str, Package] = {}  # by flavor
        first_package_in_branch: dict[tuple[str | None, str], Package] = {}  # by branch, flavor

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


def _is_packageset_unique(packages: Sequence[Package]) -> bool:
    if len(packages) <= 1:
        return True

    for package in packages[1:]:
        if package.family != packages[0].family:
            return False

    return True


def _is_nix_mixed_snapshot_schemes_case(packages: Sequence[Package]) -> bool:
    # hack/special case: nix has changed snapshot scheme from YYYY-MM-DD to
    # 0-unstable-YYYY-MM-DD since the former compares as greater, we can't
    # suppress ignore for nix, as it would make older snapshots outdated
    # newer ones
    has_old_scheme = False
    has_new_scheme = False
    if packages[0].family == 'nix':
        for package in packages:
            if package.version.startswith('20'):
                has_old_scheme = True
            elif package.version.startswith('0-unstable-'):
                has_new_scheme = True

    return has_old_scheme and has_new_scheme


def _should_suppress_ignore(packages: Sequence[Package]) -> bool:
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

    if _is_nix_mixed_snapshot_schemes_case(packages):
        return False

    return True


def _sort_packages_by_version(packages: Iterable[Package]) -> list[Package]:
    """Sort an iterable of packages by version."""
    def compare(p1: Package, p2: Package) -> int:
        return p2.version_compare(p1)

    return sorted(packages, key=cmp_to_key(compare))


def _preprocess_packages(packages: Iterable[Package]) -> Iterator[Package]:
    """Preprocess an iterable of packages.

    Here we process packages which don't require complex
    version comparison logic and may be classified right
    away. `versionclass` is set immediately for these and
    they are excluded from the output.
    """
    for package in packages:
        if package.has_flag(PackageFlags.ROLLING):
            package.versionclass = PackageStatus.ROLLING
        else:
            yield package


def classify_packages(packages: Sequence[Package]) -> None:
    """Classify package statuses.

    Fill `versionclass` field of given packages.
    """
    # Determine of package is unique, e.g. we need to use `unique`
    # status instead of `newest`.
    is_unique = _is_packageset_unique(packages)

    # Preprocess and sort packages for further processing.
    packages = _sort_packages_by_version(_preprocess_packages(packages))

    # Check a special case when all given packages are ignored,
    # but belong to a single family - in such case we may
    # reset ignored status and allow normal version classification
    # in hope that due to packages coming from a single origin,
    # versions are of the same format and may be compared meaningfully.
    suppress_ignore = _should_suppress_ignore(packages)

    # Process altscheme and normal packages independently.
    altscheme_packages = [package for package in packages if package.flags & PackageFlags.ALTSCHEME]
    if altscheme_packages:
        _classify_packages_inner(altscheme_packages, is_unique, suppress_ignore)

    normal_packages = [package for package in packages if not package.flags & PackageFlags.ALTSCHEME]
    if normal_packages:
        _classify_packages_inner(normal_packages, is_unique, suppress_ignore)
