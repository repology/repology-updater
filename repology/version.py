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


def ParseVersionCompoment(c):
    # fallback to alphanumeric comparison
    number = 0
    alpha = c
    patchlevel = 0

    # split into number-alpha-patchlevel, as in 123alpha1
    # each part is optional
    m = re.match('([0-9]*)(?:([^0-9]+)([0-9]*))?$', c.lower())

    if m:
        number = m.group(1)

        if number == '':
            number = -1
        else:
            number = int(number)

        alpha = m.group(2)

        if alpha is None:
            alpha = ''
        elif alpha != '':
            patchlevel = m.group(3)

            if patchlevel == '' or patchlevel is None:
                patchlevel = 0
            else:
                patchlevel = int(patchlevel)

    return number, alpha, patchlevel


def CompareVersionComponents(c1, c2):
    n1, a1, p1 = ParseVersionCompoment(c1)
    n2, a2, p2 = ParseVersionCompoment(c2)

    if n1 < n2:
        return -1
    elif n1 > n2:
        return 1

    if a1 < a2:
        return -1
    elif a1 > a2:
        return 1

    if p1 < p2:
        return -1
    elif p1 > p2:
        return 1

    return 0


def VersionCompare(v1, v2):
    # split by dot
    components1 = v1.split('.')
    components2 = v2.split('.')

    # align lengths
    while len(components1) < len(components2):
        components1.append("0")

    while len(components1) > len(components2):
        components2.append("0")

    # compare by component
    for pos in range(0, len(components1)):
        component_res = CompareVersionComponents(components1[pos], components2[pos])
        if component_res != 0:
            return component_res

    return 0
