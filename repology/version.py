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
        return 0, c, 0

    number = -1 if m.group(1) == '' else int(m.group(1))

    alpha = m.group(2)

    # no alpha part, just number
    if alpha is None:
        return number, '', 0

    extranumber = -1 if m.group(3) == '' else int(m.group(3))

    # special words
    if alpha == 'alpha' or alpha == 'beta' or alpha == 'pre' or alpha == 'rc':
        alpha = alpha[0]

        # special cases, create additional triplet
        if number != -1:
            return number, '', 0, -1, alpha[0], extranumber

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
        components1.extend((0, '', 0))

    while len(components1) > len(components2):
        components2.extend((0, '', 0))

    # compare by component
    for pos in range(0, len(components1)):
        if components1[pos] < components2[pos]:
            return -1
        if components1[pos] > components2[pos]:
            return 1

    return 0
