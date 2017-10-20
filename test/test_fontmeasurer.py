#!/usr/bin/env python3
#
# Copyright (C) 2017 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import os
import unittest

from repologyapp.fontmeasurer import FontMeasurer

from repology.config import config


@unittest.skipIf('BADGE_FONT' not in config, 'font measurer test requires BADGE_FONT configuration directive defined')
class FontMeasurerTest(unittest.TestCase):
    def test_fontmeasurer(self):
        fontmeas = FontMeasurer(config['BADGE_FONT'], 11)

        self.assertEqual(fontmeas.GetDimensions('The quick brown fox jumps over the lazy dog'), (254, 13))
        self.assertEqual(fontmeas.GetDimensions('The quick brown fox jumps over the lazy dog'), (254, 13))  # cached


if __name__ == '__main__':
    unittest.main()
