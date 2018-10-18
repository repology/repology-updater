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


from copy import copy
from functools import total_ordering

from libversion import ANY_IS_PATCH, P_IS_PATCH, version_compare

from repology.package import PackageFlags


@total_ordering
class UserVisibleVersionInfo:
    __slots__ = ['version', 'versionclass', 'metaorder', 'versionflags', 'spread']

    def __init__(self, package, spread=1):
        self.version = package.version
        self.versionclass = package.versionclass

        self.metaorder = PackageFlags.GetMetaorder(package.flags)
        self.versionflags = (((package.flags & PackageFlags.p_is_patch) and P_IS_PATCH) |
                             ((package.flags & PackageFlags.any_is_patch) and ANY_IS_PATCH))

        self.spread = spread

    def as_with_spread(self, spread):
        result = copy(self)
        result.spread = spread
        return result

    def __eq__(self, other):
        return (self.metaorder == other.metaorder and
                self.versionclass == other.versionclass and
                self.version == other.version and
                version_compare(self.version, other.version, self.versionflags, other.versionflags) == 0 and
                self.spread == other.spread)

    def __lt__(self, other):
        if self.metaorder < other.metaorder:
            return True
        if self.metaorder > other.metaorder:
            return False

        res = version_compare(
            self.version,
            other.version,
            self.versionflags,
            other.versionflags
        )

        if res < 0:
            return True
        if res > 0:
            return False

        if self.versionclass < other.versionclass:
            return True
        if self.versionclass > other.versionclass:
            return False

        if self.spread < other.spread:
            return True
        if self.spread > other.spread:
            return False

        return self.version < other.version

    def __hash__(self):
        return hash((self.metaorder, self.versionclass, self.version, self.spread))
