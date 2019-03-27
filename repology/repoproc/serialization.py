# Copyright (C) 2018-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
from contextlib import ExitStack
from typing import Any, BinaryIO, Iterable, Iterator, List, Optional

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


class StreamDeserializer:
    _path: str
    _fd: BinaryIO
    _unpickler: pickle.Unpickler
    _remaining: int
    current: Optional[Package]

    def __init__(self, path: str):
        self._path = path

    def __enter__(self) -> 'StreamDeserializer':
        self._fd = open(self._path, 'rb')

        try:
            self._unpickler = pickle.Unpickler(self._fd)
            self._remaining = self._unpickler.load()
            self.current = None

            self.pop()

            return self
        except:
            self._fd.close()
            raise

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self._fd.close()

    def pop(self) -> None:
        if self._remaining > 0:
            self.current = self._unpickler.load()
            self._remaining -= 1
        else:
            self.current = None
            self._remaining = -1


def heap_deserialize(paths: Iterable[str]) -> Iterator[List[Package]]:
    with ExitStack() as stack:
        deserializers = [stack.enter_context(StreamDeserializer(path)) for path in paths]

        thiskey = min((ds.current.effname for ds in deserializers if ds.current is not None), default=None)

        while thiskey is not None:
            nextkey = None

            # fetch all packages with given key from all deserializers
            packages = []
            for ds in deserializers:
                while ds.current is not None and ds.current.effname == thiskey:
                    packages.append(ds.current)
                    ds.pop()

                if ds.current is not None and (nextkey is None or ds.current.effname < nextkey):
                    nextkey = ds.current.effname

            yield packages
            thiskey = nextkey
