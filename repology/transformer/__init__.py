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

import sys

from repology.package import Package, PackageFlags
from repology.repomgr import RepositoryManager
from repology.transformer.contexts import PackageContext
from repology.transformer.iterator import RulesetIterator
from repology.transformer.ruleset import Ruleset


class PackageTransformer:
    _ruleset: Ruleset
    _iterator: RulesetIterator

    def __init__(self, repomgr: RepositoryManager, ruleset: Ruleset) -> None:
        self._repomgr = repomgr
        self._ruleset = ruleset
        self._iterator = RulesetIterator(ruleset)

    def process(self, package: Package) -> None:
        # XXX: duplicate code: PackageMaker does the same
        package.effname = package.projectname_seed

        package_context = PackageContext()
        if package.repo:
            package_context.set_rulesets(self._repomgr.get_repository(package.repo)['ruleset'])

        for rule in self._iterator.iter_rules_for_package(package):
            match_context = rule.match(package, package_context)
            if not match_context:
                continue
            rule.apply(package, package_context, match_context)
            if match_context.last:
                break

        if package_context.warnings and not package.has_flag(PackageFlags.REMOVE):
            for warning in package_context.warnings:
                print('Rule warning for {} ({}) in {}: {}'.format(package.effname, package.trackname or '???', package.repo, warning), file=sys.stderr)

        if package.has_flag(PackageFlags.TRACE):
            print('Rule trace for {} ({}) {} in {}'.format(package.effname, package.trackname or '???', package.version, package.repo), file=sys.stderr)
            for rulenum in package_context.matched_rules:
                print('{:5d} {}'.format(rulenum, self._ruleset.get_rules()[rulenum].pretty), file=sys.stderr)
