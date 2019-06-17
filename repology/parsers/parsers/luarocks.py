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

from typing import Any, Dict, Iterable

from pyparsing import Empty, Forward, QuotedString, Regex, Suppress, ZeroOrMore

from repology.packagemaker import PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.transformer import PackageTransformer


def _parse_data(data: str) -> Dict[str, Any]:
    lcur, rcur, lbrk, rbrk, comma, eq = map(Suppress, '{}[],=')

    tablekey = Regex(r'[a-z][a-z0-9_]*') | (lbrk + QuotedString(quoteChar="'") + rbrk)
    qstring = QuotedString(quoteChar='"')

    value = Forward()

    keyval = (tablekey + eq + value).setParseAction(lambda s, l, t: [(str(t[0]), t[1])])

    array_table = (value + ZeroOrMore(comma + value)).setParseAction(lambda s, l, t: [list(t)])
    dict_table = (keyval + ZeroOrMore(comma + keyval)).setParseAction(lambda s, l, t: [{k: v for k, v in t}])

    table = lcur + (dict_table | array_table | Empty().setParseAction(lambda s, l, t: [None])) + rcur
    value << (qstring | table)

    root = ZeroOrMore(keyval).setParseAction(lambda s, l, t: {k: v for k, v in t})

    return root.parseString(data, parseAll=True)[0]  # type: ignore


class LuaRocksParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        with open(path, encoding='utf-8', errors='ignore') as contents:
            data = contents.read()

        for pkgname, pkgdata in _parse_data(data)['repository'].items():
            with factory.begin() as pkg:
                pkg.set_name(pkgname)

                for version, versiondatas in pkgdata.items():
                    for versiondata in versiondatas:
                        verpkg = pkg.clone()

                        verpkg.set_rawversion(version)
                        verpkg.set_version(version.rsplit('-', 1)[0])
                        verpkg.set_arch(versiondata['arch'])

                        yield verpkg
