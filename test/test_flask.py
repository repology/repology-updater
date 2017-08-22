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

import json
import os
import sys
import unittest
import xml.etree.ElementTree


html_validation = True

try:
    from tidylib import tidy_document
    _, errors = tidy_document('<!DOCTYPE html><html><head><title>test</title></head><body><nav>test</nav></body></html>')
    if errors.find('<nav> is not recognized') != -1:
        raise RuntimeError('Tidylib does not support HTML5')
except ImportError:
    print('Unable to import tidylib, HTML validation is disabled', file=sys.stderr)
    html_validation = False
except RuntimeError:
    print('Tidylib HTML5 support check failed, HTML validation is disabled', file=sys.stderr)
    html_validation = False


repology_app = __import__('repology-app')


@unittest.skipIf('REPOLOGY_CONFIG' not in os.environ, 'flask tests require database filled with test data; please prepare the database and configuration file (see repology-test.conf.default for reference) and pass it via REPOLOGY_CONFIG environment variable')
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

    def checkurl_html(self, url, status_code=200, mimetype='text/html', has=[], hasnot=[]):
        document = self.checkurl(url=url, status_code=status_code, mimetype=mimetype, has=has, hasnot=hasnot)
        if not html_validation:
            return document

        errors = [error for error in tidy_document(document)[1].split('\n') if error and error.find('trimming empty <span>') == -1]
        for error in errors:
            print('HTML error in ' + url + ': ' + error, file=sys.stderr)
        self.assertTrue(not errors)

        return document

    def checkurl_json(self, url, status_code=200, mimetype='application/json', has=[], hasnot=[]):
        return json.loads(self.checkurl(url=url, status_code=status_code, mimetype=mimetype, has=has, hasnot=hasnot))

    def checkurl_svg(self, url, status_code=200, mimetype='image/svg+xml', has=[], hasnot=[]):
        return xml.etree.ElementTree.fromstring(self.checkurl(url=url, status_code=status_code, mimetype=mimetype, has=has, hasnot=hasnot))

    def checkurl_404(self, url):
        return self.checkurl(url=url, status_code=404, mimetype=None)

    def test_static_pages(self):
        self.checkurl_html('/news', has=['Added', 'repository'])  # assume we always have "Added xxx repository" news there
        self.checkurl_html('/about', has=['maintainers'])
        self.checkurl_html('/api', has=['/api/v1/metapackages/all/firefox'])

    def test_titlepage(self):
        self.checkurl('/', has=['FreeBSD', 'virtualbox'])

    def test_statistics(self):
        self.checkurl('/statistics', has=['FreeBSD'])

    def test_badges(self):
        self.checkurl_svg('/badge/vertical-allrepos/kiconvtool.svg', has=['<svg', 'FreeBSD'])
        self.checkurl_svg('/badge/vertical-allrepos/nonexistent.svg', has=['<svg', 'yet'])
        self.checkurl_404('/badge/vertical-allrepos/nonexistent')

        self.checkurl_svg('/badge/tiny-repos/kiconvtool.svg', has=['<svg', '>1<'])
        self.checkurl_svg('/badge/tiny-repos/nonexistent.svg', has=['<svg', '>0<'])
        self.checkurl_404('/badge/tiny-repos/nonexistent')

    def test_graphs(self):
        self.checkurl_svg('/graph/total/metapackages.svg')
        self.checkurl_svg('/graph/total/maintainers.svg')
        self.checkurl_svg('/graph/total/problems.svg')

        self.checkurl_svg('/graph/map_repo_size_fresh.svg')

    def test_metapackage(self):
        self.checkurl('/metapackage/kiconvtool', status_code=303)

        self.checkurl_html('/metapackage/kiconvtool/versions', has=['FreeBSD', '0.97', 'amdmi3'])
        self.checkurl_html('/metapackage/nonexistent/versions', has=['No data found'])

        self.checkurl_html('/metapackage/kiconvtool/packages', has=['FreeBSD', '0.97', 'amdmi3'])
        self.checkurl_html('/metapackage/nonexistent/packages', has=['No packages found'])

        self.checkurl_html('/metapackage/kiconvtool/information', has=['FreeBSD', '0.97', 'amdmi3'])
        self.checkurl_html('/metapackage/nonexistent/information', has=['No data found'])

        self.checkurl_html('/metapackage/kiconvtool/badges', has=[
            # XXX: agnostic to site home
            '/metapackage/kiconvtool',
            '/badge/vertical-allrepos/kiconvtool.svg',
            '/badge/tiny-repos/kiconvtool.svg',
        ])

    def test_maintaners(self):
        self.checkurl_html('/maintainers/a/', has=['amdmi3@freebsd.org'])

    def test_maintaner(self):
        self.checkurl_html('/maintainer/amdmi3@freebsd.org', has=['mailto:amdmi3@freebsd.org', 'kiconvtool'])

    def test_repositories(self):
        self.checkurl_html('/repositories/', has=['FreeBSD'])

    def test_metapackages(self):
        self.checkurl_html('/metapackages/', has=['kiconvtool', '0.97'])

        self.checkurl_html('/metapackages/all/', has=['kiconvtool', 'chromium-bsu'])
        self.checkurl_html('/metapackages/all/?search=iconv', has=['kiconvtool'], hasnot=['chromium-bsu'])
        self.checkurl_html('/metapackages/all/k/', has=['kiconvtool'], hasnot=['chromium-bsu'])
        self.checkurl_html('/metapackages/all/>k/', has=['kiconvtool'], hasnot=['chromium-bsu'])
        self.checkurl_html('/metapackages/all/<l/', has=['kiconvtool'])
        self.checkurl_html('/metapackages/all/l/', hasnot=['kiconvtool'])
        self.checkurl_html('/metapackages/all/<kiconvtool/', hasnot=['kiconvtool'])
        self.checkurl_html('/metapackages/all/>kiconvtool/', hasnot=['kiconvtool'])

        self.checkurl_html('/metapackages/in-repo/freebsd/', has=['kiconvtool'], hasnot=['chromium-bsu'])

        self.checkurl_html('/metapackages/not-in-repo/freebsd/', has=['chromium-bsu', 'zlib'], hasnot=['kiconvtool'])

        self.checkurl_html('/metapackages/unique-in-repo/freebsd/', has=['kiconvtool'])

        self.checkurl_html('/metapackages/unique/', has=['kiconvtool'])

        self.checkurl_html('/metapackages/by-maintainer/amdmi3@freebsd.org/', has=['kiconvtool'], hasnot=['chromium-bsu'])

        # special cases: check fallback code for going before first or after last entry
        self.checkurl_html('/metapackages/all/<0/', has=['kiconvtool'])
        self.checkurl_html('/metapackages/all/>zzzzzz/', has=['kiconvtool'])

    def test_api_v1_metapackage(self):
        self.assertEqual(
            self.checkurl_json('/api/v1/metapackage/kiconvtool', mimetype='application/json'),
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

        self.checkurl_json('/api/v1/metapackages/all/', has=['kiconvtool', 'chromium-bsu'])
        self.checkurl_json('/api/v1/metapackages/all/k/', has=['kiconvtool'], hasnot=['chromium-bsu'])
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

    def test_api_v1_problems(self):
        # XXX: empty output for now
        self.checkurl_json('/api/v1/maintainer/amdmi3@freebsd.org/problems')
        self.checkurl_json('/api/v1/repository/freebsd/problems')


if __name__ == '__main__':
    unittest.main()
