# Copyright (C) 2016-2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
from collections import defaultdict

from libversion import version_compare

import yaml

from repology.package import PackageFlags


class RuleApplyResult:
    default = 1
    last = 3


class PackageContext:
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


class MatchContext:
    __slots__ = ['name_match', 'ver_match']

    def __init__(self):
        self.name_match = None
        self.ver_match = None


class RuleBlock:
    TYPE_SIMPLE = 1
    TYPE_NAME_MAP = 2

    def __init__(self):
        self.type = None
        self.simple_rules = []
        self.name_map = defaultdict(list)

    def add_rule(self, rule):
        rule_type = RuleBlock.TYPE_SIMPLE
        if 'name' in rule:
            rule_type = RuleBlock.TYPE_NAME_MAP

        if self.type is None:
            self.type = rule_type
        elif self.type != rule_type:
            return False

        if rule_type == RuleBlock.TYPE_SIMPLE:
            self.simple_rules.append(rule)
        elif rule_type == RuleBlock.TYPE_NAME_MAP:
            for name in rule['name']:
                self.name_map[name].append(rule)

        return True

    def iter_rules(self, package):
        if self.type == RuleBlock.TYPE_SIMPLE:
            yield from self.simple_rules
        elif self.type == RuleBlock.TYPE_NAME_MAP:
            min_rule_num = 0
            while True:
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


class PackageTransformer:
    def __init__(self, repomgr, rulesdir=None, rulestext=None):
        self.repomgr = repomgr

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

            # compile regexps (replace here handles multiline regexps)
            for field in ['namepat', 'wwwpat']:
                if field in rule:
                    rule[field] = re.compile(rule[field].replace('\n', ''), re.ASCII)

            for field in ['verpat']:
                if field in rule:  # verpat is case insensitive
                    rule[field] = re.compile(rule[field].lower().replace('\n', ''), re.ASCII)

            rule['matches'] = 0
            rule['number'] = rulenum

        self.ruleblocks = [RuleBlock()]

        for rule in self.rules:
            if not self.ruleblocks[-1].add_rule(rule):
                self.ruleblocks.append(RuleBlock())
                self.ruleblocks[-1].add_rule(rule)

    def _match_rule(self, rule, package, package_context):
        match_context = MatchContext()

        # match family
        if 'ruleset' in rule:
            if self.repomgr.GetRepository(package.repo)['ruleset'].isdisjoint(rule['ruleset']):
                return None

        if 'noruleset' in rule:
            if not self.repomgr.GetRepository(package.repo)['ruleset'].isdisjoint(rule['noruleset']):
                return None

        # match categories
        if 'category' in rule:
            if not package.category:
                return None
            if package.category.lower() not in rule['category']:
                return None

        # match name
        if 'name' in rule:
            if package.effname not in rule['name']:
                return None

        # match name patterns
        if 'namepat' in rule:
            match_context.name_match = rule['namepat'].fullmatch(package.effname)
            if not match_context.name_match:
                return None

        # match version
        if 'ver' in rule:
            if package.version not in rule['ver']:
                return None

        # match version patterns
        if 'verpat' in rule:
            match_context.ver_match = rule['verpat'].fullmatch(package.version.lower())
            if not match_context.ver_match:
                return None

        # match number of version components
        if 'verlonger' in rule:
            if not len(re.split('[^a-zA-Z0-9]', package.version)) > rule['verlonger']:
                return None

        # compare versions
        if 'vergt' in rule:
            if version_compare(package.version, rule['vergt']) <= 0:
                return None

        if 'verge' in rule:
            if version_compare(package.version, rule['verge']) < 0:
                return None

        if 'verlt' in rule:
            if version_compare(package.version, rule['verlt']) >= 0:
                return None

        if 'verle' in rule:
            if version_compare(package.version, rule['verle']) > 0:
                return None

        if 'vereq' in rule:
            if version_compare(package.version, rule['vereq']) != 0:
                return None

        if 'verne' in rule:
            if version_compare(package.version, rule['verne']) == 0:
                return None

        # match name patterns
        if 'wwwpat' in rule:
            if not package.homepage or not rule['wwwpat'].fullmatch(package.homepage):
                return None

        if 'wwwpart' in rule:
            if not package.homepage:
                return None
            matched = False
            for wwwpart in rule['wwwpart']:
                if wwwpart in package.homepage.lower():
                    matched = True
                    break
            if not matched:
                return None

        if 'flag' in rule:
            if not package_context.HasFlags(rule['flag']):
                return None

        if 'noflag' in rule:
            if package_context.HasFlags(rule['noflag']):
                return None

        rule['matches'] += 1

        return match_context

    def _apply_rule(self, rule, package, package_context, match_context):
        last = False

        if 'remove' in rule:
            package.SetFlag(PackageFlags.remove, rule['remove'])

        if 'ignore' in rule:
            package.SetFlag(PackageFlags.ignore, rule['ignore'])

        if 'weak_devel' in rule:
            # XXX: currently sets ignore; change to set non-viral variant of devel (#654)
            package.SetFlag(PackageFlags.ignore, rule['weak_devel'])

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

        if 'rolling' in rule:
            package.SetFlag(PackageFlags.rolling, rule['rolling'])

        if 'snapshot' in rule:
            # XXX: the same as ignored for now
            package.SetFlag(PackageFlags.ignore, rule['snapshot'])

        if 'successor' in rule:
            # XXX: the same as devel for now
            package.SetFlag(PackageFlags.devel, rule['successor'])

        if 'generated' in rule:
            # XXX: the same as rolling for now
            package.SetFlag(PackageFlags.rolling, rule['generated'])

        if 'last' in rule:
            last = True

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

            if match_context.name_match:
                flavors = [self.dollarN.sub(lambda x: match_context.name_match.group(int(x.group(1))), flavor) for flavor in flavors]
            else:
                flavors = [self.dollar0.sub(package.effname, flavor) for flavor in flavors]

            flavors = [flavor.strip('-') for flavor in flavors]

            package.flavors += [flavor for flavor in flavors if flavor]

        if 'resetflavors' in rule:
            package.flavors = []

        if 'addflag' in rule:
            for flag in rule['addflag']:
                package_context.SetFlag(flag)

        if 'setname' in rule:
            if match_context.name_match:
                package.effname = self.dollarN.sub(lambda x: match_context.name_match.group(int(x.group(1))), rule['setname'])
            else:
                package.effname = self.dollar0.sub(package.effname, rule['setname'])

        if 'setver' in rule:
            version_before_fix = package.version

            if package.origversion is None:
                package.origversion = package.version

            if match_context.ver_match:
                package.version = self.dollarN.sub(lambda x: match_context.ver_match.group(int(x.group(1))), rule['setver'])
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

        if last:
            return RuleApplyResult.last

        return RuleApplyResult.default

    def _iter_package_rules(self, package):
        for ruleblock in self.ruleblocks:
            yield from ruleblock.iter_rules(package)

    def Process(self, package):
        # start with package.name as is, if it was not already set
        if package.effname is None:
            package.effname = package.name

        package_context = PackageContext()

        for rule in self._iter_package_rules(package):
            match_context = self._match_rule(rule, package, package_context)
            if match_context:
                if self._apply_rule(rule, package, package_context, match_context) == RuleApplyResult.last:
                    return

    def GetUnmatchedRules(self):
        result = []

        for rule in self.rules:
            if rule['matches'] == 0:
                result.append(rule['pretty'])

        return result
