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

import re

all_version_separators = re.compile('[^0-9a-z]', re.IGNORECASE)


def SplitVersionComponents(c):
    pos = 0
    end = len(c)

    # extract numeric part
    number = ''
    while pos < end and c[pos] >= '0' and c[pos] <= '9':
        number += c[pos]
        pos += 1

    number = -1 if number == '' else int(number)

    if pos == end:
        return number, '', -1

    # extract alpha part
    alpha = ''
    while pos < end and not (c[pos] >= '0' and c[pos] <= '9'):
        alpha += c[pos]
        pos += 1

    # extract second numeric part
    extranumber = ''
    while pos < end and c[pos] >= '0' and c[pos] <= '9':
        extranumber += c[pos]
        pos += 1

    # if we can't parse the whole string, give up: assume
    # alphanumeric comparison will give better result
    if pos != end:
        return -1, c, -1

    extranumber = -1 if extranumber == '' else int(extranumber)

    # note that we only take first letter, so "a" == "alpha",
    # "b" == "beta" etc.
    alpha = alpha[0].lower()

    if number != -1 and extranumber != -1:
        return number, '', -1, -1, alpha, extranumber

    # two numeric parts, create extra triplet
    return number, alpha, extranumber


def VersionCompare(v1, v2):
    components1 = []
    components2 = []

    # split by dots
    for c in all_version_separators.split(v1):
        components1.extend(SplitVersionComponents(c))

    for c in all_version_separators.split(v2):
        components2.extend(SplitVersionComponents(c))

    # align lengths
    while len(components1) < len(components2):
        components1.extend((0, '', -1))

    while len(components1) > len(components2):
        components2.extend((0, '', -1))

    # compare by component
    for pos in range(0, len(components1)):
        if components1[pos] < components2[pos]:
            return -1
        if components1[pos] > components2[pos]:
            return 1

    return 0
