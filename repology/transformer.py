# Copyright (C) 2016-2017 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import os
import pprint
import re
import sys

import yaml


class RuleApplyResult:
    unmatched = 1
    matched = 2
    last = 3


class PackageTransformer:
    def __init__(self, rulesdir=None, rulestext=None):
        self.dollar0 = re.compile('\$0', re.ASCII)
        self.dollarN = re.compile('\$([0-9]+)', re.ASCII)

        self.rules = []

        if rulestext:
            self.rules = yaml.safe_load(rulestext)
        else:
            for filename in sorted(os.listdir(rulesdir)):
                rulespath = os.path.join(rulesdir, filename)
                if not os.path.isfile(rulespath) or not rulespath.endswith('.yaml'):
                    continue

                with open(rulespath) as rulesfile:
                    self.rules += yaml.safe_load(rulesfile)

        pp = pprint.PrettyPrinter(width=10000)
        rulenum = 0
        for rule in self.rules:
            # save pretty-print before all transformations
            rule['pretty'] = pp.pformat(rule)

            # convert some fields to lists
            for field in ['name', 'ver', 'category', 'family', 'wwwpart']:
                if field in rule and not isinstance(rule[field], list):
                    rule[field] = [rule[field]]

            # compile regexps
            for field in ['namepat', 'verpat', 'wwwpat']:
                if field in rule:
                    rule[field] = re.compile(rule[field], re.ASCII)

            rule['matches'] = 0
            rule['number'] = rulenum
            rulenum += 1

        self.fastrules = {}
        self.slowrules = []

        for rule in self.rules:
            if 'name' in rule:
                for name in rule['name']:
                    self.fastrules.setdefault(name, []).append(rule)
            else:
                self.slowrules.append(rule)

    def ApplyRule(self, rule, package):
        # match family
        if 'family' in rule:
            if package.family not in rule['family']:
                return RuleApplyResult.unmatched

        # match categories
        if 'category' in rule:
            if package.category not in rule['category']:
                return RuleApplyResult.unmatched

        # match name
        if 'name' in rule:
            if package.effname not in rule['name']:
                return RuleApplyResult.unmatched

        # match name patterns
        if 'namepat' in rule:
            if not rule['namepat'].fullmatch(package.effname):
                return RuleApplyResult.unmatched

        # match version
        if 'ver' in rule:
            if package.version not in rule['ver']:
                return RuleApplyResult.unmatched

        # match version patterns
        if 'verpat' in rule:
            if not rule['verpat'].fullmatch(package.version):
                return RuleApplyResult.unmatched

        # match number of version components
        if 'verlonger' in rule:
            if not len(package.version.split('.')) > rule['verlonger']:
                return RuleApplyResult.unmatched

        # match name patterns
        if 'wwwpat' in rule:
            if not package.homepage or not rule['wwwpat'].fullmatch(package.homepage):
                return RuleApplyResult.unmatched

        if 'wwwpart' in rule:
            if not package.homepage:
                return RuleApplyResult.unmatched
            matched = False
            for wwwpart in rule['wwwpart']:
                if wwwpart in package.homepage.lower():
                    matched = True
                    break
            if not matched:
                return RuleApplyResult.unmatched

        # rule matches, apply effects!
        result = RuleApplyResult.matched

        rule['matches'] += 1

        if 'ignore' in rule:
            package.ignore = True

        if 'unignore' in rule:
            package.ignore = False

        if 'ignorever' in rule:
            package.ignoreversion = True

        if 'unignorever' in rule:
            package.ignoreversion = False

        if 'last' in rule:
            result = RuleApplyResult.last

        if 'setname' in rule:
            match = None
            if 'namepat' in rule:
                match = rule['namepat'].fullmatch(package.effname)
            if match:
                package.effname = self.dollarN.sub(lambda x: match.group(int(x.group(1))), rule['setname'])
            else:
                package.effname = self.dollar0.sub(package.effname, rule['setname'])

        if 'replaceinname' in rule:
            for pattern, replacement in rule['replaceinname'].items():
                package.effname = package.effname.replace(pattern, replacement)

        if 'tolowername' in rule:
            package.effname = package.effname.lower()

        if 'warning' in rule:
            print('Rule warning for {} in {}: {}'.format(package.name, package.repo, rule['warning']), file=sys.stderr)

        return result

    def GetFastRule(self, package, lownumber=-1):
        for fastrule in self.fastrules.get(package.effname, []):
            if fastrule['number'] > lownumber:
                return fastrule

        return None

    def Process(self, package):
        # start with package.name as is, if it was not already set
        if package.effname is None:
            package.effname = package.name

        # keep the next fast rule that will match
        # it will be racalculated as soon as it's reached or
        # as soon as any slow rule matches (as it may change effname)
        nextfastrule = self.GetFastRule(package)

        # walk the slow rules sequentionally
        for slowrule in self.slowrules:
            result = None

            # apply fast rules
            while nextfastrule and nextfastrule['number'] < slowrule['number']:
                if self.ApplyRule(nextfastrule, package) == RuleApplyResult.last:
                    return
                nextfastrule = self.GetFastRule(package, nextfastrule['number'])

            # apply slow rule
            result = self.ApplyRule(slowrule, package)
            if result == RuleApplyResult.matched:
                nextfastrule = self.GetFastRule(package, slowrule['number'])
            elif result == RuleApplyResult.last:
                return

        # apply remaining fast rules
        while nextfastrule:
            if self.ApplyRule(nextfastrule, package) == RuleApplyResult.last:
                return
            nextfastrule = self.GetFastRule(package, nextfastrule['number'])

    def GetUnmatchedRules(self):
        result = []

        for rule in self.rules:
            if rule['matches'] == 0:
                result.append(rule['pretty'])

        return result
