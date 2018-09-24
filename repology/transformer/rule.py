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
import sys

from libversion import version_compare

from repology.package import PackageFlags


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
