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
import xml.etree.ElementTree

repology_app = __import__("repology-app")


@unittest.skipIf(not 'REPOLOGY_CONFIG' in os.environ, 'flask tests require database filled with test data; please prepare the database and configuration file (see repology-test.conf.default for reference) and pass it via REPOLOGY_CONFIG environment variable')
class TestFlask(unittest.TestCase):
    def setUp(self):
        self.app = repology_app.app.test_client()

    def checkurl(self, url, status_code=200, mimetype='text/html', has=[], hasnot=[]):
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

    def checkurl_json(self, url, status_code=200, mimetype='application/json', has=[], hasnot=[]):
        return json.loads(self.checkurl(url=url, status_code=status_code, mimetype=mimetype, has=has, hasnot=hasnot))

    def checkurl_svg(self, url, status_code=200, mimetype='image/svg+xml', has=[], hasnot=[]):
        return xml.etree.ElementTree.fromstring(self.checkurl(url=url, status_code=status_code, mimetype=mimetype, has=has, hasnot=hasnot))

    def checkurl_404(self, url):
        return self.checkurl(url=url, status_code=404, mimetype=None)

    def test_static_pages(self):
        self.checkurl('/news', has=['support added']);
        self.checkurl('/about', has=['maintainers']);
        self.checkurl('/api', has=['/api/v1/metapackages/all/firefox']);
        self.checkurl('/badges', has=['http://repology.org/badge/vertical-allrepos/METAPACKAGE', 'http://repology.org/badge/tiny-packages/METAPACKAGE']);

    def test_statistics(self):
        self.checkurl('/statistics', has=['FreeBSD']);

    def test_badges(self):
        self.checkurl_svg('/badge/vertical-allrepos/kiconvtool.svg', has=['<svg', 'FreeBSD'])
        self.checkurl_svg('/badge/vertical-allrepos/nonexistent.svg', has=['<svg', 'yet'])
        self.checkurl_404('/badge/vertical-allrepos/nonexistent')
        self.checkurl_svg('/badge/tiny-packages/kiconvtool.svg', has=['<svg', '>1<'])
        self.checkurl_svg('/badge/tiny-packages/nonexistent.svg', has=['<svg', '>0<'])
        self.checkurl_404('/badge/tiny-packages/nonexistent')

    def test_metapackage(self):
        self.checkurl('/metapackage/kiconvtool', has=['FreeBSD', '0.97', 'amdmi3'])
        self.checkurl('/metapackage/nonexistent', has=['No packages found'])

    def test_maintaners(self):
        self.checkurl('/maintainers/a/', has=['amdmi3@freebsd.org'])

    def test_repositories(self):
        self.checkurl('/repositories/', has=['FreeBSD'])

    def test_metapackages(self):
        self.checkurl('/metapackages/', has=['kiconvtool', '0.97'])

        self.checkurl('/metapackages/all/', has=['kiconvtool'])
        self.checkurl('/metapackages/all/k/', has=['kiconvtool'])
        self.checkurl('/metapackages/all/>k/', has=['kiconvtool'])
        self.checkurl('/metapackages/all/<l/', has=['kiconvtool'])
        self.checkurl('/metapackages/all/l/', hasnot=['kiconvtool'])
        self.checkurl('/metapackages/all/<kiconvtool/', hasnot=['kiconvtool'])
        self.checkurl('/metapackages/all/>kiconvtool/', hasnot=['kiconvtool'])

        self.checkurl('/metapackages/in-repo/freebsd/', has=['kiconvtool'])

        self.checkurl('/metapackages/not-in-repo/freebsd/', has=['chromium-bsu', 'zlib'], hasnot=['kiconvtool'])

        self.checkurl('/metapackages/unique-in-repo/freebsd/', has=['kiconvtool'])

        self.checkurl('/metapackages/unique/', has=['kiconvtool'])

        self.checkurl('/metapackages/by-maintainer/amdmi3@freebsd.org/', has=['kiconvtool'])

        # special cases: check fallback code for going before first or after last entry
        self.checkurl('/metapackages/all/<0/', has=['kiconvtool'])
        self.checkurl('/metapackages/all/>zzzzzz/', has=['kiconvtool'])

    def test_api_v1_metapackage(self):
        self.assertEqual(self.checkurl_json('/api/v1/metapackage/kiconvtool', mimetype='application/json'),
            [
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
            ]
        )
        self.assertEqual(self.checkurl_json('/api/v1/metapackage/nonexistent', mimetype='application/json'), [])

    def test_api_v1_metapackages(self):
        self.checkurl_json('/api/v1/metapackages/', has=['kiconvtool', '0.97'])

        self.checkurl_json('/api/v1/metapackages/all/', has=['kiconvtool'])
        self.checkurl_json('/api/v1/metapackages/all/k/', has=['kiconvtool'])
        self.checkurl_json('/api/v1/metapackages/all/>k/', has=['kiconvtool'])
        self.checkurl_json('/api/v1/metapackages/all/<l/', has=['kiconvtool'])
        self.checkurl_json('/api/v1/metapackages/all/l/', hasnot=['kiconvtool'])
        self.checkurl_json('/api/v1/metapackages/all/<kiconvtool/', hasnot=['kiconvtool'])
        self.checkurl_json('/api/v1/metapackages/all/>kiconvtool/', hasnot=['kiconvtool'])

        self.checkurl_json('/api/v1/metapackages/in-repo/freebsd/', has=['kiconvtool'], hasnot=['chromium-bsu', 'zlib'])

        self.checkurl_json('/api/v1/metapackages/not-in-repo/freebsd/', has=['chromium-bsu', 'zlib'], hasnot=['kiconvtool'])

        self.checkurl_json('/api/v1/metapackages/unique-in-repo/freebsd/', has=['kiconvtool'])

        self.checkurl_json('/api/v1/metapackages/unique/', has=['kiconvtool'])

        self.checkurl_json('/api/v1/metapackages/by-maintainer/amdmi3@freebsd.org/', has=['kiconvtool'])


if __name__ == '__main__':
    unittest.main()
