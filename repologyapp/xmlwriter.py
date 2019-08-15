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

from itertools import chain
from typing import Any, Dict, List, Tuple


def _escape(val: Any) -> str:
    if isinstance(val, int):
        return str(val)

    return str(val).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&apos;')


class _XmlElement:
    __slots__ = ['_document', '_tagname', '_rawattrs', '_attrs', '_childs']

    _document: 'XmlDocument'
    _tagname: str
    _rawattrs: Tuple[Tuple[str, Any], ...]
    _attrs: Dict[str, Any]
    _childs: List[Any]

    def __init__(self, document: 'XmlDocument', tagname: str, *rawattrs: Tuple[str, Any], **attrs: Any) -> None:
        self._document = document
        self._tagname = tagname
        self._rawattrs = rawattrs
        self._attrs = attrs
        self._childs = []

    def __enter__(self) -> None:
        self._document._path.append(self)

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self._document._path.pop()

    def render(self) -> str:
        res = '<' + self._tagname

        for k, v in chain(self._rawattrs, self._attrs.items()):
            res += ' ' + k + '="' + _escape(v) + '"'

        if self._childs:
            res += '>'
            for child in self._childs:
                if isinstance(child, _XmlElement):
                    res += child.render()
                else:
                    res += _escape(child)
            res += '</' + self._tagname + '>'
        else:
            res += '/>'

        return res


class XmlDocument:
    __slots__ = ['_root', '_path']

    _root: _XmlElement
    _path: List[_XmlElement]

    def __init__(self, tagname: str, *rawattrs: Any, **attrs: Any) -> None:
        root = _XmlElement(self, tagname, *rawattrs, **attrs)
        self._root = root
        self._path = [root]

    def tag(self, tagname: str, *rawattrs: Any, **attrs: Any) -> _XmlElement:
        elt = _XmlElement(self, tagname, *rawattrs, **attrs)
        self._path[-1]._childs.append(elt)
        return elt

    def text(self, text: str) -> None:
        self._path[-1]._childs.append(text)

    def render(self) -> str:
        return self._root.render()
