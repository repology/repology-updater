# Copyright (C) 2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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


@dataclass(unsafe_hash=True)
class CPE:
    part:       str = '*'
    vendor:     str = '*'
    product:    str = '*'
    version:    str = '*'
    update:     str = '*'
    edition:    str = '*'
    lang:       str = '*'
    sw_edition: str = '*'
    target_sw:  str = '*'
    target_hw:  str = '*'
    other:      str = '*'

def cpe_parse(cpe_str: str) -> CPE:
    escaped = False
    current = ''
    res = []

    for char in cpe_str:
        if escaped:
            current += '\\' + char
            escaped = False
        elif char == '\\':
            escaped = True
        elif char == ':':
            res.append(current)
            current = ''
        else:
            current += char

    res.append(current)

    if len(res) < 3:
        return CPE()            # input seems to be faulty, return default CPE
    elif res[1] == '2.3':
        return CPE(*res[3:])    # input seems to be CPE format 2.3
    else:
        return CPE(*res[2:])    # input seems to be CPE format 2.2
