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

import xml.etree.cElementTree as ElementTree
from typing import Iterable, List


XmlElement = ElementTree.Element


def iter_xml_elements_at_level(path: str, level: int, tags: List[str]) -> Iterable[XmlElement]:
    """Iterate all specified elements from XML at given nesting level.

    Processed elements are cleared so large XML files may be processed
    without taking too much memory.
    """
    nestlevel = 0

    for event, elem in ElementTree.iterparse(path, events=['start', 'end']):
        if event == 'start':
            nestlevel += 1
        elif event == 'end':
            nestlevel -= 1
            if nestlevel == 1:
                if elem.tag in tags:
                    yield elem
                elem.clear()
