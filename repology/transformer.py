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

from repology.package import PackageFlags
from repology.version import VersionCompare


class RuleApplyResult:
    unmatched = 1
    matched = 2
    last = 3


class PackageTransformationContext:
    __slots__ = ['flags']

    def __init__(self):
        self.flags = set()

    def SetFlag(self, name, value=True):
        if value:
            self.flags.add(name)
        else:
            self.flags.discard(name)

    def HasFlag(self, name):
        return name in self.flags

    def HasFlags(self, names):
        return not self.flags.isdisjoint(names)


class PackageTransformer:
    def __init__(self, repoman, rulesdir=None, rulestext=None):
        self.repoman = repoman

        self.dollar0 = re.compile('\$0', re.ASCII)
        self.dollarN = re.compile('\$([0-9]+)', re.ASCII)

        self.rules = []

        if rulestext:
            self.rules = yaml.safe_load(rulestext)
        else:
            rulefiles = []

            for root, dirs, files in os.walk(rulesdir):
                rulefiles += [os.path.join(root, f) for f in files if f.endswith('.yaml')]
                dirs[:] = [d for d in dirs if not d.startswith('.')]

            for rulefile in sorted(rulefiles):
                with open(rulefile) as data:
                    self.rules += yaml.safe_load(data)

        pp = pprint.PrettyPrinter(width=10000)
        for rulenum, rule in enumerate(self.rules):
            # save pretty-print before all transformations
            rule['pretty'] = pp.pformat(rule)

            # convert some fields to lists
            for field in ['name', 'ver', 'category', 'family', 'ruleset', 'noruleset', 'wwwpart', 'flag', 'noflag', 'addflag']:
                if field in rule and not isinstance(rule[field], list):
                    rule[field] = [rule[field]]

            # support legacy
            if 'family' in rule and 'ruleset' in rule:
                raise RuntimeError('both ruleset and family in rule!')
            elif 'family' in rule and 'ruleset' not in rule:
                rule['ruleset'] = rule.pop('family')

            # convert some fields to sets
            for field in ['ruleset', 'noruleset', 'flag', 'noflag']:
                if field in rule:
                    rule[field] = set(rule[field])

            # convert some fields to lowercase
            for field in ['category', 'wwwpart']:
                if field in rule:
                    rule[field] = [s.lower() for s in rule[field]]

            # compile regexps
            for field in ['namepat', 'verpat', 'wwwpat']:
                if field in rule:
                    # replace here handles multiline regexps
                    rule[field] = re.compile(rule[field].replace('\n', ''), re.ASCII)

            rule['matches'] = 0
            rule['number'] = rulenum

        self.fastrules = {}
        self.slowrules = []

        for rule in self.rules:
            if 'name' in rule:
                for name in rule['name']:
                    self.fastrules.setdefault(name, []).append(rule)
            else:
                self.slowrules.append(rule)

    def ApplyRule(self, rule, package, context):
        # pattern matches are reused when rule applies
        name_match = None
        ver_match = None

        # match family
        if 'ruleset' in rule:
            if self.repoman.GetRepository(package.repo)['ruleset'].isdisjoint(rule['ruleset']):
                return RuleApplyResult.unmatched

        if 'noruleset' in rule:
            if not self.repoman.GetRepository(package.repo)['ruleset'].isdisjoint(rule['noruleset']):
                return RuleApplyResult.unmatched

        # match categories
        if 'category' in rule:
            if not package.category:
                return RuleApplyResult.unmatched
            if package.category.lower() not in rule['category']:
                return RuleApplyResult.unmatched

        # match name
        if 'name' in rule:
            if package.effname not in rule['name']:
                return RuleApplyResult.unmatched

        # match name patterns
        if 'namepat' in rule:
            name_match = rule['namepat'].fullmatch(package.effname)
            if not name_match:
                return RuleApplyResult.unmatched

        # match version
        if 'ver' in rule:
            if package.version not in rule['ver']:
                return RuleApplyResult.unmatched

        # match version patterns
        if 'verpat' in rule:
            ver_match = rule['verpat'].fullmatch(package.version.lower())
            if not ver_match:
                return RuleApplyResult.unmatched

        # match number of version components
        if 'verlonger' in rule:
            if not len(re.split('[^a-zA-Z0-9]', package.version)) > rule['verlonger']:
                return RuleApplyResult.unmatched

        # compare versions
        if 'vergt' in rule:
            if VersionCompare(package.version, rule['vergt']) <= 0:
                return RuleApplyResult.unmatched

        if 'verge' in rule:
            if VersionCompare(package.version, rule['verge']) < 0:
                return RuleApplyResult.unmatched

        if 'verlt' in rule:
            if VersionCompare(package.version, rule['verlt']) >= 0:
                return RuleApplyResult.unmatched

        if 'verle' in rule:
            if VersionCompare(package.version, rule['verle']) > 0:
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

        if 'flag' in rule:
            if not context.HasFlags(rule['flag']):
                return RuleApplyResult.unmatched

        if 'noflag' in rule:
            if context.HasFlags(rule['noflag']):
                return RuleApplyResult.unmatched

        # rule matches, apply effects!
        result = RuleApplyResult.matched

        rule['matches'] += 1

        if 'remove' in rule:
            package.SetFlag(PackageFlags.remove, rule['remove'])

        if 'ignore' in rule:
            package.SetFlag(PackageFlags.ignore, rule['ignore'])

        if 'devel' in rule:
            package.SetFlag(PackageFlags.devel, rule['devel'])

        if 'p_is_patch' in rule:
            package.SetFlag(PackageFlags.p_is_patch, rule['p_is_patch'])

        if 'any_is_patch' in rule:
            package.SetFlag(PackageFlags.any_is_patch, rule['any_is_patch'])

        if 'outdated' in rule:
            package.SetFlag(PackageFlags.outdated, rule['outdated'])

        if 'legacy' in rule:
            package.SetFlag(PackageFlags.legacy, rule['legacy'])

        if 'incorrect' in rule:
            package.SetFlag(PackageFlags.incorrect, rule['incorrect'])

        if 'untrusted' in rule:
            package.SetFlag(PackageFlags.untrusted, rule['untrusted'])

        if 'noscheme' in rule:
            package.SetFlag(PackageFlags.noscheme, rule['noscheme'])

        if 'snapshot' in rule:
            # XXX: the same as ignored for now
            package.SetFlag(PackageFlags.ignore, rule['snapshot'])

        if 'successor' in rule:
            # XXX: the same as devel for now
            package.SetFlag(PackageFlags.devel, rule['successor'])

        if 'rolling' in rule:
            package.SetFlag(PackageFlags.rolling, rule['rolling'])

        if 'last' in rule:
            result = RuleApplyResult.last

        if 'addflavor' in rule:
            flavors = []
            if isinstance(rule['addflavor'], bool):
                flavors = [package.effname]
            elif isinstance(rule['addflavor'], str):
                flavors = [rule['addflavor']]
            elif isinstance(rule['addflavor'], list):
                flavors = rule['addflavor']
            else:
                raise RuntimeError('addflavor must be boolean or str or list')

            if name_match:
                flavors = [self.dollarN.sub(lambda x: name_match.group(int(x.group(1))), flavor) for flavor in flavors]
            else:
                flavors = [self.dollar0.sub(package.effname, flavor) for flavor in flavors]

            flavors = [flavor.strip('-') for flavor in flavors]

            package.flavors += [flavor for flavor in flavors if flavor]

        if 'resetflavors' in rule:
            package.flavors = []

        if 'addflag' in rule:
            for flag in rule['addflag']:
                context.SetFlag(flag)

        if 'setname' in rule:
            if name_match:
                package.effname = self.dollarN.sub(lambda x: name_match.group(int(x.group(1))), rule['setname'])
            else:
                package.effname = self.dollar0.sub(package.effname, rule['setname'])

        if 'setver' in rule:
            version_before_fix = package.version

            if package.origversion is None:
                package.origversion = package.version

            if ver_match:
                package.version = self.dollarN.sub(lambda x: ver_match.group(int(x.group(1))), rule['setver'])
            else:
                package.version = self.dollar0.sub(package.version, rule['setver'])

            package.verfixed = package.version != version_before_fix

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
        context = PackageTransformationContext()
        for slowrule in self.slowrules:
            result = None

            # apply fast rules
            while nextfastrule and nextfastrule['number'] < slowrule['number']:
                if self.ApplyRule(nextfastrule, package, context) == RuleApplyResult.last:
                    return
                nextfastrule = self.GetFastRule(package, nextfastrule['number'])

            # apply slow rule
            result = self.ApplyRule(slowrule, package, context)
            if result == RuleApplyResult.matched:
                nextfastrule = self.GetFastRule(package, slowrule['number'])
            elif result == RuleApplyResult.last:
                return

        # apply remaining fast rules
        while nextfastrule:
            if self.ApplyRule(nextfastrule, package, context) == RuleApplyResult.last:
                return
            nextfastrule = self.GetFastRule(package, nextfastrule['number'])

    def GetUnmatchedRules(self):
        result = []

        for rule in self.rules:
            if rule['matches'] == 0:
                result.append(rule['pretty'])

        return result
