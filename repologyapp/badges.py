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

from typing import Dict, List, Optional, Tuple

from repologyapp.globals import get_text_width
from repologyapp.xmlwriter import XmlDocument

from repology.package import PackageStatus


def _truncate(s: str, length: int, end: str = '...') -> str:
    if len(s) <= length:
        return s
    return s[:length - len(end)] + end


class BadgeCell:
    __slots__ = ['text', 'width', 'color', 'collapsible', 'align']

    text: str
    width: int
    color: Optional[str]
    collapsible: bool
    align: str

    def __init__(self,
                 text: str = '',
                 color: Optional[str] = None,
                 width: Optional[int] = None,
                 truncate: Optional[int] = None,
                 padding: int = 10,
                 collapsible: bool = False,
                 align: str = 'c',
                 minwidth: int = 0) -> None:
        self.text = text if truncate is None else _truncate(text, truncate)
        self.width = max(
            (get_text_width(self.text, 11) if width is None else width) + padding,
            minwidth
        )
        self.color = color
        self.collapsible = collapsible
        self.align = align


def render_generic_badge(rows: List[List[BadgeCell]], header: Optional[str] = None, min_width: int = 0) -> Tuple[str, Dict[str, str]]:
    num_rows = len(rows)
    num_columns = len(rows[0]) if rows else 0

    column_widths = [0] * num_columns
    column_collapsed = [True] * num_columns

    # calculate column widths
    for row in rows:
        for ncol, cell in enumerate(row):
            column_widths[ncol] = max(column_widths[ncol], cell.width)
            if cell.text or not cell.collapsible:
                column_collapsed[ncol] = False

    # handle collapsed columns and finalize metrics
    column_offsets = [0] * num_columns
    for ncol in range(num_columns):
        if column_collapsed[ncol]:
            column_widths[ncol] = 0

        if ncol < num_columns - 1:
            column_offsets[ncol + 1] = column_offsets[ncol] + column_widths[ncol]

    header_height = 0
    if header:
        header_height = 25
        min_width = max(min_width, get_text_width(header, 15, bold=True) + 10)

    total_height = header_height + 20 * num_rows
    total_width = (column_offsets[-1] + column_widths[-1]) if num_columns else 0

    # force minimal width by expanding leftmost column
    if total_width < min_width:
        increment = min_width - total_width
        total_width = min_width

        for ncol in range(num_columns):
            flexible_column = 0
            if ncol == flexible_column:
                column_widths[ncol] += increment
            elif ncol > flexible_column:
                column_offsets[ncol] += increment

    doc = XmlDocument('svg', xmlns='http://www.w3.org/2000/svg', width=total_width, height=total_height)

    # define clip path for rounded corners
    with doc.tag('clipPath', id='clip'):
        doc.tag('rect', rx=3, width='100%', height='100%', fill='#000')

    # define linear gradient for bevel effect
    with doc.tag('linearGradient', id='grad', x2=0, y2='100%'):
        doc.tag('stop', ('offset', 0), ('stop-color', '#bbb'), ('stop-opacity', '.1'))
        doc.tag('stop', ('offset', 1), ('stop-opacity', '.1'))

    # graphical data
    with doc.tag('g', ('clip-path', 'url(#clip)')):
        # background
        doc.tag('rect', width='100%', height='100%', fill='#555')

        # header
        if header:
            with doc.tag('g', ('fill', '#fff'), ('text-anchor', 'middle'), ('font-family', 'DejaVu Sans,Verdana,Geneva,sans-serif'), ('font-size', 15), ('font-weight', 'bold')):
                with doc.tag('text', x=total_width / 2, y=18, fill='#010101', **{'fill-opacity': '.3'}):
                    doc.text(header)
                with doc.tag('text', x=total_width / 2, y=17):
                    doc.text(header)

        # rows
        for nrow, row in enumerate(rows):
            # cell backgrounds
            for ncol, cell in enumerate(row):
                if cell.color is None or column_collapsed[ncol]:
                    continue

                doc.tag(
                    'rect',
                    x=column_offsets[ncol],
                    y=header_height + nrow * 20,
                    width=column_widths[ncol],
                    height=20,
                    fill=cell.color
                )

            # gradient
            doc.tag('rect', y=header_height + nrow * 20, width='100%', height=20, fill='url(#grad)')

            # cell texts
            with doc.tag('g', ('fill', '#fff'), ('font-family', 'DejaVu Sans,Verdana,Geneva,sans-serif'), ('font-size', 11)):
                for ncol, cell in enumerate(row):
                    if not cell.text or column_collapsed[ncol]:
                        continue

                    text_x: float
                    if cell.align.startswith('l'):
                        text_x = column_offsets[ncol] + 5
                        text_anchor = 'start'
                    elif cell.align.startswith('r'):
                        text_x = column_offsets[ncol] + column_widths[ncol] - 5
                        text_anchor = 'end'
                    else:
                        text_x = column_offsets[ncol] + column_widths[ncol] / 2
                        text_anchor = 'middle'

                    with doc.tag('text', x=text_x, y=header_height + nrow * 20 + 15, fill='#010101', **{'fill-opacity': '.3', 'text-anchor': text_anchor}):
                        doc.text(cell.text)
                    with doc.tag('text', x=text_x, y=header_height + nrow * 20 + 14, **{'text-anchor': text_anchor}):
                        doc.text(cell.text)

    return (
        doc.render(),
        {'Content-type': 'image/svg+xml'}
    )


def badge_color(versionclass: int, unsatisfying: bool = False) -> str:
    if unsatisfying:
        return '#e00000'
    elif versionclass in [PackageStatus.OUTDATED, PackageStatus.LEGACY]:
        return '#e05d44'
    elif versionclass in [PackageStatus.NEWEST, PackageStatus.UNIQUE, PackageStatus.DEVEL]:
        return '#4c1'
    else:
        return '#9f9f9f'
