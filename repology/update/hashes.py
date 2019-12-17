# Copyright (C) 2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from typing import Iterable, Set, Tuple

from repology.database import Database
from repology.package import Package


def calculate_project_classless_hash(packages: Iterable[Package]) -> int:
    total_hash = 0
    seen_hashes: Set[int] = set()

    for package in packages:
        package_hash = package.get_classless_hash()

        if package_hash in seen_hashes:
            raise RuntimeError(f'duplicate hash for package {package}')
        else:
            seen_hashes.add(package_hash)

        total_hash ^= package_hash

    return total_hash


ProjectHash = Tuple[str, int]


def iter_project_hashes(database: Database) -> Iterable[ProjectHash]:
    prev_effname = None

    batch_size = 1000

    while True:
        pack = database.get_project_hashes(prev_effname, batch_size)
        if not pack:
            return

        yield from pack
        prev_effname = pack[-1][0]
