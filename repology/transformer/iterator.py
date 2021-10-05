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

from typing import Iterator

from repology.package import Package
from repology.transformer.blocks import CoveringRuleBlock, NameMapRuleBlock, RuleBlock, SingleRuleBlock
from repology.transformer.rule import Rule
from repology.transformer.ruleset import Ruleset


RULE_LOWFREQ_THRESHOLD = 0.001  # best of 0.1, 0.01, 0.001, 0.0001
COVERING_BLOCK_MIN_SIZE = 2  # covering block over single block impose extra overhead
NAMEMAP_BLOCK_MIN_SIZE = 1  # XXX: test > 1 after rule optimizations


class RulesetIterator:
    _ruleset: Ruleset
    _ruleblocks: list[RuleBlock]
    _optruleblocks: list[RuleBlock]
    _packages_processed: int

    def __init__(self, ruleset: Ruleset) -> None:
        self._ruleset = ruleset
        self._ruleblocks = []

        current_name_rules: list[Rule] = []

        def flush_current_name_rules() -> None:
            nonlocal current_name_rules
            if len(current_name_rules) >= NAMEMAP_BLOCK_MIN_SIZE:
                self._ruleblocks.append(NameMapRuleBlock(current_name_rules))
            elif current_name_rules:
                self._ruleblocks.extend([SingleRuleBlock(rule) for rule in current_name_rules])
            current_name_rules = []

        for rule in self._ruleset.get_rules():
            if rule.names:
                current_name_rules.append(rule)
            else:
                flush_current_name_rules()
                self._ruleblocks.append(SingleRuleBlock(rule))

        flush_current_name_rules()

        self._optruleblocks = self._ruleblocks
        self._packages_processed = 0

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

    def iter_rules_for_package(self, package: Package) -> Iterator[Rule]:
        self._packages_processed += 1

        if self._packages_processed == 1000 or self._packages_processed == 10000 or self._packages_processed == 100000 or self._packages_processed == 1000000:
            self._recalc_opt_ruleblocks()

        for ruleblock in self._optruleblocks:
            yield from ruleblock.iter_rules(package)
