# Copyright (C) 2017 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import PIL.ImageFont


class FontMeasurer:
    def __init__(self, fontpath, fontsize, maxcachesize=1000):
        self.font = PIL.ImageFont.truetype(fontpath, fontsize)
        self.cache = {}
        self.maxcachesize = maxcachesize
        self.generation = 0

    def GetDimensions(self, text):
        self.generation += 1

        if text in self.cache:
            item = self.cache[text]
            item[1] = self.generation
            return item[0]

        dimensions = self.font.getsize(text)

        if len(self.cache) >= self.maxcachesize:
            # if cache is full, remove at least 10% LRU entries
            last_generation = self.generation - len(self.cache) + max(self.maxcachesize // 10, len(self.cache) + 1 - self.maxcachesize)

            for key in list(self.cache.keys()):
                if self.cache[key][1] < last_generation:
                    del self.cache[key]

        self.cache[text] = [dimensions, self.generation]

        return dimensions
