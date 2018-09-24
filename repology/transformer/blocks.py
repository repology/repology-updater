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
from collections import defaultdict


class SingleRuleBlock:
    def __init__(self, rule):
        self.rule = rule

    def iter_rules(self, package):
        return [self.rule]

    def iter_all_rules(self):
        return [self.rule]

    def get_rule_range(self):
        return self.rule['number'], self.rule['number']


class NameMapRuleBlock:
    def __init__(self, rules):
        self.rules = rules
        self.name_map = defaultdict(list)

        for rule in rules:
            if 'name' not in rule:
                raise RuntimeError('unexpected rule kind for NameMapRuleBlock')

            for name in rule['name']:
                self.name_map[name].append(rule)

    def iter_rules(self, package):
        min_rule_num = 0
        while True:
            if package.effname not in self.name_map:
                return

            rules = self.name_map[package.effname]

            found = False
            for rule in rules:
                if rule['number'] >= min_rule_num:
                    yield rule
                    min_rule_num = rule['number'] + 1
                    found = True
                    break

            if not found:
                return

    def iter_all_rules(self):
        yield from self.rules

    def get_rule_range(self):
        return self.rules[0]['number'], self.rules[-1]['number']


class CoveringRuleBlock:
    def __init__(self, blocks):
        self.names = set()

        megaregexp_parts = []
        for block in blocks:
            for rule in block.iter_all_rules():
                if 'name' in rule:
                    for name in rule['name']:
                        self.names.add(name)
                elif 'namepat' in rule:
                    megaregexp_parts.append('(?:' + rule['namepat'].pattern + ')')
                else:
                    raise RuntimeError('unexpected rule kind for CoveringRuleBlock')

        self.megaregexp = re.compile('|'.join(megaregexp_parts), re.ASCII)
        self.blocks = blocks

    def iter_rules(self, package):
        if package.effname in self.names or self.megaregexp.fullmatch(package.effname):
            for block in self.blocks:
                yield from block.iter_rules(package)

    def iter_all_rules(self):
        for block in self.blocks:
            yield from block.iter_all_rules()

    def get_rule_range(self):
        return self.blocks[0].get_rule_range()[0], self.blocks[-1].get_rule_range()[-1]
