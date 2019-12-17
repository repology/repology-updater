# Copyright (C) 2018-2020 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import heapq
import os
import pickle
from typing import Iterable, Iterator, List

from repology.package import Package


class ChunkedSerializer:
    path: str
    next_chunk_number: int
    chunk_size: int
    packages: List[Package]
    total_packages: int

    def __init__(self, path: str, chunk_size: int) -> None:
        self.path = path
        self.next_chunk_number = 0
        self.chunk_size = chunk_size
        self.packages = []
        self.total_packages = 0

    def _flush(self) -> None:
        if not self.packages:
            return

        packages = sorted(self.packages, key=lambda package: package.effname)

        with open(os.path.join(self.path, str(self.next_chunk_number)), 'wb') as outfile:
            pickler = pickle.Pickler(outfile, protocol=pickle.HIGHEST_PROTOCOL)
            pickler.fast = True  # deprecated, but I don't see any alternatives
            pickler.dump(len(packages))
            for package in packages:
                pickler.dump(package)
            outfile.flush()
            os.fsync(outfile.fileno())

        self.packages = []
        self.next_chunk_number += 1

    def serialize(self, packages: Iterable[Package]) -> None:
        for package in packages:
            self.packages.append(package)
            self.total_packages += 1

            if len(self.packages) >= self.chunk_size:
                self._flush()

        self._flush()

    def get_num_packages(self) -> int:
        return self.total_packages


def _stream_deserialize(path: str) -> Iterator[Package]:
    with open(path, 'rb') as fd:
        unpickler = pickle.Unpickler(fd)
        count = unpickler.load()

        for _ in range(count):
            yield unpickler.load()


def heap_deserialize(paths: Iterable[str]) -> Iterator[List[Package]]:
    packages: List[Package] = []

    for package in heapq.merge(*(_stream_deserialize(path) for path in paths), key=lambda p: p.effname):
        if packages and packages[0].effname != package.effname:
            yield packages
            packages = []
        packages.append(package)

    yield packages
