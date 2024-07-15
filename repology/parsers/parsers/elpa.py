# Copyright (C) 2019, 2021, 2023 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
from typing import Any, Iterable

from pyparsing import OneOrMore, QuotedString, Regex, Suppress, Word, ZeroOrMore, alphas, printables

from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers


@dataclass
class _PackageData:
    name: str
    version: str
    summary: str
    keyvals: dict[str, Any]


def _parse_data(data: str) -> list[_PackageData]:
    lpar, rpar, lbrk, rbrk, dot = map(Suppress, '()[].')
    nil = Suppress('nil')

    pkgname = Word(printables)
    decimal = Regex(r'0|-?[1-9]\d*').setParseAction(lambda t: int(t[0]))
    qstring = QuotedString(quoteChar='"', escChar='\\')

    version = (lpar + OneOrMore(decimal) + rpar).setParseAction(lambda s, l, t: ['.'.join(map(str, t))])

    dependency_entry = lpar + pkgname + version + rpar
    dependency_list = ((lpar + OneOrMore(dependency_entry) + rpar) | nil)

    people_list = OneOrMore(qstring | dot | nil)

    keyval_url = (lpar + (Suppress(':url') | Suppress(':homepage')) + dot + qstring + rpar).setParseAction(lambda s, l, t: [('url', t[0])])
    keyval_keywords = (lpar + Suppress(':keywords') + ZeroOrMore(qstring) + rpar).setParseAction(lambda s, l, t: [('keywords', [str(k) for k in t])])
    keyval_commit = (lpar + Suppress(':commit') + dot + qstring + rpar).setParseAction(lambda s, l, t: [('commit', t[0])])
    keyval_maintainer = (lpar + Suppress(':maintainer') + people_list + rpar).setParseAction(lambda s, l, t: [('maintainer', [str(m) for m in t])])
    keyval_maintainer_multi = (lpar + Suppress(':maintainer') + OneOrMore(lpar + people_list + rpar) + rpar).setParseAction(lambda s, l, t: [('maintainer_multi', [str(m) for m in t])])
    keyval_maintainers = (lpar + Suppress(':maintainers') + lpar + people_list + rpar + rpar).setParseAction(lambda s, l, t: [('maintainers', [str(m) for m in t])])
    keyval_maintainers_multi = (lpar + Suppress(':maintainers') + OneOrMore(lpar + people_list + rpar) + rpar).setParseAction(lambda s, l, t: [('maintainers_multi', [str(m) for m in t])])
    keyval_author = (lpar + Suppress(':author') + people_list + rpar).setParseAction(lambda s, l, t: [('author', [str(a) for a in t])])
    keyval_authors = (lpar + Suppress(':authors') + OneOrMore(lpar + people_list + rpar) + rpar).setParseAction(lambda s, l, t: [('authors', [str(a) for a in t])])

    keyval_item = keyval_url | keyval_keywords | keyval_commit | keyval_maintainer | keyval_maintainer_multi | keyval_maintainers | keyval_maintainers_multi | keyval_authors | keyval_author

    keyvals = (lpar + ZeroOrMore(keyval_item) + rpar).setParseAction(lambda s, l, t: [{k: v for k, v in t}]) | nil.setParseAction(lambda s, l, t: [{}])

    package_entry = (lpar + pkgname + dot + lbrk + version + Suppress(dependency_list) + qstring + Suppress(Word(alphas)) + keyvals + rbrk + rpar).setParseAction(lambda s, l, t: [_PackageData(*t)])

    root = lpar + Suppress(decimal) + ZeroOrMore(package_entry) + rpar

    return root.parseString(data, parseAll=True)  # type: ignore


class ArchiveContentsParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        with open(path, encoding='utf-8', errors='ignore') as contents:
            data = contents.read()

        for pkgdata in _parse_data(data):
            with factory.begin() as pkg:
                pkg.add_name(pkgdata.name, NameType.ELPA_NAME)
                pkg.set_version(pkgdata.version)
                pkg.set_summary(pkgdata.summary)

                for key in ['maintainer', 'maintainer_multi', 'maintainers', 'maintainers_multi']:
                    if key in pkgdata.keyvals:
                        maintainers: list[str] = sum(map(extract_maintainers, pkgdata.keyvals[key]), [])
                        pkg.add_maintainers(maintainers)

                pkg.add_homepages(pkgdata.keyvals.get('url'))

                # XXX: enable when we support multiple categories
                #pkg.add_categories(pkgdata.keyvals.get('keywords'))

                yield pkg
