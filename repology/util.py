# Copyright (C) 2016 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from pkg_resources import parse_version

def SplitPackageNameVersion(pkgname):
    hyphen_pos = pkgname.rindex('-')

    name = pkgname[0 : hyphen_pos]
    version = pkgname[hyphen_pos + 1 : ]

    return name, version

def VersionCompare(v1, v2):
    pv1, pv2 = parse_version(v1), parse_version(v2)
    if pv1 < pv2:
        return -1
    elif pv1 > pv2:
        return 1
    return 0
