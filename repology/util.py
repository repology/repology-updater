# Copyright (C) 2016-2017 Dmitry Marakasov <amdmi3@amdmi3.ru>
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


def SplitPackageNameVersion(pkgname):
    hyphen_pos = pkgname.rindex('-')

    name = pkgname[0:hyphen_pos]
    version = pkgname[hyphen_pos + 1:]

    return name, version


def GetMaintainers(instr):
    tmpresult = None
    # match "name <mail>", but not "name <at> obfuscated"
    if re.search('<[^<>]{3,}>', instr):
        tmpresult = re.findall('<([^<>]*)>', instr)
    else:
        tmpresult = instr.split(',')

    def ReverseBracket(s):
        if s == '[':
            return ']'
        if s == ']':
            return '['
        if s == '(':
            return ')'
        if s == ')':
            return '('
        if s == '<':
            return '>'
        if s == '>':
            return '<'
        if s == '{':
            return '}'
        if s == '}':
            return '{'
        return s

    def Reverse(s):
        return ''.join(map(ReverseBracket, s[::-1]))

    result = set()
    for item in tmpresult:
        # strip whitespace
        item = item.strip()

        # one spacial case
        if item.endswith(' (remove NO and SPAM)'):
            item = item[:-21].replace('NO', '').replace('SPAM', '')

        # lowercase
        item = item.lower()

        # deobfuscate
        for word, symbol in (('at', '@'), ('underscore', '_'), ('dot', '.'), ('plus', '+')):
            match = re.search('([^a-z0-9.]+)' + word + '[^a-z0-9.]', item)
            if match:
                item = item.replace(match.group(1) + word + Reverse(match.group(1)), symbol)

        for extrare in (r'agent smith \((.*)\)',):
            match = re.search(extrare, item)
            if match:
                item = match.group(1)

        for extrarepl in ((' @ google mail', '@gmail.com'), ):
            item = item.replace(extrarepl[0], extrarepl[1])

        # also assumes non-empty items
        if item.find('@') != -1:
            result.add(item)

    return sorted([item for item in result])
