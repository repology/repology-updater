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


def SplitVersionComponents(c):
    # split into number-alpha-number, as in 123a1
    # each part is optional
    m = re.match('([0-9]*)(?:([^0-9]+)([0-9]*))?$', c.lower())

    # version doesn't match pattern, fallback to alphanumeric comparison
    if not m:
        return -1, c, -1

    number = -1 if m.group(1) == '' else int(m.group(1))

    alpha = m.group(2)

    # no alpha part, just number
    if alpha is None:
        return number, '', -1

    extranumber = -1 if m.group(3) == '' else int(m.group(3))

    # only take first letter into account (alpha = a, beta = b etc.)
    alpha = alpha[0]

    # if there are two numeric parts, assume prerelease (alpha/beta/pre/rc)
    # and create additional triplet
    if number != -1 and extranumber != -1:
        return number, '', -1, -1, alpha, extranumber

    return number, alpha, extranumber


def VersionCompare(v1, v2):
    components1 = []
    components2 = []

    # split by dots
    for c in v1.replace('_', '.').replace('+', '.').split('.'):
        components1.extend(SplitVersionComponents(c))

    for c in v2.replace('_', '.').replace('+', '.').split('.'):
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


def MaxVersion(v1, v2):
    if v1 and v2:
        return v1 if VersionCompare(v1, v2) > 0 else v2
    elif v1:
        return v1
    else:
        return v2
