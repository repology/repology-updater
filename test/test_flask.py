#!/usr/bin/env python3
#
# Copyright (C) 2016 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

repology_app = __import__("repology-app")


@unittest.skipIf(not 'REPOLOGY_TEST_DSN' in os.environ, 'flask tests require database, but REPOLOGY_TEST_DSN not defined')
class TestFlask(unittest.TestCase):
    def setUp(self):
        repology_app.app.config['DSN'] = os.environ['REPOLOGY_TEST_DSN']
        self.app = repology_app.app.test_client()

    def request_and_check(self, url, has=[], hasnot=[]):
        reply = self.app.get(url)
        text = reply.data.decode('utf-8')
        for pattern in has:
            self.assertTrue(pattern in text)
        for pattern in hasnot:
            self.assertFalse(pattern in text)

    def test_static_pages(self):
        self.request_and_check('/news', has=['support added']);
        self.request_and_check('/about', has=['maintainers']);
        self.request_and_check('/api', has=['/api/v1/metapackages/all/firefox']);

    def test_badges(self):
        self.request_and_check('/badge/vertical-allrepos/kiconvtool', has=['<svg', 'FreeBSD'])
        self.request_and_check('/badge/vertical-allrepos/nonexistent', has=['<svg', 'yet'])
        self.request_and_check('/badge/tiny-packages/kiconvtool', has=['<svg', '>1<'])
        self.request_and_check('/badge/tiny-packages/nonexistent', has=['<svg', '>0<'])

    def test_metapackage(self):
        self.request_and_check('/metapackage/kiconvtool', has=['FreeBSD', '0.97', 'amdmi3'])

    def test_metapackages(self):
        self.request_and_check('/metapackages/', has=['kiconvtool', '0.97'])
        self.request_and_check('/metapackages/all/', has=['kiconvtool', '0.97'])
        self.request_and_check('/metapackages/all/k/', has=['kiconvtool', '0.97'])
        self.request_and_check('/metapackages/all/>k/', has=['kiconvtool', '0.97'])
        self.request_and_check('/metapackages/all/<l/', has=['kiconvtool', '0.97'])


if __name__ == '__main__':
    unittest.main()
