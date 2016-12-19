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
import json
import unittest

repology_app = __import__("repology-app")


@unittest.skipIf(not 'REPOLOGY_TEST_DSN' in os.environ, 'flask tests require database, but REPOLOGY_TEST_DSN not defined')
class TestFlask(unittest.TestCase):
    def setUp(self):
        repology_app.app.config['DSN'] = os.environ['REPOLOGY_TEST_DSN']
        self.app = repology_app.app.test_client()

    def request_and_check(self, url, status_code=200, mimetype='text/html', has=[], hasnot=[]):
        reply = self.app.get(url)
        if status_code is not None:
            self.assertEqual(reply.status_code, status_code)
        if mimetype is not None:
            self.assertEqual(reply.mimetype, mimetype)
        text = reply.data.decode('utf-8')
        for pattern in has:
            self.assertTrue(pattern in text)
        for pattern in hasnot:
            self.assertFalse(pattern in text)
        return text

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

    def test_maintaners(self):
        self.request_and_check('/maintainers/', has=['amdmi3@freebsd.org'])
        self.request_and_check('/maintainers/0/', has=['amdmi3@freebsd.org'])

    def test_metapackages(self):
        self.request_and_check('/metapackages/', has=['kiconvtool', '0.97'])

        self.request_and_check('/metapackages/all/', has=['kiconvtool'])
        self.request_and_check('/metapackages/all/k/', has=['kiconvtool'])
        self.request_and_check('/metapackages/all/>k/', has=['kiconvtool'])
        self.request_and_check('/metapackages/all/<l/', has=['kiconvtool'])
        self.request_and_check('/metapackages/all/l/', hasnot=['kiconvtool'])
        self.request_and_check('/metapackages/all/<kiconvtool/', hasnot=['kiconvtool'])
        self.request_and_check('/metapackages/all/>kiconvtool/', hasnot=['kiconvtool'])

        self.request_and_check('/metapackages/in-repo/', has=['FreeBSD'])
        self.request_and_check('/metapackages/in-repo/freebsd/', has=['kiconvtool'])

        self.request_and_check('/metapackages/not-in-repo/', has=['FreeBSD'])
        self.request_and_check('/metapackages/not-in-repo/freebsd/', has=['chromium-bsu', 'zlib'], hasnot=['kiconvtool'])

        self.request_and_check('/metapackages/unique-in-repo/', has=['FreeBSD'])
        self.request_and_check('/metapackages/unique-in-repo/freebsd/', has=['kiconvtool'])

        self.request_and_check('/metapackages/unique/', has=['kiconvtool'])

        self.request_and_check('/metapackages/by-maintainer/amdmi3@freebsd.org/', has=['kiconvtool'])

        # special cases: check fallback code for going before first or after last entry
        self.request_and_check('/metapackages/all/<0/', has=['kiconvtool'])
        self.request_and_check('/metapackages/all/>zzzzzz/', has=['kiconvtool'])

    def test_api_v1_metapackage(self):
        packages = json.loads(self.app.get('/api/v1/metapackage/kiconvtool').data.decode('utf-8'))
        self.assertEqual(len(packages), 1)
        self.assertEqual(packages[0],
            {
                'repo': 'freebsd',
                'name': 'kiconvtool',
                'version': '0.97',
                'origversion': '0.97_1',
                'categories': ['sysutils'],
                'summary': 'Tool to preload kernel iconv charset tables',
                'maintainers': ['amdmi3@freebsd.org'],
                'www': ['http://wiki.freebsd.org/DmitryMarakasov/kiconvtool'],
            }
        )

    def test_api_v1_metapackages(self):
        self.request_and_check('/api/v1/metapackages/', has=['kiconvtool', '0.97'])

        self.request_and_check('/api/v1/metapackages/all/', has=['kiconvtool'])
        self.request_and_check('/api/v1/metapackages/all/k/', has=['kiconvtool'])
        self.request_and_check('/api/v1/metapackages/all/>k/', has=['kiconvtool'])
        self.request_and_check('/api/v1/metapackages/all/<l/', has=['kiconvtool'])
        self.request_and_check('/api/v1/metapackages/all/l/', hasnot=['kiconvtool'])
        self.request_and_check('/api/v1/metapackages/all/<kiconvtool/', hasnot=['kiconvtool'])
        self.request_and_check('/api/v1/metapackages/all/>kiconvtool/', hasnot=['kiconvtool'])

        self.request_and_check('/api/v1/metapackages/in-repo/freebsd/', has=['kiconvtool'], hasnot=['chromium-bsu', 'zlib'])

        self.request_and_check('/api/v1/metapackages/not-in-repo/freebsd/', has=['chromium-bsu', 'zlib'], hasnot=['kiconvtool'])

        self.request_and_check('/api/v1/metapackages/unique-in-repo/freebsd/', has=['kiconvtool'])

        self.request_and_check('/api/v1/metapackages/unique/', has=['kiconvtool'])

        self.request_and_check('/api/v1/metapackages/by-maintainer/amdmi3@freebsd.org/', has=['kiconvtool'])


if __name__ == '__main__':
    unittest.main()
