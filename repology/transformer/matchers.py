# Copyright (C) 2018-2021 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
from typing import Any, Callable, Final, cast

from libversion import LOWER_BOUND, UPPER_BOUND, version_compare

from repology.package import LinkType, Package, PackageFlags
from repology.transformer.contexts import MatchContext, PackageContext
from repology.transformer.util import yaml_as_list, yaml_as_lowercase_list, yaml_as_lowercase_set, yaml_as_set


__all__ = ['get_matcher_generators']


# types
Matcher = Callable[[Package, PackageContext, MatchContext], bool]
MatcherGenerator = Callable[[Any], Matcher]


# machinery for matcher registration
_matcher_generators: list[tuple[str, MatcherGenerator]] = []


def get_matcher_generators() -> list[tuple[str, MatcherGenerator]]:
    return _matcher_generators


def _matcher_generator(func: MatcherGenerator) -> MatcherGenerator:
    _matcher_generators.append((func.__name__, func))
    return func


# matchers
@_matcher_generator
def category(ruledata: Any) -> Matcher:
    categories = yaml_as_lowercase_set(ruledata['category'])

    def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
        return bool(package.category and package.category.lower() in categories)

    return matcher


@_matcher_generator
def categorypat(ruledata: Any) -> Matcher:
    categorypat_re = re.compile(ruledata['categorypat'].replace('\n', '').lower(), re.ASCII)

    def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
        return categorypat_re.fullmatch(package.category.lower()) is not None if package.category else False

    return matcher


@_matcher_generator
def maintainer(ruledata: Any) -> Matcher:
    maintainers = yaml_as_lowercase_set(ruledata['maintainer'])

    def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
        return package.maintainers is not None and not maintainers.isdisjoint(set((m.lower() for m in package.maintainers)))

    return matcher


@_matcher_generator
def name(ruledata: Any) -> Matcher:
    names = yaml_as_list(ruledata['name'])

    if len(names) == 1:
        name_to_check = names[0]

        def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
            return package.effname == name_to_check

        return matcher
    else:
        names_to_check = set(names)

        def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
            return package.effname in names_to_check

        return matcher


@_matcher_generator
def namepat(ruledata: Any) -> Matcher:
    namepat_re = re.compile(ruledata['namepat'].replace('\n', ''), re.ASCII)

    def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
        match = namepat_re.fullmatch(package.effname)
        if match is not None:
            match_context.name_match = match
            return True
        return False

    return matcher


@_matcher_generator
def ver(ruledata: Any) -> Matcher:
    versions = yaml_as_set(ruledata['ver'])

    if len(versions) == 1:
        version = versions.pop()

        def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
            return package.version == version

        return matcher
    else:
        def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
            return package.version in versions

        return matcher


@_matcher_generator
def notver(ruledata: Any) -> Matcher:
    notversions = yaml_as_set(ruledata['notver'])

    if len(notversions) == 1:
        notversion: Final[str] = notversions.pop()

        def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
            return package.version != notversion

        return matcher
    else:
        def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
            return package.version not in notversions

        return matcher


@_matcher_generator
def verpat(ruledata: Any) -> Matcher:
    verpat: Final = re.compile(ruledata['verpat'].replace('\n', '').lower(), re.ASCII)

    def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
        match = verpat.fullmatch(package.version.lower())
        if match is not None:
            match_context.ver_match = match
            return True
        return False

    return matcher


@_matcher_generator
def verlonger(ruledata: Any) -> Matcher:
    verlonger: Final[int] = ruledata['verlonger']

    def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
        return len(re.split('[^a-zA-Z0-9]', package.version)) > verlonger

    return matcher


@_matcher_generator
def vercomps(ruledata: Any) -> Matcher:
    vercomps: Final[int] = ruledata['vercomps']

    def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
        return len(re.split('[^a-zA-Z0-9]', package.version)) == vercomps

    return matcher


# ver* matchers
@_matcher_generator
def vergt(ruledata: Any) -> Matcher:
    vergt: Final[str] = ruledata['vergt']

    def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
        return version_compare(package.version, vergt) > 0

    return matcher


@_matcher_generator
def verge(ruledata: Any) -> Matcher:
    verge: Final[str] = ruledata['verge']

    def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
        return version_compare(package.version, verge) >= 0

    return matcher


@_matcher_generator
def verlt(ruledata: Any) -> Matcher:
    verlt: Final[str] = ruledata['verlt']

    def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
        return version_compare(package.version, verlt) < 0

    return matcher


@_matcher_generator
def verle(ruledata: Any) -> Matcher:
    verle: Final[str] = ruledata['verle']

    def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
        return version_compare(package.version, verle) <= 0

    return matcher


@_matcher_generator
def vereq(ruledata: Any) -> Matcher:
    vereq: Final[str] = ruledata['vereq']

    def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
        return version_compare(package.version, vereq) == 0

    return matcher


@_matcher_generator
def verne(ruledata: Any) -> Matcher:
    verne: Final[str] = ruledata['verne']

    def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
        return version_compare(package.version, verne) != 0

    return matcher


# rel* matchers
@_matcher_generator
def relgt(ruledata: Any) -> Matcher:
    relgt: Final[str] = ruledata['relgt']

    def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
        return version_compare(package.version, relgt, 0, UPPER_BOUND) > 0

    return matcher


@_matcher_generator
def relge(ruledata: Any) -> Matcher:
    relge: Final[str] = ruledata['relge']

    def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
        return version_compare(package.version, relge, 0, LOWER_BOUND) > 0

    return matcher


@_matcher_generator
def rellt(ruledata: Any) -> Matcher:
    rellt: Final[str] = ruledata['rellt']

    def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
        return version_compare(package.version, rellt, 0, LOWER_BOUND) < 0

    return matcher


@_matcher_generator
def relle(ruledata: Any) -> Matcher:
    relle: Final[str] = ruledata['relle']

    def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
        return version_compare(package.version, relle, 0, UPPER_BOUND) < 0

    return matcher


@_matcher_generator
def releq(ruledata: Any) -> Matcher:
    releq = cast(str, ruledata['releq'])

    def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
        return version_compare(package.version, releq, 0, LOWER_BOUND) > 0 and version_compare(package.version, releq, 0, UPPER_BOUND) < 0

    return matcher


@_matcher_generator
def relne(ruledata: Any) -> Matcher:
    relne = cast(str, ruledata['relne'])

    def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
        return version_compare(package.version, relne, 0, LOWER_BOUND) < 0 or version_compare(package.version, relne, 0, UPPER_BOUND) > 0

    return matcher


# www* matchers
@_matcher_generator
def wwwpat(ruledata: Any) -> Matcher:
    wwwpat = re.compile(ruledata['wwwpat'].replace('\n', '').lower(), re.ASCII)

    def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
        if package.links is not None:
            for link_type, url in package.links:
                if LinkType.is_relevant_for_rule_matching(link_type) and wwwpat.fullmatch(url):
                    return True

        return False

    return matcher


@_matcher_generator
def wwwpart(ruledata: Any) -> Matcher:
    wwwparts = yaml_as_lowercase_list(ruledata['wwwpart'])

    def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
        if package.links is not None:
            for link_type, url in package.links:
                lower_url = url.lower()
                if LinkType.is_relevant_for_rule_matching(link_type):
                    for wwwpart in wwwparts:
                        if wwwpart in lower_url:
                            return True

        return False

    return matcher


@_matcher_generator
def summpart(ruledata: Any) -> Matcher:
    summparts = yaml_as_lowercase_list(ruledata['summpart'])

    def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
        if not package.comment:
            return False
        for summpart in summparts:
            if summpart in package.comment.lower():
                return True
        return False

    return matcher


@_matcher_generator
def flag(ruledata: Any) -> Matcher:
    flags = yaml_as_set(ruledata['flag'])

    def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
        return package_context.has_flags(flags)

    return matcher


@_matcher_generator
def noflag(ruledata: Any) -> Matcher:
    noflags = yaml_as_set(ruledata['noflag'])

    def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
        return not package_context.has_flags(noflags)

    return matcher


@_matcher_generator
def hasbranch(ruledata: Any) -> Matcher:
    hasbranch = cast(bool, ruledata['hasbranch'])

    def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
        return (package.branch is not None) == hasbranch

    return matcher


@_matcher_generator
def is_p_is_patch(ruledata: Any) -> Matcher:
    is_p_is_patch = cast(bool, ruledata['is_p_is_patch'])

    def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
        return package.has_flag(PackageFlags.P_IS_PATCH) == is_p_is_patch

    return matcher
