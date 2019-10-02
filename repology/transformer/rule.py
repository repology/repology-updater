# Copyright (C) 2018-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
from typing import AbstractSet, Any, Callable, Dict, Iterable, List, Match, MutableSet, Optional, Pattern, Set, TYPE_CHECKING

from libversion import LOWER_BOUND, UPPER_BOUND, version_compare

from repology.package import Package, PackageFlags

if TYPE_CHECKING:
    from typing_extensions import Final


DOLLAR0 = re.compile('\\$0', re.ASCII)
DOLLARN = re.compile('\\$([0-9])', re.ASCII)


class PackageContext:
    __slots__ = ['_flags', '_rulesets', 'warnings', 'matched_rules']

    _flags: MutableSet[str]
    _rulesets: MutableSet[str]
    warnings: List[str]
    matched_rules: List[int]

    def __init__(self) -> None:
        self._flags = set()
        self._rulesets = set()
        self.warnings = []
        self.matched_rules = []

    def add_flag(self, name: str) -> None:
        self._flags.add(name)

    def has_flag(self, name: str) -> bool:
        return name in self._flags

    def has_flags(self, names: AbstractSet[str]) -> bool:
        return not self._flags.isdisjoint(names)

    def has_rulesets(self, rulesets: AbstractSet[str]) -> bool:
        return not self._rulesets.isdisjoint(rulesets)

    def set_rulesets(self, rulesets: Iterable[str]) -> None:
        self._rulesets = set(rulesets)

    def add_warning(self, warning: str) -> None:
        self.warnings.append(warning)

    def add_matched_rule(self, ruleid: int) -> None:
        self.matched_rules.append(ruleid)


class MatchContext:
    __slots__ = ['name_match', 'ver_match', 'last']

    name_match: Optional[Match[str]]
    ver_match: Optional[Match[str]]
    last: bool

    def __init__(self) -> None:
        self.name_match = None
        self.ver_match = None
        self.last = False

    def sub_name_dollars(self, value: str, fullstr: str) -> str:
        if self.name_match is None:
            return DOLLAR0.sub(fullstr, value)

        def repl(matchobj: Match[str]) -> str:
            # mypy is unable to derive that self.name_match is always defined here
            return self.name_match.group(int(matchobj.group(1)))  # type: ignore

        return DOLLARN.sub(repl, value)

    def sub_ver_dollars(self, value: str, fullstr: str) -> str:
        if self.ver_match is None:
            return DOLLAR0.sub(fullstr, value)

        def repl(matchobj: Match[str]) -> str:
            return self.ver_match.group(int(matchobj.group(1)))  # type: ignore

        return DOLLARN.sub(repl, value)


class Rule:
    __slots__ = ['_matchers', '_actions', 'names', 'namepat', 'checks', 'matches', 'number', 'pretty']

    _matchers: List[Callable[[Package, PackageContext, MatchContext], bool]]
    _actions: List[Callable[[Package, PackageContext, MatchContext], None]]
    names: Optional[List[str]]
    namepat: Optional[str]
    checks: int
    matches: int
    number: int
    pretty: str

    def __init__(self, number: int, ruledata: Dict[str, Any]) -> None:
        self.names = None
        self.namepat = None
        self.number = number
        self.checks = 0
        self.matches = 0

        self.pretty = str(ruledata)

        self._matchers = []
        self._actions = []

        def as_list(val: Any) -> List[str]:
            if isinstance(val, list):
                return val
            elif isinstance(val, set):
                return list(val)
            else:
                return [val]

        def as_lowercase_list(val: Any) -> List[str]:
            return [v.lower() for v in as_list(val)]

        def as_set(val: Any) -> Set[str]:
            return set(as_list(val))

        def as_lowercase_set(val: Any) -> Set[str]:
            return set(as_lowercase_list(val))

        # These conditional blocks use local variables which are then captured by
        # nested functions. MAKE SURE that names for all these are unique, because
        # they are common to the whole function, and reusing the name for multiple
        # conditions or actions will break formerly defined ones

        # matchers
        if 'ruleset' in ruledata:
            rulesets: Final = as_set(ruledata['ruleset'])

            def ruleset_matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                return package_context.has_rulesets(rulesets)

            self._matchers.append(ruleset_matcher)

        if 'noruleset' in ruledata:
            norulesets: Final = as_set(ruledata['noruleset'])

            def noruleset_matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                return not package_context.has_rulesets(norulesets)

            self._matchers.append(noruleset_matcher)

        if 'category' in ruledata:
            categories: Final = as_lowercase_set(ruledata['category'])

            def category_matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                return bool(package.category and package.category.lower() in categories)

            self._matchers.append(category_matcher)

        if 'maintainer' in ruledata:
            maintainers: Final = as_lowercase_set(ruledata['maintainer'])

            def maintainer_matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                return not maintainers.isdisjoint(set((m.lower() for m in package.maintainers)))

            self._matchers.append(maintainer_matcher)

        if 'name' in ruledata:
            names = as_list(ruledata['name'])

            if 'setname' in ruledata:
                names = [DOLLAR0.sub(ruledata['setname'], name) for name in names]

            self.names = names

            if len(names) == 1:
                name_to_check: Final[str] = names[0]

                def name_matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                    return package.effname == name_to_check

                self._matchers.append(name_matcher)
            else:
                names_to_check: Final = set(names)

                def names_matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                    return package.effname in names_to_check

                self._matchers.append(names_matcher)

        if 'namepat' in ruledata:
            namepat = ruledata['namepat'].replace('\n', '')

            if 'setname' in ruledata:
                namepat = DOLLAR0.sub(ruledata['setname'], namepat)

            self.namepat = namepat
            namepat_re: Final[Pattern[str]] = re.compile(namepat, re.ASCII)

            def namepat_matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                match = namepat_re.fullmatch(package.effname)
                if match is not None:
                    match_context.name_match = match
                    return True
                return False

            self._matchers.append(namepat_matcher)

        if 'ver' in ruledata:
            versions: Final = as_set(ruledata['ver'])

            if len(versions) == 1:
                version: Final[str] = versions.pop()

                def ver_matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                    return package.version == version

                self._matchers.append(ver_matcher)
            else:
                def vers_matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                    return package.version in versions

                self._matchers.append(vers_matcher)

        if 'notver' in ruledata:
            notversions: Final = as_set(ruledata['notver'])

            if len(notversions) == 1:
                notversion: Final[str] = notversions.pop()

                def notver_matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                    return package.version != notversion

                self._matchers.append(notver_matcher)
            else:
                def notvers_matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                    return package.version not in notversions

                self._matchers.append(notvers_matcher)

        if 'verpat' in ruledata:
            verpat: Final = re.compile(ruledata['verpat'].replace('\n', '').lower(), re.ASCII)

            def verpat_matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                match = verpat.fullmatch(package.version.lower())
                if match is not None:
                    match_context.ver_match = match
                    return True
                return False

            self._matchers.append(verpat_matcher)

        if 'verlonger' in ruledata:
            verlonger: Final[int] = ruledata['verlonger']

            def verlonger_matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                return len(re.split('[^a-zA-Z0-9]', package.version)) > verlonger

            self._matchers.append(verlonger_matcher)

        # ver* matchers
        if 'vergt' in ruledata:
            vergt: Final[str] = ruledata['vergt']

            def vergt_matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                return version_compare(package.version, vergt) > 0

            self._matchers.append(vergt_matcher)

        if 'verge' in ruledata:
            verge: Final[str] = ruledata['verge']

            def verge_matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                return version_compare(package.version, verge) >= 0

            self._matchers.append(verge_matcher)

        if 'verlt' in ruledata:
            verlt: Final[str] = ruledata['verlt']

            def verlt_matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                return version_compare(package.version, verlt) < 0

            self._matchers.append(verlt_matcher)

        if 'verle' in ruledata:
            verle: Final[str] = ruledata['verle']

            def verle_matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                return version_compare(package.version, verle) <= 0

            self._matchers.append(verle_matcher)

        if 'vereq' in ruledata:
            vereq: Final[str] = ruledata['vereq']

            def vereq_matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                return version_compare(package.version, vereq) == 0

            self._matchers.append(vereq_matcher)

        if 'verne' in ruledata:
            verne: Final[str] = ruledata['verne']

            def verne_matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                return version_compare(package.version, verne) != 0

            self._matchers.append(verne_matcher)

        # rel* matchers
        if 'relgt' in ruledata:
            relgt: Final[str] = ruledata['relgt']

            def relgt_matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                return version_compare(package.version, relgt, 0, UPPER_BOUND) > 0

            self._matchers.append(relgt_matcher)

        if 'relge' in ruledata:
            relge: Final[str] = ruledata['relge']

            def relge_matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                return version_compare(package.version, relge, 0, LOWER_BOUND) > 0

            self._matchers.append(relge_matcher)

        if 'rellt' in ruledata:
            rellt: Final[str] = ruledata['rellt']

            def rellt_matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                return version_compare(package.version, rellt, 0, LOWER_BOUND) < 0

            self._matchers.append(rellt_matcher)

        if 'relle' in ruledata:
            relle: Final[str] = ruledata['relle']

            def relle_matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                return version_compare(package.version, relle, 0, UPPER_BOUND) < 0

            self._matchers.append(relle_matcher)

        if 'releq' in ruledata:
            releq: Final[str] = ruledata['releq']

            def releq_matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                return version_compare(package.version, releq, 0, LOWER_BOUND) > 0 and version_compare(package.version, releq, 0, UPPER_BOUND) < 0

            self._matchers.append(releq_matcher)

        if 'relne' in ruledata:
            relne: Final[str] = ruledata['relne']

            def relne_matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                return version_compare(package.version, relne, 0, LOWER_BOUND) < 0 or version_compare(package.version, relne, 0, UPPER_BOUND) > 0

            self._matchers.append(relne_matcher)

        # www* matchers
        if 'wwwpat' in ruledata:
            wwwpat: Final[Pattern[str]] = re.compile(ruledata['wwwpat'].replace('\n', '').lower(), re.ASCII)

            def wwwpat_matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                if package.homepage and wwwpat.fullmatch(package.homepage):
                    return True

                for download in package.downloads:
                    if wwwpat.fullmatch(download):
                        return True

                return False

            self._matchers.append(wwwpat_matcher)

        if 'wwwpart' in ruledata:
            wwwparts: Final = as_lowercase_list(ruledata['wwwpart'])

            def wwwpart_matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                if package.homepage:
                    for wwwpart in wwwparts:
                        if wwwpart in package.homepage.lower():
                            return True
                for download in package.downloads:
                    for wwwpart in wwwparts:
                        if wwwpart in download.lower():
                            return True
                return False

            self._matchers.append(wwwpart_matcher)

        if 'summpart' in ruledata:
            summparts: Final = as_lowercase_list(ruledata['summpart'])

            def summpart_matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                if not package.comment:
                    return False
                for summpart in summparts:
                    if summpart in package.comment.lower():
                        return True
                return False

            self._matchers.append(summpart_matcher)

        if 'flag' in ruledata:
            flags: Final = as_set(ruledata['flag'])

            def flag_matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                return package_context.has_flags(flags)

            self._matchers.append(flag_matcher)

        if 'noflag' in ruledata:
            noflags: Final = as_set(ruledata['noflag'])

            def noflag_matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                return not package_context.has_flags(noflags)

            self._matchers.append(noflag_matcher)

        if 'hasbranch' in ruledata:
            hasbranch: Final[bool] = ruledata['hasbranch']

            def hasbranch_matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                return (package.branch is not None) == hasbranch

            self._matchers.append(hasbranch_matcher)

        if 'is_p_is_patch' in ruledata:
            is_p_is_patch: Final[bool] = ruledata['is_p_is_patch']

            def is_p_is_patch_matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                return package.has_flag(PackageFlags.P_IS_PATCH) == is_p_is_patch

            self._matchers.append(is_p_is_patch_matcher)

        # actions
        if 'remove' in ruledata:
            remove_flag: Final[bool] = ruledata['remove']

            def remove_action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                package.set_flag(PackageFlags.REMOVE, remove_flag)

            self._actions.append(remove_action)

        if 'ignore' in ruledata:
            ignore_flag: Final[bool] = ruledata['ignore']

            def ignore_action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                package.set_flag(PackageFlags.IGNORE, ignore_flag)

            self._actions.append(ignore_action)

        if 'weak_devel' in ruledata:
            weak_devel_flag: Final = ruledata['weak_devel']

            def weak_devel_action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                # XXX: currently sets ignore; change to set non-viral variant of devel (#654)
                package.set_flag(PackageFlags.IGNORE, weak_devel_flag)

            self._actions.append(weak_devel_action)

        if 'stable' in ruledata:
            stable_flag: Final = ruledata['stable']

            def stable_action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                package.set_flag(PackageFlags.STABLE, stable_flag)

            self._actions.append(stable_action)

        if 'devel' in ruledata:
            devel_flag: Final = ruledata['devel']

            def devel_action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                package.set_flag(PackageFlags.DEVEL, devel_flag)

            self._actions.append(devel_action)

        if 'p_is_patch' in ruledata:
            p_is_patch_flag: Final = ruledata['p_is_patch']

            def p_is_patch_action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                package.set_flag(PackageFlags.P_IS_PATCH, p_is_patch_flag)

            self._actions.append(p_is_patch_action)

        if 'any_is_patch' in ruledata:
            any_is_patch_flag: Final = ruledata['any_is_patch']

            def any_is_patch_action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                package.set_flag(PackageFlags.ANY_IS_PATCH, any_is_patch_flag)

            self._actions.append(any_is_patch_action)

        if 'outdated' in ruledata:
            outdated_flag: Final = ruledata['outdated']

            def outdated_action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                package.set_flag(PackageFlags.OUTDATED, outdated_flag)

            self._actions.append(outdated_action)

        if 'legacy' in ruledata:
            legacy_flag: Final = ruledata['legacy']

            def legacy_action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                package.set_flag(PackageFlags.LEGACY, legacy_flag)

            self._actions.append(legacy_action)

        if 'incorrect' in ruledata:
            incorrect_flag: Final = ruledata['incorrect']

            def incorrect_action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                package.set_flag(PackageFlags.INCORRECT, incorrect_flag)

            self._actions.append(incorrect_action)

        if 'untrusted' in ruledata:
            untrusted_flag: Final = ruledata['untrusted']

            def untrusted_action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                package.set_flag(PackageFlags.UNTRUSTED, untrusted_flag)

            self._actions.append(untrusted_action)

        if 'noscheme' in ruledata:
            noscheme_flag: Final = ruledata['noscheme']

            def noscheme_action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                package.set_flag(PackageFlags.NOSCHEME, noscheme_flag)

            self._actions.append(noscheme_action)

        if 'rolling' in ruledata:
            rolling_flag: Final = ruledata['rolling']

            def rolling_action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                package.set_flag(PackageFlags.ROLLING, rolling_flag)

            self._actions.append(rolling_action)

        if 'snapshot' in ruledata:
            snapshot_flag: Final = ruledata['snapshot']

            def snapshot_action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                # XXX: the same as ignored for now
                package.set_flag(PackageFlags.IGNORE, snapshot_flag)

            self._actions.append(snapshot_action)

        if 'successor' in ruledata:
            successor_flag: Final = ruledata['successor']

            def successor_action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                # XXX: the same as devel for now
                package.set_flag(PackageFlags.DEVEL, successor_flag)

            self._actions.append(successor_action)

        if 'debianism' in ruledata:
            debianism_flag: Final = ruledata['debianism']

            def debianism_action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                # XXX: the same as devel for now
                package.set_flag(PackageFlags.DEVEL, debianism_flag)

            self._actions.append(debianism_action)

        if 'generated' in ruledata:
            generated_flag: Final = ruledata['generated']

            def generated_action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                # XXX: the same as rolling for now
                package.set_flag(PackageFlags.ROLLING, generated_flag)

            self._actions.append(generated_action)

        if 'trace' in ruledata:
            trace_flag: Final = ruledata['trace']

            def trace_action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                package.set_flag(PackageFlags.TRACE, trace_flag)

            self._actions.append(trace_action)

        if 'altver' in ruledata:
            altver_flag: Final = ruledata['altver']

            def altver_action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                package.set_flag(PackageFlags.ALTVER, altver_flag)

            self._actions.append(altver_action)

        if 'last' in ruledata:
            def last_action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                match_context.last = True

            self._actions.append(last_action)

        if 'addflavor' in ruledata:
            tmp_flavors: Optional[List[str]]

            if isinstance(ruledata['addflavor'], str):
                tmp_flavors = [ruledata['addflavor']]
            elif isinstance(ruledata['addflavor'], list):
                tmp_flavors = ruledata['addflavor']
            elif not isinstance(ruledata['addflavor'], bool):
                raise RuntimeError('addflavor must be boolean or str or list')
            else:
                tmp_flavors = None

            want_flavors: Final[Optional[List[str]]] = tmp_flavors

            def addflavor_action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                flavors: List[str] = want_flavors if want_flavors else [package.effname]

                flavors = [match_context.sub_name_dollars(flavor, package.effname) for flavor in flavors]

                flavors = [flavor.strip('-') for flavor in flavors]

                package.flavors += [flavor for flavor in flavors if flavor]

            self._actions.append(addflavor_action)

        if 'resetflavors' in ruledata:
            def resetflavors_action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                package.flavors = []

            self._actions.append(resetflavors_action)

        if 'setbranch' in ruledata:
            setbranch: Final = ruledata['setbranch']

            def setbranch_action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                package.branch = match_context.sub_ver_dollars(setbranch, package.version)

            self._actions.append(setbranch_action)

        if 'setbranchcomps' in ruledata:
            setbranchcomps: Final = ruledata['setbranchcomps']

            def setbranchcomps_action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                package.branch = '.'.join(re.split('[^a-zA-Z0-9]', package.version)[0:setbranchcomps])

            self._actions.append(setbranchcomps_action)

        if 'addflag' in ruledata:
            addflags: Final = as_list(ruledata['addflag'])

            def addflag_action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                for flag in addflags:
                    package_context.add_flag(flag)

            self._actions.append(addflag_action)

        if 'setname' in ruledata:
            setname: Final = ruledata['setname']

            def setname_action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                package.effname = match_context.sub_name_dollars(setname, package.effname)

            self._actions.append(setname_action)

        if 'setver' in ruledata:
            setver: Final = ruledata['setver']

            def setver_action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                package.version = match_context.sub_ver_dollars(setver, package.version)

            self._actions.append(setver_action)

        if 'replaceinname' in ruledata:
            replace_items: Final = list(ruledata['replaceinname'].items())

            def replaceinname_action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                for pattern, replacement in replace_items:
                    package.effname = package.effname.replace(pattern, replacement)

            self._actions.append(replaceinname_action)

        if 'tolowername' in ruledata:
            def tolowername_action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                package.effname = package.effname.lower()

            self._actions.append(tolowername_action)

        if 'warning' in ruledata:
            def warning_action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                package_context.add_warning(ruledata['warning'])

            self._actions.append(warning_action)

    def match(self, package: Package, package_context: PackageContext) -> Optional[MatchContext]:
        match_context = MatchContext()

        self.checks += 1

        for matcher in self._matchers:
            if not matcher(package, package_context, match_context):
                return None

        self.matches += 1
        package_context.add_matched_rule(self.number)

        return match_context

    def apply(self, package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
        for action in self._actions:
            action(package, package_context, match_context)
