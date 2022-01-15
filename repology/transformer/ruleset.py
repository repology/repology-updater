# Copyright (C) 2016-2019,2021 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from copy import deepcopy
from typing import Any

from repology.transformer.rule import Rule
from repology.yamlloader import YamlConfig


SPLIT_MULTI_NAME_RULES = True


class Ruleset:
    _rules: list[Rule]
    _hash: str

    def __init__(self, rules_config: YamlConfig) -> None:
        self._rules = []

        for rule in rules_config.get_items():
            self._add_rule(rule)

        self._hash = rules_config.get_hash()

    def _add_rule(self, ruledata: dict[str, Any]) -> None:
        if SPLIT_MULTI_NAME_RULES and 'name' in ruledata and isinstance(ruledata['name'], list):
            for name in ruledata['name']:
                modified_ruledata = deepcopy(ruledata)
                modified_ruledata['name'] = name
                self._rules.append(Rule(len(self._rules), modified_ruledata))
        else:
            self._rules.append(Rule(len(self._rules), ruledata))

    def get_rules(self) -> list[Rule]:
        return self._rules

    def get_hash(self) -> str:
        return self._hash
