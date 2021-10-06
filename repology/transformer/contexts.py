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

from typing import Iterable, Match

from repology.transformer.util import DOLLAR0, DOLLARN


class PackageContext:
    __slots__ = ['_flags', '_rulesets', 'warnings', 'matched_rules']

    _flags: set[str]
    _rulesets: set[str]
    warnings: list[str]
    matched_rules: list[int]

    def __init__(self) -> None:
        self._flags = set()
        self._rulesets = set()
        self.warnings = []
        self.matched_rules = []

    def add_flag(self, name: str) -> None:
        self._flags.add(name)

    def has_flag(self, name: str) -> bool:
        return name in self._flags

    def has_flags(self, names: set[str]) -> bool:
        return not self._flags.isdisjoint(names)

    def has_rulesets(self, rulesets: set[str]) -> bool:
        return not self._rulesets.isdisjoint(rulesets)

    def set_rulesets(self, rulesets: Iterable[str]) -> None:
        self._rulesets = set(rulesets)

    def add_warning(self, warning: str) -> None:
        self.warnings.append(warning)

    def add_matched_rule(self, ruleid: int) -> None:
        self.matched_rules.append(ruleid)


class MatchContext:
    __slots__ = ['name_match', 'ver_match', 'last']

    name_match: Match[str] | None
    ver_match: Match[str] | None
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
