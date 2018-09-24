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


RULE_LOWFREQ_THRESHOLD = 0.001  # best of 0.1, 0.01, 0.001, 0.0001
COVERING_BLOCK_MIN_SIZE = 2  # covering block over single block impose extra overhead
NAMEMAP_BLOCK_MIN_SIZE = 1  # XXX: test > 1 after rule optimizations

DOLLAR0 = re.compile('\$0', re.ASCII)
DOLLARN = re.compile('\$([0-9]+)', re.ASCII)


class RuleApplyResult:
    default = 1
    last = 3


class PackageContext:
    __slots__ = ['flags', 'rulesets']

    def __init__(self, rulesets):
        self.flags = set()
        self.rulesets = set(rulesets)

    def SetFlag(self, name, value=True):
        if value:
            self.flags.add(name)
        else:
            self.flags.discard(name)

    def HasFlag(self, name):
        return name in self.flags

    def HasFlags(self, names):
        return not self.flags.isdisjoint(names)

    def has_rulesets(self, rulesets):
        return not self.rulesets.isdisjoint(rulesets)


class MatchContext:
    __slots__ = ['name_match', 'ver_match']

    def __init__(self):
        self.name_match = None
        self.ver_match = None


class Rule(dict):
    def __init__(self, ruledata):
        self.update(ruledata)

    def match(self, package, package_context):
        match_context = MatchContext()

        # match family
        if 'ruleset' in self:
            if not package_context.has_rulesets(self['ruleset']):
                return None

        if 'noruleset' in self:
            if package_context.has_rulesets(self['noruleset']):
                return None

        # match categories
        if 'category' in self:
            if not package.category:
                return None
            if package.category.lower() not in self['category']:
                return None

        # match name
        if 'name' in self:
            if package.effname not in self['name']:
                return None

        # match name patterns
        if 'namepat' in self:
            match_context.name_match = self['namepat'].fullmatch(package.effname)
            if not match_context.name_match:
                return None

        # match version
        if 'ver' in self:
            if package.version not in self['ver']:
                return None

        # match version patterns
        if 'verpat' in self:
            match_context.ver_match = self['verpat'].fullmatch(package.version.lower())
            if not match_context.ver_match:
                return None

        # match number of version components
        if 'verlonger' in self:
            if not len(re.split('[^a-zA-Z0-9]', package.version)) > self['verlonger']:
                return None

        # compare versions
        if 'vergt' in self:
            if version_compare(package.version, self['vergt']) <= 0:
                return None

        if 'verge' in self:
            if version_compare(package.version, self['verge']) < 0:
                return None

        if 'verlt' in self:
            if version_compare(package.version, self['verlt']) >= 0:
                return None

        if 'verle' in self:
            if version_compare(package.version, self['verle']) > 0:
                return None

        if 'vereq' in self:
            if version_compare(package.version, self['vereq']) != 0:
                return None

        if 'verne' in self:
            if version_compare(package.version, self['verne']) == 0:
                return None

        # match name patterns
        if 'wwwpat' in self:
            if not package.homepage or not self['wwwpat'].fullmatch(package.homepage):
                return None

        if 'wwwpart' in self:
            if not package.homepage:
                return None
            matched = False
            for wwwpart in self['wwwpart']:
                if wwwpart in package.homepage.lower():
                    matched = True
                    break
            if not matched:
                return None

        if 'flag' in self:
            if not package_context.HasFlags(self['flag']):
                return None

        if 'noflag' in self:
            if package_context.HasFlags(self['noflag']):
                return None

        self['matches'] += 1

        return match_context

    def apply(self, package, package_context, match_context):
        last = False

        if 'remove' in self:
            package.SetFlag(PackageFlags.remove, self['remove'])

        if 'ignore' in self:
            package.SetFlag(PackageFlags.ignore, self['ignore'])

        if 'weak_devel' in self:
            # XXX: currently sets ignore; change to set non-viral variant of devel (#654)
            package.SetFlag(PackageFlags.ignore, self['weak_devel'])

        if 'devel' in self:
            package.SetFlag(PackageFlags.devel, self['devel'])

        if 'p_is_patch' in self:
            package.SetFlag(PackageFlags.p_is_patch, self['p_is_patch'])

        if 'any_is_patch' in self:
            package.SetFlag(PackageFlags.any_is_patch, self['any_is_patch'])

        if 'outdated' in self:
            package.SetFlag(PackageFlags.outdated, self['outdated'])

        if 'legacy' in self:
            package.SetFlag(PackageFlags.legacy, self['legacy'])

        if 'incorrect' in self:
            package.SetFlag(PackageFlags.incorrect, self['incorrect'])

        if 'untrusted' in self:
            package.SetFlag(PackageFlags.untrusted, self['untrusted'])

        if 'noscheme' in self:
            package.SetFlag(PackageFlags.noscheme, self['noscheme'])

        if 'rolling' in self:
            package.SetFlag(PackageFlags.rolling, self['rolling'])

        if 'snapshot' in self:
            # XXX: the same as ignored for now
            package.SetFlag(PackageFlags.ignore, self['snapshot'])

        if 'successor' in self:
            # XXX: the same as devel for now
            package.SetFlag(PackageFlags.devel, self['successor'])

        if 'generated' in self:
            # XXX: the same as rolling for now
            package.SetFlag(PackageFlags.rolling, self['generated'])

        if 'last' in self:
            last = True

        if 'addflavor' in self:
            flavors = []
            if isinstance(self['addflavor'], bool):
                flavors = [package.effname]
            elif isinstance(self['addflavor'], str):
                flavors = [self['addflavor']]
            elif isinstance(self['addflavor'], list):
                flavors = self['addflavor']
            else:
                raise RuntimeError('addflavor must be boolean or str or list')

            if match_context.name_match:
                flavors = [DOLLARN.sub(lambda x: match_context.name_match.group(int(x.group(1))), flavor) for flavor in flavors]
            else:
                flavors = [DOLLAR0.sub(package.effname, flavor) for flavor in flavors]

            flavors = [flavor.strip('-') for flavor in flavors]

            package.flavors += [flavor for flavor in flavors if flavor]

        if 'resetflavors' in self:
            package.flavors = []

        if 'addflag' in self:
            for flag in self['addflag']:
                package_context.SetFlag(flag)

        if 'setname' in self:
            if match_context.name_match:
                package.effname = DOLLARN.sub(lambda x: match_context.name_match.group(int(x.group(1))), self['setname'])
            else:
                package.effname = DOLLAR0.sub(package.effname, self['setname'])

        if 'setver' in self:
            version_before_fix = package.version

            if package.origversion is None:
                package.origversion = package.version

            if match_context.ver_match:
                package.version = DOLLARN.sub(lambda x: match_context.ver_match.group(int(x.group(1))), self['setver'])
            else:
                package.version = DOLLAR0.sub(package.version, self['setver'])

            package.verfixed = package.version != version_before_fix

        if 'replaceinname' in self:
            for pattern, replacement in self['replaceinname'].items():
                package.effname = package.effname.replace(pattern, replacement)

        if 'tolowername' in self:
            package.effname = package.effname.lower()

        if 'warning' in self:
            print('Rule warning for {} in {}: {}'.format(package.name, package.repo, self['warning']), file=sys.stderr)

        if last:
            return RuleApplyResult.last

        return RuleApplyResult.default


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


class PackageTransformer:
    def __init__(self, repomgr, rulesdir=None, rulestext=None):
        self.repomgr = repomgr

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

        self.rules = [Rule(ruledata) for ruledata in self.rules]

        self.ruleblocks = []

        current_name_rules = []

        def flush_current_name_rules():
            nonlocal current_name_rules
            if len(current_name_rules) >= NAMEMAP_BLOCK_MIN_SIZE:
                self.ruleblocks.append(NameMapRuleBlock(current_name_rules))
            elif current_name_rules:
                self.ruleblocks.extend([SingleRuleBlock(rule) for rule in current_name_rules])
            current_name_rules = []

        for rule in self.rules:
            if 'name' in rule:
                current_name_rules.append(rule)
            else:
                flush_current_name_rules()
                self.ruleblocks.append(SingleRuleBlock(rule))

        flush_current_name_rules()

        self.optruleblocks = self.ruleblocks
        self.packages_processed = 0

    def _recalc_opt_ruleblocks(self):
        self.optruleblocks = []

        current_lowfreq_blocks = []

        def flush_current_lowfreq_blocks():
            nonlocal current_lowfreq_blocks
            if len(current_lowfreq_blocks) >= COVERING_BLOCK_MIN_SIZE:
                self.optruleblocks.append(CoveringRuleBlock(current_lowfreq_blocks))
            elif current_lowfreq_blocks:
                self.optruleblocks.extend(current_lowfreq_blocks)
            current_lowfreq_blocks = []

        for block in self.ruleblocks:
            max_matches = 0
            has_unconditional = False
            for rule in block.iter_all_rules():
                max_matches = max(max_matches, rule['matches'])
                if 'name' not in rule and 'namepat' not in rule:
                    has_unconditional = True
                    break

            if has_unconditional or max_matches >= self.packages_processed * RULE_LOWFREQ_THRESHOLD:
                flush_current_lowfreq_blocks()
                self.optruleblocks.append(block)
                continue

            current_lowfreq_blocks.append(block)

        flush_current_lowfreq_blocks()

    def _iter_package_rules(self, package):
        for ruleblock in self.optruleblocks:
            yield from ruleblock.iter_rules(package)

    def Process(self, package):
        self.packages_processed += 1

        if self.packages_processed == 1000 or self.packages_processed == 10000 or self.packages_processed == 100000 or self.packages_processed == 1000000:
            self._recalc_opt_ruleblocks()

        # start with package.name as is, if it was not already set
        if package.effname is None:
            package.effname = package.name

        package_context = PackageContext(self.repomgr.GetRepository(package.repo)['ruleset'])

        for rule in self._iter_package_rules(package):
            match_context = rule.match(package, package_context)
            if match_context:
                if rule.apply(package, package_context, match_context) == RuleApplyResult.last:
                    return

    def GetUnmatchedRules(self):
        result = []

        for rule in self.rules:
            if rule['matches'] == 0:
                result.append(rule['pretty'])

        return result
