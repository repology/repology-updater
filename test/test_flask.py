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

    def test_static_pages(self):
        reply = self.app.get('/news')
        self.assertTrue('support added' in reply.data.decode('utf-8'))

        reply = self.app.get('/about')
        self.assertTrue('maintainers' in reply.data.decode('utf-8'))

        reply = self.app.get('/api')
        self.assertTrue('/api/v1/metapackages/all/firefox' in reply.data.decode('utf-8'))

    def test_badges(self):
        reply = self.app.get('/badge/vertical-allrepos/kiconvtool')
        self.assertTrue('<svg' in reply.data.decode('utf-8'))
        self.assertTrue('FreeBSD' in reply.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
