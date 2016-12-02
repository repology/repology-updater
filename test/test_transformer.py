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

from repology.transformer import PackageTransformer
from repology.package import Package

class TestPackageTransformer(unittest.TestCase):
    def test_ignore(self):
        p = Package(name="foo", version="1.0")
        self.assertEqual(p.ignore, False)
        PackageTransformer(rulestext='[ { ignore: true } ]').Process(p)
        self.assertEqual(p.ignore, True)

    def test_unignore(self):
        p = Package(name="foo", version="1.0")
        self.assertEqual(p.ignore, False)
        PackageTransformer(rulestext='[ { ignore: true }, { unignore: true } ]').Process(p)
        self.assertEqual(p.ignore, False)

    def test_ignorever(self):
        p = Package(name="foo", version="1.0")
        self.assertEqual(p.ignoreversion, False)
        PackageTransformer(rulestext='[ { ignorever: true } ]').Process(p)
        self.assertEqual(p.ignoreversion, True)

    def test_unignorever(self):
        p = Package(name="foo", version="1.0")
        self.assertEqual(p.ignoreversion, False)
        PackageTransformer(rulestext='[ { ignorever: true }, { unignorever: true } ]').Process(p)
        self.assertEqual(p.ignoreversion, False)

    def test_setname(self):
        p = Package(name="foo", version="1.0")
        PackageTransformer(rulestext='[ { setname: "bar" } ]').Process(p)
        self.assertEqual(p.name, "foo")
        self.assertEqual(p.effname, "bar")

    def test_setname_subst(self):
        p = Package(name="foo", version="1.0")
        PackageTransformer(rulestext='[ { setname: "bar_$0" } ]').Process(p)
        self.assertEqual(p.name, "foo")
        self.assertEqual(p.effname, "bar_foo")

if __name__ == '__main__':
    unittest.main()
