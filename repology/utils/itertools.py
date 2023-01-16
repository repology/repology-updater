# Copyright (C) 2023 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from typing import Iterable, Iterator, TypeVar

__all__ = ['chain_optionals', 'unicalize']


_T = TypeVar('_T')


def chain_optionals(*iterables: Iterable[_T] | None) -> Iterator[_T]:
    for iterator in iterables:
        if iterator is not None:
            yield from iterator


def unicalize(values: Iterable[_T]) -> Iterator[_T]:
    seen = set()

    for value in values:
        if value not in seen:
            seen.add(value)
            yield value
