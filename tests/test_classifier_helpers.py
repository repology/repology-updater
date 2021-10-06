# Copyright (C) 2017-2021 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from repology.classifier import _is_packageset_unique
from repology.package import Package

from .package import spawn_package


def test_is_packageset_unique() -> None:
    packages: list[Package] = []
    assert _is_packageset_unique(packages)

    packages = [spawn_package(family='foo')]
    assert _is_packageset_unique(packages)

    packages = [spawn_package(family='foo'), spawn_package(family='foo')]
    assert _is_packageset_unique(packages)

    packages = [spawn_package(family='foo'), spawn_package(family='bar')]
    assert not _is_packageset_unique(packages)
