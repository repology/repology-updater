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

        first_result = fontmeas.GetDimensions('The quick brown fox jumps over the lazy dog')
        cached_result = fontmeas.GetDimensions('The quick brown fox jumps over the lazy dog')

        self.assertEqual(first_result, cached_result)

        # I've got 254 on FreeBSD and 258 on Ubuntu, I believe there
        # are fluctuations because of freetype hinting settings
        #
        # We currently use 6 pixel padding for badge texts. I'd say
        # that for center-aligned text we can tolerate fluctuations
        # of this size (e.g. +/-6, which may eat up to half of the
        # padding on each size), and for side-aligned text we can
        # add additional 3 pixel safety padding
        #
        # Note also that real strings will be usually shorter than
        # this example

        self.assertTrue(abs(first_result[0] - 254) <= 6)


if __name__ == '__main__':
    unittest.main()
