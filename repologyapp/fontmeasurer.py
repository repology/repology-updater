# Copyright (C) 2017-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from dataclasses import dataclass
from typing import Dict, Tuple

import PIL.ImageFont


_Dimensions = Tuple[int, int]


@dataclass
class _CacheEntry:
    dimensions: _Dimensions
    generation: int


class FontMeasurer:
    _font: PIL.ImageFont
    _cache: Dict[str, _CacheEntry]
    _maxcachesize: int
    _generation: int

    def __init__(self, fontpath: str, fontsize: int, maxcachesize: int = 1000) -> None:
        self._font = PIL.ImageFont.truetype(fontpath, fontsize)
        self._cache = {}
        self._maxcachesize = maxcachesize
        self._generation = 0

    def get_text_dimensions(self, text: str) -> Tuple[int, int]:
        self._generation += 1

        if text in self._cache:
            item = self._cache[text]
            item.generation = self._generation
            return item.dimensions

        dimensions: _Dimensions = self._font.getsize(text)

        if len(self._cache) >= self._maxcachesize:
            # if cache is full, remove at least 10% LRU entries
            last_generation = self._generation - len(self._cache) + max(self._maxcachesize // 10, len(self._cache) + 1 - self._maxcachesize)

            for key in list(self._cache.keys()):
                if self._cache[key].generation < last_generation:
                    del self._cache[key]

        self._cache[text] = _CacheEntry(dimensions, self._generation)

        return dimensions
