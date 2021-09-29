# Copyright (C) 2016-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
from typing import Any


def extract_maintainers(input_: Any) -> list[str]:
    if not input_:
        return []

    def looks_like_email(s: str) -> bool:
        return bool(re.fullmatch('[^<> \t]+@[^<> \t]+', s))

    addresses = set()
    for part in input_.lower().split(','):
        words = part.strip().split()

        has_other_words = False
        candidates = set()
        for word in words:
            if word.startswith('<') and word.endswith('>'):
                # emaily thing in angle brackets is most likely
                # complete, so just use it
                word = word.strip('<>')
                if looks_like_email(word):
                    addresses.add(word)
            elif looks_like_email(word):
                # standalone emaily thing may be part of obfuscated string...
                candidates.add(word)
            else:
                # ...so check if there are other words around...
                has_other_words = True

        # ...and only use it if there are none
        if not has_other_words:
            addresses |= candidates

    return sorted(addresses)
