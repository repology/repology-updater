# Copyright (C) 2021 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
import pickle
from collections import defaultdict


class RuleMatchStatistics:
    """Registry of Rule match frequency.

    This class stores information in Rule match frequency, e.g. how
    many times a Rule was matched per total number of Packages
    processed. This information is used in optimized Ruleset lookups.

    This class also supports persist storage, so complete frequency
    info from a previous parse run may be reused for the next run.

    Note that we cannot reference Rules by number here, as numbers
    may change between parse runes, so Rules are instead referenced
    by their hashes.
    """

    __slots__ = ['_total_packages', '_rule_match_counts']

    _total_packages: int
    _rule_match_counts: dict[int, int]

    def __init__(self, path: str | None = None) -> None:
        self._total_packages = 0
        self._rule_match_counts = defaultdict(int)

        if path is not None:
            self.load(path)

    def count_package(self) -> None:
        self._total_packages += 1

    def count_rule_match(self, rulehash: int) -> None:
        self._rule_match_counts[rulehash] += 1

    def get_rule_frequency(self, rulehash: int) -> float:
        if self._total_packages == 0:
            return 0.0

        return self._rule_match_counts.get(rulehash, 0.0) / self._total_packages

    def get_total_packages(self) -> int:
        return self._total_packages

    def load(self, path: str) -> None:
        try:
            with open(path, 'rb') as fd:
                loaded = pickle.load(fd)
                self._total_packages = loaded._total_packages
                self._rule_match_counts = loaded._rule_match_counts
        except (EOFError, FileNotFoundError, pickle.UnpicklingError):
            pass

    def dump(self, path: str) -> None:
        with open(path, 'wb') as fd:
            pickle.dump(self, fd)
            fd.flush()
            os.fsync(fd.fileno())
