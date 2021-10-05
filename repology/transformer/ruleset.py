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

import hashlib
import os
from copy import deepcopy
from typing import Any, Optional

import yaml

from repology.transformer.rule import Rule


SPLIT_MULTI_NAME_RULES = True


class Ruleset:
    _rules: list[Rule]
    _hash: str

    def __init__(self, rulesdir: Optional[str] = None, rulestext: Optional[str] = None) -> None:
        self._rules = []

        hasher = hashlib.sha256()

        if isinstance(rulestext, str):
            hasher.update(rulestext.encode('utf-8'))
            for ruledata in yaml.safe_load(rulestext):
                self._add_rule(ruledata)
        elif isinstance(rulesdir, str):
            rulefiles: list[str] = []

            for root, dirs, files in os.walk(rulesdir):
                rulefiles += [os.path.join(root, f) for f in files if f.endswith('.yaml')]
                dirs[:] = [d for d in dirs if not d.startswith('.')]

            for rulefile in sorted(rulefiles):
                with open(rulefile) as data:
                    ruleset_text = data.read()
                    hasher.update(ruleset_text.encode('utf-8'))

                    rules = yaml.safe_load(ruleset_text)
                    if rules:  # may be None for empty file
                        for rule in rules:
                            self._add_rule(rule)
        else:
            raise RuntimeError('rulesdir or rulestext must be defined')

        self._hash = hasher.hexdigest()

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
