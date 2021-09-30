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

import hashlib
import os
import sys
from copy import deepcopy
from typing import Any, Iterable, Optional

import yaml

from repology.package import Package, PackageFlags
from repology.repomgr import RepositoryManager
from repology.transformer.blocks import CoveringRuleBlock, NameMapRuleBlock, RuleBlock, SingleRuleBlock
from repology.transformer.rule import PackageContext, Rule


RULE_LOWFREQ_THRESHOLD = 0.001  # best of 0.1, 0.01, 0.001, 0.0001
COVERING_BLOCK_MIN_SIZE = 2  # covering block over single block impose extra overhead
NAMEMAP_BLOCK_MIN_SIZE = 1  # XXX: test > 1 after rule optimizations
SPLIT_MULTI_NAME_RULES = True


class RulesetStatistics:
    RuleStatistics = tuple[str, int, int]

    blocks: list[list[RuleStatistics]] = []

    def __init__(self) -> None:
        self.blocks = []

    def begin_block(self) -> None:
        self.blocks.append([])

    def add_rule(self, rule: Rule) -> None:
        self.blocks[-1].append((rule.pretty, rule.checks, rule.matches))

    def end_block(self) -> None:
        pass


class PackageTransformer:
    _repomgr: RepositoryManager
    _rules: list[Rule]
    _hash: str
    _ruleblocks: list[RuleBlock]
    _optruleblocks: list[RuleBlock]
    _packages_processed: int

    def __init__(self, repomgr: RepositoryManager, rulesdir: Optional[str] = None, rulestext: Optional[str] = None):
        self._repomgr = repomgr
        self._rules = []

        hasher = hashlib.sha256()

        if isinstance(rulestext, str):
            hasher.update(rulestext.encode('utf-8'))
            for ruledata in yaml.safe_load(rulestext):
                self._add_rule(ruledata)
        elif isinstance(rulesdir, str):
            rulefiles: list[str] = []

            for root, dirs, files in os.walk(rulesdir):
                rulefiles += [os.path.join(root, f) for f in files if f.endswith('.yaml')]
                dirs[:] = [d for d in dirs if not d.startswith('.')]

            for rulefile in sorted(rulefiles):
                with open(rulefile) as data:
                    ruleset_text = data.read()
                    hasher.update(ruleset_text.encode('utf-8'))

                    rules = yaml.safe_load(ruleset_text)
                    if rules:  # may be None for empty file
                        for rule in rules:
                            self._add_rule(rule)
        else:
            raise RuntimeError('rulesdir or rulestext must be defined')

        self._hash = hasher.hexdigest()

        self._ruleblocks = []

        current_name_rules: list[Rule] = []

        def flush_current_name_rules() -> None:
            nonlocal current_name_rules
            if len(current_name_rules) >= NAMEMAP_BLOCK_MIN_SIZE:
                self._ruleblocks.append(NameMapRuleBlock(current_name_rules))
            elif current_name_rules:
                self._ruleblocks.extend([SingleRuleBlock(rule) for rule in current_name_rules])
            current_name_rules = []

        for rule in self._rules:
            if rule.names:
                current_name_rules.append(rule)
            else:
                flush_current_name_rules()
                self._ruleblocks.append(SingleRuleBlock(rule))

        flush_current_name_rules()

        self._optruleblocks = self._ruleblocks
        self._packages_processed = 0

    def _add_rule(self, ruledata: dict[str, Any]) -> None:
        if SPLIT_MULTI_NAME_RULES and 'name' in ruledata and isinstance(ruledata['name'], list):
            for name in ruledata['name']:
                modified_ruledata = deepcopy(ruledata)
                modified_ruledata['name'] = name
                self._rules.append(Rule(len(self._rules), modified_ruledata))
        else:
            self._rules.append(Rule(len(self._rules), ruledata))

    def _recalc_opt_ruleblocks(self) -> None:
        self._optruleblocks = []

        current_lowfreq_blocks: list[RuleBlock] = []

        def flush_current_lowfreq_blocks() -> None:
            nonlocal current_lowfreq_blocks
            if len(current_lowfreq_blocks) >= COVERING_BLOCK_MIN_SIZE:
                self._optruleblocks.append(CoveringRuleBlock(current_lowfreq_blocks))
            elif current_lowfreq_blocks:
                self._optruleblocks.extend(current_lowfreq_blocks)
            current_lowfreq_blocks = []

        for block in self._ruleblocks:
            max_matches = 0
            has_unconditional = False
            for rule in block.iter_all_rules():
                max_matches = max(max_matches, rule.matches)
                if not rule.names and not rule.namepat:
                    has_unconditional = True
                    break

            if has_unconditional or max_matches >= self._packages_processed * RULE_LOWFREQ_THRESHOLD:
                flush_current_lowfreq_blocks()
                self._optruleblocks.append(block)
                continue

            current_lowfreq_blocks.append(block)

        flush_current_lowfreq_blocks()

    def _iter_package_rules(self, package: Package) -> Iterable[Rule]:
        for ruleblock in self._optruleblocks:
            yield from ruleblock.iter_rules(package)

    def process(self, package: Package) -> None:
        self._packages_processed += 1

        if self._packages_processed == 1000 or self._packages_processed == 10000 or self._packages_processed == 100000 or self._packages_processed == 1000000:
            self._recalc_opt_ruleblocks()

        # XXX: duplicate code: PackageMaker does the same
        package.effname = package.projectname_seed

        package_context = PackageContext()
        if package.repo:
            package_context.set_rulesets(self._repomgr.get_repository(package.repo)['ruleset'])

        for rule in self._iter_package_rules(package):
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
                print('{:5d} {}'.format(rulenum, self._rules[rulenum].pretty), file=sys.stderr)

    def get_statistics(self) -> RulesetStatistics:
        statistics = RulesetStatistics()

        for block in self._optruleblocks:
            statistics.begin_block()
            for rule in block.iter_all_rules():
                statistics.add_rule(rule)
            statistics.end_block()

        return statistics

    def get_ruleset_hash(self) -> str:
        return self._hash
