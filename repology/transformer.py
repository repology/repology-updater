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
    ignorepackage = 1
    ignoreversion = 2
    lastrule = 4


class PackageTransformer:
    def __init__(self, rulespath=None, rulestext=None):
        self.dollar0 = re.compile("\$0", re.ASCII)
        self.dollarN = re.compile("\$([0-9]+)", re.ASCII)

        self.rules = yaml.safe_load(rulestext if rulestext else open(rulespath))

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

    def MatchRule(self, rule, pkgname, pkgversion, pkgcategory, pkgfamily):
        # match families
        if 'families' in rule:
            if pkgfamily not in rule['families']:
                return False

        # match categories
        if 'category' in rule:
            catmatch = False
            for category in rule['category']:
                if category == pkgcategory:
                    catmatch = True
                    break

            if not catmatch:
                return False

        # match name
        if 'name' in rule:
            if pkgname != rule['name']:
                return False

        # match name patterns
        if 'namepat' in rule:
            if not rule['namepat'].match(pkgname):
                return False

        # match version
        if 'ver' in rule:
            if pkgversion != rule['ver']:
                return False

        # match version patterns
        if 'verpat' in rule:
            if not rule['verpat'].match(pkgversion):
                return False

        # match number of version components
        if 'verlonger' in rule:
            if not len(pkgversion.split('.')) > rule['verlonger']:
                return False

        return True

    def ApplyRule(self, rule, pkgname, pkgversion):
        flags = 0

        if 'ignore' in rule:
            flags |= MatchResult.ignorepackage

        if 'ignorever' in rule:
            flags |= MatchResult.ignoreversion

        if 'last' in rule:
            flags |= MatchResult.lastrule

        if 'setname' in rule:
            match = None
            if 'namepat' in rule:
                match = rule['namepat'].match(pkgname)
            if match:
                pkgname = self.dollarN.sub(lambda x: match.group(int(x.group(1))), rule['setname'])
            else:
                pkgname = self.dollar0.sub(pkgname, rule['setname'])

        if 'replaceinname' in rule:
            for pattern, replacement in rule['replaceinname'].items():
                pkgname = pkgname.replace(pattern, replacement)

        if 'tolowername' in rule:
            pkgname = pkgname.lower()

        return flags, pkgname

    def Process(self, package):
        transformed_name = package.name

        # apply first matching rule
        for rule in self.rules:
            if not self.MatchRule(rule, transformed_name, package.version, package.category, package.family):
                continue

            rule['matches'] += 1

            flags, transformed_name = self.ApplyRule(rule, transformed_name, package.version)

            if flags & MatchResult.ignorepackage:
                package.ignore = True

            if flags & MatchResult.ignoreversion:
                package.ignoreversion = True

            if flags & MatchResult.lastrule:
                break

        package.effname = transformed_name

    def GetUnmatchedRules(self):
        result = []

        for rule in self.rules:
            if rule['matches'] == 0:
                result.append(rule['pretty'])

        return result
