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

import pprint
import re
import sys
from typing import AbstractSet, Any, Callable, Dict, Iterable, List, Match, MutableSet, Optional, Pattern, Set, TYPE_CHECKING

from libversion import version_compare

from repology.package import Package, PackageFlags

if TYPE_CHECKING:
    from typing_extensions import Final


DOLLAR0 = re.compile('\$0', re.ASCII)
DOLLARN = re.compile('\$([0-9])', re.ASCII)


class PackageContext:
    __slots__ = ['_flags', '_rulesets']

    _flags: MutableSet[str]
    _rulesets: MutableSet[str]

    def __init__(self) -> None:
        self._flags = set()
        self._rulesets = set()

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
    __slots__ = ['_matchers', '_actions', 'names', 'namepat', 'matches', 'number', 'pretty']

    _matchers: List[Callable[[Package, PackageContext, MatchContext], bool]]
    _actions: List[Callable[[Package, PackageContext, MatchContext], None]]
    names: Optional[List[str]]
    namepat: Optional[str]
    matches: int
    number: int
    pretty: str

    def __init__(self, number: int, ruledata: Dict[str, Any]) -> None:
        self.names = None
        self.namepat = None
        self.number = number
        self.matches = 0

        self.pretty = pprint.PrettyPrinter(width=10000).pformat(ruledata)

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

            def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                return package_context.has_rulesets(rulesets)

            self._matchers.append(matcher)

        if 'noruleset' in ruledata:
            norulesets: Final = as_set(ruledata['noruleset'])

            def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                return not package_context.has_rulesets(norulesets)

            self._matchers.append(matcher)

        if 'category' in ruledata:
            categories: Final = as_lowercase_set(ruledata['category'])

            def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                return bool(package.category and package.category.lower() in categories)

            self._matchers.append(matcher)

        if 'maintainer' in ruledata:
            maintainers: Final = as_lowercase_set(ruledata['maintainer'])

            def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                return not maintainers.isdisjoint(set((m.lower() for m in package.maintainers)))

            self._matchers.append(matcher)

        if 'name' in ruledata:
            names = as_list(ruledata['name'])

            if 'setname' in ruledata:
                names = [DOLLAR0.sub(ruledata['setname'], name) for name in names]

            self.names = names

            if len(names) == 1:
                name_to_check: Final[str] = names[0]

                def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                    return package.effname == name_to_check

                self._matchers.append(matcher)
            else:
                names_to_check: Final = set(names)

                def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                    return package.effname in names_to_check

                self._matchers.append(matcher)

        if 'namepat' in ruledata:
            namepat = ruledata['namepat'].replace('\n', '')

            if 'setname' in ruledata:
                namepat = DOLLAR0.sub(ruledata['setname'], namepat)

            self.namepat = namepat
            namepat_re: Final[Pattern[str]] = re.compile(namepat, re.ASCII)

            def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                match = namepat_re.fullmatch(package.effname)
                if match:
                    match_context.name_match = match
                    return True
                return False

            self._matchers.append(matcher)

        if 'ver' in ruledata:
            versions: Final = as_set(ruledata['ver'])

            if len(versions) == 1:
                version: Final[str] = versions.pop()

                def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                    return package.version == version

                self._matchers.append(matcher)
            else:
                def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                    return package.version in versions

                self._matchers.append(matcher)

        if 'verpat' in ruledata:
            verpat: Final = re.compile(ruledata['verpat'].replace('\n', '').lower(), re.ASCII)

            def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                match = verpat.fullmatch(package.version.lower())
                if match:
                    match_context.ver_match = match
                    return True
                return False

            self._matchers.append(matcher)

        if 'verlonger' in ruledata:
            verlonger: Final[int] = ruledata['verlonger']

            def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                return len(re.split('[^a-zA-Z0-9]', package.version)) > verlonger

            self._matchers.append(matcher)

        if 'vergt' in ruledata:
            vergt: Final[str] = ruledata['vergt']

            def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                return version_compare(package.version, vergt) > 0

            self._matchers.append(matcher)

        if 'verge' in ruledata:
            verge: Final[str] = ruledata['verge']

            def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                return version_compare(package.version, verge) >= 0

            self._matchers.append(matcher)

        if 'verlt' in ruledata:
            verlt: Final[str] = ruledata['verlt']

            def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                return version_compare(package.version, verlt) < 0

            self._matchers.append(matcher)

        if 'verle' in ruledata:
            verle: Final[str] = ruledata['verle']

            def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                return version_compare(package.version, verle) <= 0

            self._matchers.append(matcher)

        if 'vereq' in ruledata:
            vereq: Final[str] = ruledata['vereq']

            def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                return version_compare(package.version, vereq) == 0

            self._matchers.append(matcher)

        if 'verne' in ruledata:
            verne: Final[str] = ruledata['verne']

            def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                return version_compare(package.version, verne) != 0

            self._matchers.append(matcher)

        if 'wwwpat' in ruledata:
            wwwpat: Final[Pattern[str]] = re.compile(ruledata['wwwpat'].replace('\n', '').lower(), re.ASCII)

            def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                return bool(package.homepage and wwwpat.fullmatch(package.homepage))

            self._matchers.append(matcher)

        if 'wwwpart' in ruledata:
            wwwparts: Final = as_lowercase_list(ruledata['wwwpart'])

            def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                if not package.homepage:
                    return False
                for wwwpart in wwwparts:
                    if wwwpart in package.homepage.lower():
                        return True
                return False

            self._matchers.append(matcher)

        if 'summpart' in ruledata:
            summparts: Final = as_lowercase_list(ruledata['summpart'])

            def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                if not package.comment:
                    return False
                for summpart in summparts:
                    if summpart in package.comment.lower():
                        return True
                return False

            self._matchers.append(matcher)

        if 'flag' in ruledata:
            flags: Final = as_set(ruledata['flag'])

            def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                return package_context.has_flags(flags)

            self._matchers.append(matcher)

        if 'noflag' in ruledata:
            noflags: Final = as_set(ruledata['noflag'])

            def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                return not package_context.has_flags(noflags)

            self._matchers.append(matcher)

        if 'is_p_is_patch' in ruledata:
            is_p_is_patch: Final[bool] = ruledata['is_p_is_patch']

            def matcher(package: Package, package_context: PackageContext, match_context: MatchContext) -> bool:
                return package.HasFlag(PackageFlags.p_is_patch) == is_p_is_patch

            self._matchers.append(matcher)

        # actions
        if 'remove' in ruledata:
            remove_flag: Final[bool] = ruledata['remove']

            def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                package.SetFlag(PackageFlags.remove, remove_flag)

            self._actions.append(action)

        if 'ignore' in ruledata:
            ignore_flag: Final[bool] = ruledata['ignore']

            def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                package.SetFlag(PackageFlags.ignore, ignore_flag)

            self._actions.append(action)

        if 'weak_devel' in ruledata:
            weak_devel_flag: Final = ruledata['weak_devel']

            def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                # XXX: currently sets ignore; change to set non-viral variant of devel (#654)
                package.SetFlag(PackageFlags.ignore, weak_devel_flag)

            self._actions.append(action)

        if 'devel' in ruledata:
            devel_flag: Final = ruledata['devel']

            def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                package.SetFlag(PackageFlags.devel, devel_flag)

            self._actions.append(action)

        if 'p_is_patch' in ruledata:
            p_is_patch_flag: Final = ruledata['p_is_patch']

            def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                package.SetFlag(PackageFlags.p_is_patch, p_is_patch_flag)

            self._actions.append(action)

        if 'any_is_patch' in ruledata:
            any_is_patch_flag: Final = ruledata['any_is_patch']

            def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                package.SetFlag(PackageFlags.any_is_patch, any_is_patch_flag)

            self._actions.append(action)

        if 'outdated' in ruledata:
            outdated_flag: Final = ruledata['outdated']

            def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                package.SetFlag(PackageFlags.outdated, outdated_flag)

            self._actions.append(action)

        if 'legacy' in ruledata:
            legacy_flag: Final = ruledata['legacy']

            def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                package.SetFlag(PackageFlags.legacy, legacy_flag)

            self._actions.append(action)

        if 'incorrect' in ruledata:
            incorrect_flag: Final = ruledata['incorrect']

            def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                package.SetFlag(PackageFlags.incorrect, incorrect_flag)

            self._actions.append(action)

        if 'untrusted' in ruledata:
            untrusted_flag: Final = ruledata['untrusted']

            def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                package.SetFlag(PackageFlags.untrusted, untrusted_flag)

            self._actions.append(action)

        if 'noscheme' in ruledata:
            noscheme_flag: Final = ruledata['noscheme']

            def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                package.SetFlag(PackageFlags.noscheme, noscheme_flag)

            self._actions.append(action)

        if 'rolling' in ruledata:
            rolling_flag: Final = ruledata['rolling']

            def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                package.SetFlag(PackageFlags.rolling, rolling_flag)

            self._actions.append(action)

        if 'snapshot' in ruledata:
            snapshot_flag: Final = ruledata['snapshot']

            def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                # XXX: the same as ignored for now
                package.SetFlag(PackageFlags.ignore, snapshot_flag)

            self._actions.append(action)

        if 'successor' in ruledata:
            successor_flag: Final = ruledata['successor']

            def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                # XXX: the same as devel for now
                package.SetFlag(PackageFlags.devel, successor_flag)

            self._actions.append(action)

        if 'debianism' in ruledata:
            debianism_flag: Final = ruledata['debianism']

            def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                # XXX: the same as devel for now
                package.SetFlag(PackageFlags.devel, debianism_flag)

            self._actions.append(action)

        if 'generated' in ruledata:
            generated_flag: Final = ruledata['generated']

            def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                # XXX: the same as rolling for now
                package.SetFlag(PackageFlags.rolling, generated_flag)

            self._actions.append(action)

        if 'last' in ruledata:
            def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                match_context.last = True

            self._actions.append(action)

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

            def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                flavors: List[str] = want_flavors if want_flavors else [package.effname]

                flavors = [match_context.sub_name_dollars(flavor, package.effname) for flavor in flavors]

                flavors = [flavor.strip('-') for flavor in flavors]

                package.flavors += [flavor for flavor in flavors if flavor]

            self._actions.append(action)

        if 'resetflavors' in ruledata:
            def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                package.flavors = []

            self._actions.append(action)

        if 'addflag' in ruledata:
            addflags: Final = as_list(ruledata['addflag'])

            def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                for flag in addflags:
                    package_context.add_flag(flag)

            self._actions.append(action)

        if 'setname' in ruledata:
            setname: Final = ruledata['setname']

            def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                package.effname = match_context.sub_name_dollars(setname, package.effname)

            self._actions.append(action)

        if 'setver' in ruledata:
            setver: Final = ruledata['setver']

            def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                if package.origversion is None:
                    package.origversion = package.version

                package.version = match_context.sub_ver_dollars(setver, package.version)

            self._actions.append(action)

        if 'replaceinname' in ruledata:
            replace_items: Final = list(ruledata['replaceinname'].items())

            def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                for pattern, replacement in replace_items:
                    package.effname = package.effname.replace(pattern, replacement)

            self._actions.append(action)

        if 'tolowername' in ruledata:
            def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                package.effname = package.effname.lower()

            self._actions.append(action)

        if 'warning' in ruledata:
            def action(package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
                print('Rule warning for {} ({}) in {}: {}'.format(package.effname, package.name, package.repo, ruledata['warning']), file=sys.stderr)

            self._actions.append(action)

    def match(self, package: Package, package_context: PackageContext) -> Optional[MatchContext]:
        match_context = MatchContext()

        for matcher in self._matchers:
            if not matcher(package, package_context, match_context):
                return None

        self.matches += 1

        return match_context

    def apply(self, package: Package, package_context: PackageContext, match_context: MatchContext) -> None:
        for action in self._actions:
            action(package, package_context, match_context)
