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

import pprint
import re
import sys

from libversion import version_compare

from repology.package import PackageFlags


DOLLAR0 = re.compile('\$0', re.ASCII)
DOLLARN = re.compile('\$([0-9]+)', re.ASCII)


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
    __slots__ = ['name_match', 'ver_match', 'last']

    def __init__(self):
        self.name_match = None
        self.ver_match = None
        self.last = False


class Rule:
    __slots__ = ['data', 'matchers', 'actions', 'names', 'namepat', 'matches', 'number', 'pretty']

    def __init__(self, number, ruledata):
        self.data = ruledata

        self.matchers = []
        self.actions = []

        self.names = set(ruledata['name']) if 'name' in ruledata else None
        self.namepat = ruledata['namepat'].pattern if 'namepat' in ruledata else None
        self.matches = 0
        self.number = number
        self.pretty = pprint.PrettyPrinter(width=10000).pformat(ruledata)

        # matchers
        if 'ruleset' in self.data:
            rulesets = self.data['ruleset']

            def matcher(package, package_context, match_context):
                return package_context.has_rulesets(rulesets)

            self.matchers.append(matcher)

        if 'noruleset' in self.data:
            norulesets = self.data['noruleset']

            def matcher(package, package_context, match_context):
                return not package_context.has_rulesets(norulesets)

            self.matchers.append(matcher)

        if 'category' in self.data:
            categories = self.data['category']

            def matcher(package, package_context, match_context):
                return package.category and package.category.lower() in categories

            self.matchers.append(matcher)

        if 'name' in self.data:
            names = self.data['name']

            def matcher(package, package_context, match_context):
                return package.effname in names

            self.matchers.append(matcher)

        if 'namepat' in self.data:
            pattern = self.data['namepat']

            def matcher(package, package_context, match_context):
                match = namepat.fullmatch(package.effname)
                if match:
                    match_context.name_match = match
                    return True
                return False

            self.matchers.append(matcher)

        if 'ver' in self.data:
            versions = self.data['ver']

            def matcher(package, package_context, match_context):
                return package.version in versions

            self.matchers.append(matcher)

        if 'verpat' in self.data:
            pattern = self.data['verpat']

            def matcher(package, package_context, match_context):
                match = verpat.fullmatch(package.version.lower())
                if match:
                    match_context.ver_match = match
                    return True
                return False

            self.matchers.append(matcher)

        if 'verlonger' in self.data:
            verlonger = self.data['verlonger']

            def matcher(package, package_context, match_context):
                return len(re.split('[^a-zA-Z0-9]', package.version)) > verlonger

            self.matchers.append(matcher)

        if 'vergt' in self.data:
            ver = self.data['vergt']

            def matcher(package, package_context, match_context):
                return version_compare(package.version, ver) > 0

            self.matchers.append(matcher)

        if 'verge' in self.data:
            ver = self.data['verge']

            def matcher(package, package_context, match_context):
                return version_compare(package.version, ver) >= 0

            self.matchers.append(matcher)

        if 'verlt' in self.data:
            ver = self.data['verlt']

            def matcher(package, package_context, match_context):
                return version_compare(package.version, ver) < 0

            self.matchers.append(matcher)

        if 'verle' in self.data:
            ver = self.data['verle']

            def matcher(package, package_context, match_context):
                return version_compare(package.version, ver) <= 0

            self.matchers.append(matcher)

        if 'vereq' in self.data:
            ver = self.data['vereq']

            def matcher(package, package_context, match_context):
                return version_compare(package.version, ver) == 0

            self.matchers.append(matcher)

        if 'verne' in self.data:
            ver = self.data['verne']

            def matcher(package, package_context, match_context):
                return version_compare(package.version, ver) != 0

            self.matchers.append(matcher)

        if 'wwwpat' in self.data:
            pattern = self.data['wwwpat']

            def matcher(package, package_context, match_context):
                return package.homepage and pattern.fullmatch(package.homepage)

            self.matchers.append(matcher)

        if 'wwwpart' in self.data:
            wwwparts = self.data['wwwpart']

            def matcher(package, package_context, match_context):
                if not package.homepage:
                    return False
                for wwwpart in wwwparts:
                    if wwwpart in package.homepage.lower():
                        return True
                return False

            self.matchers.append(matcher)

        if 'flag' in self.data:
            flags = self.data['flag']

            def matcher(package, package_context, match_context):
                return package_context.HasFlags(flags)

            self.matchers.append(matcher)

        if 'noflag' in self.data:
            noflags = self.data['noflag']

            def matcher(package, package_context, match_context):
                return not package_context.HasFlags(noflags)

            self.matchers.append(matcher)

        # actions
        if 'remove' in self.data:
            flagval = self.data['remove']

            def action(package, package_context, match_context):
                package.SetFlag(PackageFlags.remove, flagval)

            self.actions.append(action)

        if 'ignore' in self.data:
            flagval = self.data['ignore']

            def action(package, package_context, match_context):
                package.SetFlag(PackageFlags.ignore, flagval)

            self.actions.append(action)

        if 'weak_devel' in self.data:
            flagval = self.data['weak_devel']

            def action(package, package_context, match_context):
                # XXX: currently sets ignore; change to set non-viral variant of devel (#654)
                package.SetFlag(PackageFlags.ignore, flagval)

            self.actions.append(action)

        if 'devel' in self.data:
            flagval = self.data['devel']

            def action(package, package_context, match_context):
                package.SetFlag(PackageFlags.devel, flagval)

            self.actions.append(action)

        if 'p_is_patch' in self.data:
            flagval = self.data['p_is_patch']

            def action(package, package_context, match_context):
                package.SetFlag(PackageFlags.p_is_patch, flagval)

            self.actions.append(action)

        if 'any_is_patch' in self.data:
            flagval = self.data['any_is_patch']

            def action(package, package_context, match_context):
                package.SetFlag(PackageFlags.any_is_patch, flagval)

            self.actions.append(action)

        if 'outdated' in self.data:
            flagval = self.data['outdated']

            def action(package, package_context, match_context):
                package.SetFlag(PackageFlags.outdated, flagval)

            self.actions.append(action)

        if 'legacy' in self.data:
            flagval = self.data['legacy']

            def action(package, package_context, match_context):
                package.SetFlag(PackageFlags.legacy, flagval)

            self.actions.append(action)

        if 'incorrect' in self.data:
            flagval = self.data['incorrect']

            def action(package, package_context, match_context):
                package.SetFlag(PackageFlags.incorrect, flagval)

            self.actions.append(action)

        if 'untrusted' in self.data:
            flagval = self.data['untrusted']

            def action(package, package_context, match_context):
                package.SetFlag(PackageFlags.untrusted, flagval)

            self.actions.append(action)

        if 'noscheme' in self.data:
            flagval = self.data['noscheme']

            def action(package, package_context, match_context):
                package.SetFlag(PackageFlags.noscheme, flagval)

            self.actions.append(action)

        if 'rolling' in self.data:
            flagval = self.data['rolling']

            def action(package, package_context, match_context):
                package.SetFlag(PackageFlags.rolling, flagval)

            self.actions.append(action)

        if 'snapshot' in self.data:
            flagval = self.data['snapshot']

            def action(package, package_context, match_context):
                # XXX: the same as ignored for now
                package.SetFlag(PackageFlags.ignore, flagval)

            self.actions.append(action)

        if 'successor' in self.data:
            flagval = self.data['successor']

            def action(package, package_context, match_context):
                # XXX: the same as devel for now
                package.SetFlag(PackageFlags.devel, flagval)

            self.actions.append(action)

        if 'generated' in self.data:
            flagval = self.data['generated']

            def action(package, package_context, match_context):
                # XXX: the same as rolling for now
                package.SetFlag(PackageFlags.rolling, flagval)

            self.actions.append(action)

        if 'last' in self.data:
            def action(package, package_context, match_context):
                match_context.last = True

            self.actions.append(action)

        if 'addflavor' in self.data:
            want_flavors = None
            if isinstance(self.data['addflavor'], str):
                want_flavors = [self.data['addflavor']]
            elif isinstance(self.data['addflavor'], list):
                want_flavors = self.data['addflavor']
            elif not isinstance(self.data['addflavor'], bool):
                raise RuntimeError('addflavor must be boolean or str or list')

            def action(package, package_context, match_context):
                flavors = want_flavors if want_flavors else [package.effname]

                if match_context.name_match:
                    flavors = [DOLLARN.sub(lambda x: match_context.name_match.group(int(x.group(1))), flavor) for flavor in flavors]
                else:
                    flavors = [DOLLAR0.sub(package.effname, flavor) for flavor in flavors]

                flavors = [flavor.strip('-') for flavor in flavors]

                package.flavors += [flavor for flavor in flavors if flavor]

            self.actions.append(action)

        if 'resetflavors' in self.data:
            def action(package, package_context, match_context):
                package.flavors = []

            self.actions.append(action)

        if 'addflag' in self.data:
            addflags = self.data['addflag']

            def action(package, package_context, match_context):
                for flag in addflags:
                    package_context.SetFlag(flag)

            self.actions.append(action)

        if 'setname' in self.data:
            setname = self.data['setname']

            def action(package, package_context, match_context):
                if match_context.name_match:
                    package.effname = DOLLARN.sub(lambda x: match_context.name_match.group(int(x.group(1))), setname)
                else:
                    package.effname = DOLLAR0.sub(package.effname, setname)

            self.actions.append(action)

        if 'setver' in self.data:
            setver = self.data['setver']

            def action(package, package_context, match_context):
                version_before_fix = package.version

                if package.origversion is None:
                    package.origversion = package.version

                if match_context.ver_match:
                    package.version = DOLLARN.sub(lambda x: match_context.ver_match.group(int(x.group(1))), setver)
                else:
                    package.version = DOLLAR0.sub(package.version, setver)

                package.verfixed = package.version != version_before_fix

            self.actions.append(action)

        if 'replaceinname' in self.data:
            items = list(self.data['replaceinname'].items())

            def action(package, package_context, match_context):
                for pattern, replacement in items:
                    package.effname = package.effname.replace(pattern, replacement)

            self.actions.append(action)

        if 'tolowername' in self.data:
            def action(package, package_context, match_context):
                package.effname = package.effname.lower()

            self.actions.append(action)

        if 'warning' in self.data:
            def action(package, package_context, match_context):
                print('Rule warning for {} in {}: {}'.format(package.name, package.repo, self.data['warning']), file=sys.stderr)

            self.actions.append(action)

    def match(self, package, package_context):
        match_context = MatchContext()

        for matcher in self.matchers:
            if not matcher(package, package_context, match_context):
                return None

        self.matches += 1

        return match_context

    def apply(self, package, package_context, match_context):
        for action in self.actions:
            action(package, package_context, match_context)
