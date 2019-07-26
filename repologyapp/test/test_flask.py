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

# mypy: no-disallow-untyped-calls

import json
import os
import sys
import unittest
import xml.etree.ElementTree
from typing import Any, List, Optional

from repologyapp import app


TIDY_OPTIONS = {'drop-empty-elements': False}


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


@unittest.skipIf('REPOLOGY_CONFIG' not in os.environ, 'flask tests require database filled with test data; please prepare the database and configuration file (see repology-test.conf.default for reference) and pass it via REPOLOGY_CONFIG environment variable')
class TestFlask(unittest.TestCase):
    def setUp(self) -> None:
        self.app = app.test_client()

    def checkurl(self, url: str, status_code: Optional[int] = 200, mimetype: Optional[str] = 'text/html', has: List[str] = [], hasnot: List[str] = []) -> str:
        reply = self.app.get(url)
        if status_code is not None:
            self.assertEqual(reply.status_code, status_code)
        if mimetype is not None:
            self.assertEqual(reply.mimetype, mimetype)
        text = reply.data.decode('utf-8')
        assert(isinstance(text, str))
        for pattern in has:
            self.assertTrue(pattern in text)
        for pattern in hasnot:
            self.assertFalse(pattern in text)
        return text

    def checkurl_html(self, url: str, status_code: Optional[int] = 200, mimetype: Optional[str] = 'text/html', has: List[str] = [], hasnot: List[str] = []) -> str:
        document = self.checkurl(url=url, status_code=status_code, mimetype=mimetype, has=has, hasnot=hasnot)
        if not html_validation:
            return document

        errors = [error for error in tidy_document(document, options=TIDY_OPTIONS)[1].split('\n') if error and error.find('trimming empty <span>') == -1]
        for error in errors:
            print('HTML error in ' + url + ': ' + error, file=sys.stderr)
        self.assertTrue(not errors)

        return document

    def checkurl_json(self, url: str, status_code: Optional[int] = 200, mimetype: Optional[str] = 'application/json', has: List[str] = [], hasnot: List[str] = []) -> Any:
        return json.loads(self.checkurl(url=url, status_code=status_code, mimetype=mimetype, has=has, hasnot=hasnot))

    def checkurl_svg(self, url: str, status_code: Optional[int] = 200, mimetype: Optional[str] = 'image/svg+xml', has: List[str] = [], hasnot: List[str] = []) -> xml.etree.ElementTree.Element:
        return xml.etree.ElementTree.fromstring(self.checkurl(url=url, status_code=status_code, mimetype=mimetype, has=has, hasnot=hasnot))

    def checkurl_404(self, url: str) -> str:
        return self.checkurl(url=url, status_code=404, mimetype=None)

    def test_static_pages(self) -> None:
        self.checkurl_html('/news', has=['Added', 'repository'])  # assume we always have "Added xxx repository" news there
        self.checkurl_html('/about', has=['maintainers'])
        self.checkurl_html('/api', has=['/api/v1/projects/firefox'])

    def test_titlepage(self) -> None:
        self.checkurl('/', has=['FreeBSD', 'virtualbox'])

    def test_badges(self) -> None:
        self.checkurl_svg('/badge/vertical-allrepos/kiconvtool.svg', has=['<svg', 'FreeBSD'])
        self.checkurl_svg('/badge/vertical-allrepos/kiconvtool.svg?header=FooBar', has=['<svg', 'FreeBSD', 'FooBar'])
        self.checkurl_svg('/badge/vertical-allrepos/kiconvtool.svg?minversion=99999999', has=['<svg', 'FreeBSD', 'e00000'])
        self.checkurl_svg('/badge/vertical-allrepos/nonexistent.svg', has=['<svg', 'No known packages'])

        self.checkurl_svg('/badge/tiny-repos/kiconvtool.svg', has=['<svg', '>1<'])
        self.checkurl_svg('/badge/tiny-repos/nonexistent.svg', has=['<svg', '>0<'])

        self.checkurl_svg('/badge/version-for-repo/freebsd/kiconvtool.svg', has=['<svg', '>0.97<'])
        self.checkurl_svg('/badge/version-for-repo/freebsd/kiconvtool.svg?minversion=99999999', has=['<svg', '>0.97<', 'e00000'])
        self.checkurl_svg('/badge/version-for-repo/freebsd/nonexistent.svg', has=['<svg', '>No package<'])
        self.checkurl_404('/badge/version-for-repo/nonexistent/kiconvtool.svg')

        self.checkurl_svg('/badge/version-only-for-repo/freebsd/kiconvtool.svg', has=['<svg', '>0.97<'])
        self.checkurl_svg('/badge/version-only-for-repo/freebsd/kiconvtool.svg?minversion=99999999', has=['<svg', '>0.97<', 'e00000'])
        self.checkurl_svg('/badge/version-only-for-repo/freebsd/nonexistent.svg', has=['<svg', '>-<'])
        self.checkurl_404('/badge/version-only-for-repo/nonexistent/kiconvtool.svg')

        self.checkurl_svg('/badge/latest-versions/kiconvtool.svg', has=['<svg', '>0.97<'])
        self.checkurl_svg('/badge/latest-versions/nonexistent.svg', has=['<svg', '>-<'])

    def test_graphs(self) -> None:
        self.checkurl_svg('/graph/total/projects.svg')
        self.checkurl_svg('/graph/total/maintainers.svg')
        self.checkurl_svg('/graph/total/problems.svg')

        self.checkurl_svg('/graph/map_repo_size_fresh.svg')

        self.checkurl_svg('/graph/repo/freebsd/projects_total.svg')
        self.checkurl_svg('/graph/repo/freebsd/projects_newest.svg')
        self.checkurl_svg('/graph/repo/freebsd/projects_newest_percent.svg')
        self.checkurl_svg('/graph/repo/freebsd/projects_outdated.svg')
        self.checkurl_svg('/graph/repo/freebsd/projects_outdated_percent.svg')
        self.checkurl_svg('/graph/repo/freebsd/projects_unique.svg')
        self.checkurl_svg('/graph/repo/freebsd/projects_unique_percent.svg')
        self.checkurl_svg('/graph/repo/freebsd/projects_problematic.svg')
        self.checkurl_svg('/graph/repo/freebsd/projects_problematic_percent.svg')
        self.checkurl_svg('/graph/repo/freebsd/maintainers.svg')
        self.checkurl_svg('/graph/repo/freebsd/problems.svg')

    def test_project(self) -> None:
        self.checkurl_html('/project/kiconvtool/versions', has=['FreeBSD', '0.97', 'amdmi3'])
        self.checkurl_html('/project/nonexistent/versions', has=['Unknown project'], status_code=404)

        self.checkurl_html('/project/kiconvtool/packages', has=['FreeBSD', '0.97', 'amdmi3'])
        self.checkurl_html('/project/nonexistent/packages', has=['Unknown project'], status_code=404)

        self.checkurl_html('/project/kiconvtool/information', has=['FreeBSD', '0.97', 'amdmi3'])
        self.checkurl_html('/project/nonexistent/information', has=['Unknown project'], status_code=404)

        self.checkurl_html('/project/kiconvtool/related')  # , has=['0.97']) # XXX: no related packages in current testdata
        self.checkurl_html('/project/nonexistent/related', has=['Unknown project'], status_code=404)

        self.checkurl_html('/project/kiconvtool/badges', has=[
            # XXX: agnostic to site home
            '/project/kiconvtool',
            '/badge/vertical-allrepos/kiconvtool.svg',
            '/badge/tiny-repos/kiconvtool.svg',
        ])

        self.checkurl_html('/project/kiconvtool/report', has=[''])

    def test_maintaners(self) -> None:
        self.checkurl_html('/maintainers/a/', has=['amdmi3@freebsd.org'])
        self.checkurl_html('/maintainers/?search=%20AMDmi3%20', has=['amdmi3@freebsd.org'])

    def test_maintaner(self) -> None:
        self.checkurl_html('/maintainer/amdmi3@freebsd.org', has=['mailto:amdmi3@freebsd.org', 'kiconvtool'])
        self.checkurl_html('/maintainer/nonexistent', 404, has=['noindex'])

    def test_maintaner_problems(self) -> None:
        self.checkurl_html('/maintainer/amdmi3@freebsd.org/problems')

    def test_repositories(self) -> None:
        self.checkurl_html('/repositories/statistics', has=['FreeBSD'])
        self.checkurl_html('/repositories/statistics/newest', has=['FreeBSD'])
        self.checkurl_html('/repositories/packages', has=['FreeBSD'])
        self.checkurl_html('/repositories/graphs')
        self.checkurl_html('/repositories/updates', has=['FreeBSD'])

    def test_log(self) -> None:
        self.checkurl_html('/log/1', has=['successful'])

    def test_link(self) -> None:
        self.checkurl_html('/link/http://chromium-bsu.sourceforge.net/', has=['chromium-bsu.sourceforge.net'])

    def test_repository(self) -> None:
        self.checkurl_html('/repository/freebsd', has=['FreeBSD'])

    def test_repository_problems(self) -> None:
        self.checkurl_html('/repository/freebsd/problems', has=['FreeBSD'])

    def test_projects(self) -> None:
        self.checkurl_html('/projects/', has=['kiconvtool', '0.97', 'chromium-bsu', '0.9.15.1'])

        self.checkurl_html('/projects/k/', has=['kiconvtool', 'virtualbox'], hasnot=['chromium-bsu'])
        self.checkurl_html('/projects/..l/', has=['kiconvtool', 'chromium-bsu'], hasnot=['virtualbox'])

        self.checkurl_html('/projects/?search=iconv', has=['kiconvtool'], hasnot=['chromium-bsu'])
        self.checkurl_html('/projects/?search=%20ICONV%20', has=['kiconvtool'], hasnot=['chromium-bsu'])
        self.checkurl_html('/projects/?category=games-action', has=['chromium-bsu'], hasnot=['kiconvtool'])
        self.checkurl_html('/projects/?inrepo=freebsd', has=['kiconvtool'], hasnot=['oracle-xe'])
        self.checkurl_html('/projects/?notinrepo=freebsd', has=['oracle-xe'], hasnot=['kiconvtool'])
        self.checkurl_html('/projects/?maintainer=amdmi3@freebsd.org', has=['kiconvtool'], hasnot=['kforth', 'teamviewer'])

        # XXX add some duplicated packages in testdata and add spread and unique tests

        # special cases: check fallback code for going before first or after last entry
        self.checkurl_html('/projects/..0/', has=['kiconvtool'])
        self.checkurl_html('/projects/zzzzzz/', has=['kiconvtool'])

    def test_api_v1_project(self) -> None:
        self.assertEqual(
            self.checkurl_json('/api/v1/project/kiconvtool', mimetype='application/json'),
            [
                {
                    'repo': 'freebsd',
                    'name': 'kiconvtool',
                    'version': '0.97',
                    'origversion': '0.97_1',
                    'status': 'unique',
                    'categories': ['sysutils'],
                    'summary': 'Tool to preload kernel iconv charset tables',
                    'maintainers': ['amdmi3@freebsd.org'],
                    'www': ['http://wiki.freebsd.org/DmitryMarakasov/kiconvtool'],
                }
            ]
        )
        self.assertEqual(self.checkurl_json('/api/v1/project/nonexistent', mimetype='application/json'), [])

    def test_api_v1_projects(self) -> None:
        self.checkurl_json('/api/v1/projects/', has=['kiconvtool', '0.97', 'chromium-bsu', '0.9.15.1'])

        self.checkurl_json('/api/v1/projects/k/', has=['kiconvtool', 'virtualbox'], hasnot=['chromium-bsu'])
        self.checkurl_json('/api/v1/projects/..l/', has=['kiconvtool', 'chromium-bsu'], hasnot=['virtualbox'])

        self.checkurl_json('/api/v1/projects/?search=iconv', has=['kiconvtool'], hasnot=['chromium-bsu'])
        self.checkurl_json('/api/v1/projects/?category=games-action', has=['chromium-bsu'], hasnot=['kiconvtool'])
        self.checkurl_json('/api/v1/projects/?inrepo=freebsd', has=['kiconvtool'], hasnot=['oracle-xe'])
        self.checkurl_json('/api/v1/projects/?notinrepo=freebsd', has=['oracle-xe'], hasnot=['kiconvtool'])
        self.checkurl_json('/api/v1/projects/?maintainer=amdmi3@freebsd.org', has=['kiconvtool'], hasnot=['kforth', 'teamviewer'])

    def test_api_v1_problems(self) -> None:
        # XXX: empty output for now
        self.checkurl_json('/api/v1/maintainer/amdmi3@freebsd.org/problems')
        self.checkurl_json('/api/v1/repository/freebsd/problems')


if __name__ == '__main__':
    unittest.main()
