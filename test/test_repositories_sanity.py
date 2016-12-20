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

from repology.repositories import REPOSITORIES

class TestVersionComparison(unittest.TestCase):
    # all these fields should be present in repository data
    def test_have_all_fields(self):
        for repository in REPOSITORIES:
            for field in ('name', 'desc', 'family', 'fetcher', 'parser', 'tags'):
                self.assertEqual(field in repository, True)

    def test_names(self):
        tags = set()
        for repository in REPOSITORIES:
            for tag in repository['tags']:
                tags.add(tag)

        names = set()
        for repository in REPOSITORIES:
            self.assertEqual(repository['name'] in names, False)
            self.assertEqual(repository['name'] in tags, False)
            names.add(repository['name'])

    def test_descs(self):
        # descs should be unique
        descs = set()
        for repository in REPOSITORIES:
            self.assertEqual(repository['desc'] in descs, False)
            descs.add(repository['desc'])


if __name__ == '__main__':
    unittest.main()
