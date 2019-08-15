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

from markupsafe import escape

from repologyapp.globals import get_text_width


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

        if width is None:
            width = get_text_width(text)

        if color is None:
            color = '#555555'

        self._sections.append(TinyBadgeRenderer._SectionInfo(text=text, width=width + padding, color=color))

    def render(self) -> str:
        total_width = sum(sec.width for sec in self._sections)

        rects = []
        texts = []

        left = 0
        for sec in self._sections:
            rects.append(
                '<rect x="{left}" width="{width}" height="20" fill="{color}"/>'.format(
                    left=left,
                    width=sec.width,
                    color=sec.color
                )
            )

            text = escape(sec.text)

            texts.append(
                '<text x="{textx}" y="15" fill="#010101" fill-opacity=".3">{text}</text>'.format(
                    textx=left + sec.width / 2,
                    text=text
                )
            )

            texts.append(
                '<text x="{textx}" y="14">{text}</text>'.format(
                    textx=left + sec.width / 2,
                    text=text
                )
            )

            left += sec.width

        return """
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{total_width}" height="20">
    <clipPath id="clip">
        <rect rx="3" width="100%" height="100%" fill="#000"/>
    </clipPath>
    <linearGradient id="grad" x2="0" y2="100%"><stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
        <stop offset="1" stop-opacity=".1"/>
    </linearGradient>

    <g clip-path="url(#clip)">
        {rects}
        <rect width="100%" height="100%" fill="url(#grad)"/>
        <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
            {texts}
        </g>
    </g>
</svg>
        """.strip().format(
            total_width=total_width,
            rects=''.join(rects),
            texts=''.join(texts),
        )
