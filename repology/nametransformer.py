# Copyright (C) 2016 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
import pprint

import yaml


class MatchResult:
    none = 0,
    match = 1,
    ignore = 2


class NameTransformer:
    def __init__(self, rulespath):
        self.dollar0 = re.compile("\$0", re.ASCII)
        self.dollarN = re.compile("\$([0-9]+)", re.ASCII)

        with open(rulespath) as file:
            self.rules = yaml.safe_load(file)

        pp = pprint.PrettyPrinter(width=10000)
        for rule in self.rules:
            # save pretty-print before all transformations
            rule['pretty'] = pp.pformat(rule)

            # convert some fields to lists
            for field in ['category']:
                if field in rule and not isinstance(rule[field], list):
                    rule[field] = [rule[field]]

            # compile regexps
            for field in ['namepat', 'verpat']:
                if field in rule:
                    rule[field] = re.compile(rule[field] + "$", re.ASCII)

            rule['matches'] = 0

    def IsRuleMatching(self, rule, package):
        # match categories
        if 'category' in rule:
            catmatch = False
            for category in rule['category']:
                if category == package.category:
                    catmatch = True
                    break

            if not catmatch:
                return False

        # match name
        if 'name' in rule:
            if package.name != rule['name']:
                return False

        # match name patterns
        if 'namepat' in rule:
            if not rule['namepat'].match(package.name):
                return False

        # match version
        if 'ver' in rule:
            if package.version != rule['ver']:
                return False

        # match version patterns
        if 'verpat' in rule:
            if not rule['verpat'].match(package.version):
                return False

        # match number of version components
        if 'verlonger' in rule:
            if not len(package.version.split('.')) > rule['verlonger']:
                return False

        return True

    def ApplyRule(self, rule, package):
        if not self.IsRuleMatching(rule, package):
            return MatchResult.none, None

        rule['matches'] += 1

        if 'ignore' in rule:
            return MatchResult.ignore, None

        # XXX: this should not really be intrusive to package, fix
        if 'ignorever' in rule:
            package.ignoreversion = True

        if 'setname' in rule:
            match = None
            if 'namepat' in rule:
                match = rule['namepat'].match(package.name)
            if match:
                return MatchResult.match, \
                       self.dollarN.sub(lambda x: match.group(int(x.group(1))), rule['setname'])
            else:
                return MatchResult.match, \
                       self.dollar0.sub(package.name, rule['setname'])

        if 'pass' in rule:
            return MatchResult.match, package.name

        return MatchResult.none, None

    def TransformName(self, package, family):
        # apply first matching rule
        for rule in self.rules:
            if 'families' in rule and family not in rule['families']:
                continue

            result, name = self.ApplyRule(rule, package)
            if result == MatchResult.ignore:
                return None
            elif result == MatchResult.match:
                return name.lower().replace('_', '-')

        # default processing
        return package.name.lower().replace('_', '-')

    def GetUnmatchedRules(self):
        result = []

        for rule in self.rules:
            if rule['matches'] == 0:
                result.append(rule['pretty'])

        return result
