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
from typing import List, Optional

from repologyapp.globals import get_text_width
from repologyapp.xmlwriter import XmlDocument


def _truncate(s: str, length: int, end: str = '...') -> str:
    if len(s) <= length:
        return s
    return s[:length - len(end)] + end


class TinyBadgeRenderer:
    @dataclass
    class _SectionInfo:
        text: str
        width: int
        color: str

    _sections: List['TinyBadgeRenderer._SectionInfo']

    def __init__(self, link: Optional[str] = None):
        self._sections = []

    def add_section(self, text: str, color: Optional[str] = None, width: Optional[int] = None, truncate: Optional[int] = None, padding: int = 10) -> None:
        if truncate is not None:
            text = _truncate(text, truncate)

        if not text:
            return

        if width is None:
            width = get_text_width(text)

        if color is None:
            color = '#555555'

        self._sections.append(TinyBadgeRenderer._SectionInfo(text=text, width=width + padding, color=color))

    def render(self) -> str:
        total_width = sum(sec.width for sec in self._sections)

        doc = XmlDocument('svg', xmlns='http://www.w3.org/2000/svg', width=total_width, height=20)

        # define clip path for rounded corners
        with doc.tag('clipPath', id='clip'):
            doc.tag('rect', rx=3, width='100%', height='100%', fill='#000')

        # define linear gradient for bevel effect
        with doc.tag('linearGradient', id='grad', x2=0, y2='100%'):
            doc.tag('stop', ('offset', 0), ('stop-color', '#bbb'), ('stop-opacity', '.1'))
            doc.tag('stop', ('offset', 1), ('stop-opacity', '.1'))

        # main data
        with doc.tag('g', ('clip-path', 'url(#clip)')):
            # section rectangles
            left = 0
            for sec in self._sections:
                doc.tag('rect', x=left, width=sec.width, height=20, fill=sec.color)
                left += sec.width

            # gradient for bevel effect
            doc.tag('rect', width='100%', height='100%', fill='url(#grad)')

            # texts
            with doc.tag('g', ('fill', '#fff'), ('text-anchor', 'middle'), ('font-family', 'DejaVu Sans,Verdana,Geneva,sans-serif'), ('font-size', 11)):
                left = 0
                for sec in self._sections:
                    with doc.tag('text', x=left + sec.width / 2, y=15, fill='#010101', **{'fill-opacity': '.3'}):
                        doc.text(sec.text)
                    with doc.tag('text', x=left + sec.width / 2, y=14):
                        doc.text(sec.text)
                    left += sec.width

        return doc.render()
