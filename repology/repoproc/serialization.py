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

import pickle
from contextlib import ExitStack, contextmanager


def serialize(objects, path):
    with open(path, 'wb') as outfile:
        pickler = pickle.Pickler(outfile, protocol=pickle.HIGHEST_PROTOCOL)
        pickler.fast = True  # deprecated, but I don't see any alternatives
        pickler.dump(len(objects))
        for obj in objects:
            pickler.dump(obj)


class StreamDeserializer:
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        self.fd = open(self.path, 'rb')

        try:
            self.unpickler = pickle.Unpickler(self.fd)
            self.remaining = self.unpickler.load()
            self.current = None

            self.pop()

            return self
        except:
            self.fd.close()
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.fd.close()

    def pop(self):
        current = self.current

        if self.remaining > 0:
            self.current = self.unpickler.load()
            self.remaining -= 1
        else:
            self.current = None
            self.remaining = -1

        return current

    def peek(self):
        return self.current

    def is_eof(self):
        return self.remaining == -1


@contextmanager
def heap_deserializer(paths, getkey):
    with ExitStack() as stack:
        deserializers = [stack.enter_context(StreamDeserializer(path)) for path in paths]

        def iterate():
            while True:
                # find lowest key
                thiskey = min((getkey(ds.peek()) for ds in deserializers if not ds.is_eof()), default=None)
                if thiskey is None:
                    return

                # fetch all packages with given key from all deserializers
                packages = []
                for ds in deserializers:
                    while not ds.is_eof() and getkey(ds.peek()) == thiskey:
                        packages.append(ds.pop())

                yield packages

        yield iterate
