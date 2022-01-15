# Copyright (C) 2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Iterable, Pattern

from repology.package import Package
from repology.transformer.rule import Rule


class RuleBlock(ABC):
    @abstractmethod
    def iter_rules(self, package: Package) -> Iterable[Rule]:
        pass

    @abstractmethod
    def iter_all_rules(self) -> Iterable[Rule]:
        pass

    @abstractmethod
    def get_rule_range(self) -> tuple[int, int]:
        pass


class SingleRuleBlock(RuleBlock):
    _rule: Rule

    def __init__(self, rule: Rule) -> None:
        self._rule = rule

    def iter_rules(self, package: Package) -> Iterable[Rule]:
        return [self._rule]

    def iter_all_rules(self) -> Iterable[Rule]:
        return [self._rule]

    def get_rule_range(self) -> tuple[int, int]:
        return self._rule.number, self._rule.number


class NameMapRuleBlock(RuleBlock):
    _rules: list[Rule]
    _name_map: dict[str, list[Rule]]

    def __init__(self, rules: list[Rule]) -> None:
        self._rules = rules
        self._name_map = defaultdict(list)

        for rule in rules:
            if not rule.names:
                raise RuntimeError('unexpected rule kind for NameMapRuleBlock')

            for name in rule.names:
                self._name_map[name].append(rule)

    def iter_rules(self, package: Package) -> Iterable[Rule]:
        min_rule_num = 0
        while True:
            if package.effname not in self._name_map:
                return

            rules = self._name_map[package.effname]

            found = False
            for rule in rules:
                if rule.number >= min_rule_num:
                    yield rule
                    min_rule_num = rule.number + 1
                    found = True
                    break

            if not found:
                return

    def iter_all_rules(self) -> Iterable[Rule]:
        yield from self._rules

    def get_rule_range(self) -> tuple[int, int]:
        return self._rules[0].number, self._rules[-1].number


class CoveringRuleBlock(RuleBlock):
    _names: set[str]
    _megaregexp: Pattern[str]
    _sub_blocks: list[RuleBlock]

    def __init__(self, blocks: list[RuleBlock]) -> None:
        self._names = set()

        megaregexp_parts: list[str] = []
        for block in blocks:
            for rule in block.iter_all_rules():
                if rule.names:
                    for name in rule.names:
                        self._names.add(name)
                elif rule.namepat:
                    megaregexp_parts.append('(?:' + rule.namepat + ')')
                else:
                    raise RuntimeError('unexpected rule kind for CoveringRuleBlock')

        self._megaregexp = re.compile('|'.join(megaregexp_parts), re.ASCII)
        self._sub_blocks = blocks

    def iter_rules(self, package: Package) -> Iterable[Rule]:
        if package.effname in self._names or self._megaregexp.fullmatch(package.effname):
            for block in self._sub_blocks:
                yield from block.iter_rules(package)

    def iter_all_rules(self) -> Iterable[Rule]:
        for block in self._sub_blocks:
            yield from block.iter_all_rules()

    def get_rule_range(self) -> tuple[int, int]:
        return self._sub_blocks[0].get_rule_range()[0], self._sub_blocks[-1].get_rule_range()[-1]
