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

import unittest

from repology.template_helpers import maintainer_to_links, maintainers_to_group_mailto


class TestMaintainerLinks(unittest.TestCase):
    def test_email(self):
        self.assertEqual(maintainer_to_links('amdmi3@freebsd.org'), ['mailto:amdmi3@freebsd.org'])

    def test_garbage(self):
        self.assertEqual(maintainer_to_links('foo'), [])

    def test_cpan(self):
        self.assertEqual(maintainer_to_links('foo@cpan'), ['http://search.cpan.org/~foo'])

    def test_aur(self):
        self.assertEqual(maintainer_to_links('foo@aur'), ['https://aur.archlinux.org/account/foo'])

    def test_alt(self):
        self.assertEqual(maintainer_to_links('foo@altlinux.org'), ['http://sisyphus.ru/en/packager/foo/', 'mailto:foo@altlinux.org'])
        self.assertEqual(maintainer_to_links('foo@altlinux.ru'), ['http://sisyphus.ru/en/packager/foo/', 'mailto:foo@altlinux.ru'])

    def test_group(self):
        self.assertEqual(maintainers_to_group_mailto(['some@notemail', 'amdmi3@freebsd.org', 'amdmi3@amdmi3.ru']), 'mailto:amdmi3@amdmi3.ru,amdmi3@freebsd.org')
        self.assertEqual(maintainers_to_group_mailto(['some@notemail', 'amdmi3@freebsd.org', 'amdmi3@amdmi3.ru'], 'Hello, world!'), 'mailto:amdmi3@amdmi3.ru,amdmi3@freebsd.org?subject=Hello, world!')
        self.assertEqual(maintainers_to_group_mailto(['some@notemail'], 'Hello, world!'), None)
        self.assertEqual(maintainers_to_group_mailto(['some@notemail']), None)


if __name__ == '__main__':
    unittest.main()
