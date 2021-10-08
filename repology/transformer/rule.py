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

from typing import Any, Callable

from repology.package import Package
from repology.transformer.actions import get_action_generators
from repology.transformer.contexts import MatchContext, PackageContext
from repology.transformer.matchers import get_matcher_generators
from repology.transformer.util import DOLLAR0, yaml_as_list, yaml_as_set


class Rule:
    __slots__ = ['_matchers', '_actions', 'names', 'namepat', 'rulesets', 'norulesets', 'checks', 'matches', 'number', 'pretty']

    _matchers: list[Callable[[Package, PackageContext, MatchContext], bool]]
    _actions: list[Callable[[Package, PackageContext, MatchContext], None]]
    names: list[str] | None
    namepat: str | None
    rulesets: set[str] | None
    norulesets: set[str] | None
    checks: int
    matches: int
    number: int
    pretty: str

    def __init__(self, number: int, ruledata: dict[str, Any]) -> None:
        self.names = None
        self.namepat = None
        self.rulesets = None
        self.norulesets = None
        self.number = number
        self.checks = 0
        self.matches = 0

        self.pretty = str(ruledata)

        self._matchers = []
        self._actions = []

        # handle substitution of final name in name matchers
        if 'name' in ruledata:
            self.names = yaml_as_list(ruledata['name'])

            if 'setname' in ruledata:
                self.names = [DOLLAR0.sub(ruledata['setname'], name) for name in self.names]

            ruledata['name'] = self.names

        if 'namepat' in ruledata:
            self.namepat = ruledata['namepat'].replace('\n', '')

            if 'setname' in ruledata:
                self.namepat = DOLLAR0.sub(ruledata['setname'], self.namepat)

            ruledata['namepat'] = self.namepat

        if 'ruleset' in ruledata:
            self.rulesets = yaml_as_set(ruledata['ruleset'])

        if 'noruleset' in ruledata:
            self.norulesets = yaml_as_set(ruledata['noruleset'])

        # matchers
        for keyword, generate_matcher in get_matcher_generators():
            if keyword in ruledata:
                self._matchers.append(generate_matcher(ruledata))

        # actions
        for keyword, generate_action in get_action_generators():
            if keyword in ruledata:
                self._actions.append(generate_action(ruledata))

    def match(self, package: Package, package_context: PackageContext) -> MatchContext | None:
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
