# Copyright (C) 2016-2021 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from collections import defaultdict
from typing import Iterable, Optional

from repology.package import Package


def packageset_deduplicate(packages: Iterable[Package]) -> list[Package]:
    aggregated: dict[tuple[str, Optional[str], Optional[str], str], list[Package]] = defaultdict(list)

    # aggregate by subset of fields to make O(n²) merge below faster
    for package in packages:
        key = (package.repo, package.subrepo, package.name, package.version)
        aggregated[key].append(package)

    outpkgs = []
    for aggregated_packages in aggregated.values():
        while aggregated_packages:
            nextpackages = []
            for package in aggregated_packages[1:]:
                if package != aggregated_packages[0]:
                    nextpackages.append(package)

            outpkgs.append(aggregated_packages[0])
            aggregated_packages = nextpackages

    return outpkgs
