# Copyright (C) 2026 Gustavo Nunes Goretkin <gustavo.goretkin@gmail.com>
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
from pathlib import Path
from typing import Any

import pytest

from repology.package import LinkType, Package, PackageFlags
from repology.packagemaker import PackageFactory
from repology.parsers.parsers.bcr import BazelCentralRegistryParser, _normalize_version


@pytest.mark.parametrize('version,expected', [
    ('1.3.1', '1.3.1'),
    ('1.3.1.bcr.5', '1.3.1'),
    ('3.4.0.bcr.1.1', '3.4.0'),
    ('0.10.0-bcr.20240313-1142dc4.bcr.2', '0.10.0-bcr.20240313-1142dc4'),
    # other spellings are left for the rules
    ('v2.0.0', 'v2.0.0'),
    ('5.3.0-bcr.3', '5.3.0-bcr.3'),
    ('2.10.1.bcr1', '2.10.1.bcr1'),
])
def test_normalize_version(version: str, expected: str) -> None:
    assert _normalize_version(version) == expected


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def _parse(registry: Path, module: str = 'foo') -> dict[str, Package]:
    parser = BazelCentralRegistryParser()
    factory = PackageFactory()
    packages = (
        maker.spawn(repo='bcr', family='bcr')
        for maker in parser.iter_parse(str(registry), factory)
    )
    return {package.rawversion: package for package in packages if package.projectname_seed == module}


@pytest.fixture
def registry(tmp_path: Path) -> Path:
    module = tmp_path / 'modules' / 'foo'
    _write_json(module / 'metadata.json', {
        'homepage': 'https://example.com/foo',
        'repository': ['github:example/foo'],
        'maintainers': [{'email': 'maintainer@example.com'}],
        'versions': ['1.0.0', '1.1.0', '1.1.0.bcr.1', '1.2.0', '1.3.0'],
        'yanked_versions': {
            '1.0.0': 'CVE-2020-0001 (https://example.com/advisory)',
            '1.1.0': 'Incorrect release artifacts',
            '1.2.0': 'Broken build',
        },
    })
    _write_json(module / '1.1.0.bcr.1' / 'source.json', {
        'url': 'https://example.com/foo-1.1.0.tar.gz',
        'patches': {'b.patch': 'sha256-b', 'a.patch': 'sha256-a'},
    })
    _write_json(module / '1.3.0' / 'source.json', {
        'url': 'https://example.com/foo-1.3.0.tar.gz',
    })
    # a directory without metadata.json is not a module
    (tmp_path / 'modules' / 'stray').mkdir()
    return tmp_path


def test_every_version_is_emitted(registry: Path) -> None:
    packages = _parse(registry)
    assert sorted(packages) == ['1.0.0', '1.1.0', '1.1.0.bcr.1', '1.2.0', '1.3.0']
    assert {package.projectname_seed for package in packages.values()} == {'foo'}


def test_revision_shares_normalized_version(registry: Path) -> None:
    package = _parse(registry)['1.1.0.bcr.1']
    assert package.version == '1.1.0'
    assert package.extrafields is not None
    assert package.rawversion == '1.1.0.bcr.1'
    assert package.extrafields['patch'] == ['a.patch', 'b.patch']


def test_yank_flags(registry: Path) -> None:
    packages = _parse(registry)
    # yanked for a CVE
    assert packages['1.0.0'].flags & PackageFlags.VULNERABLE
    assert not packages['1.0.0'].flags & PackageFlags.RECALLED
    # yanked, but a live revision of the same version exists
    assert not packages['1.1.0'].flags & (PackageFlags.VULNERABLE | PackageFlags.RECALLED)
    # yanked with no live revision
    assert packages['1.2.0'].flags & PackageFlags.RECALLED
    # not yanked
    assert not packages['1.3.0'].flags & (PackageFlags.VULNERABLE | PackageFlags.RECALLED)


def test_links(registry: Path) -> None:
    package = _parse(registry)['1.3.0']
    assert package.links is not None
    links = {(link[0], link[1]) for link in package.links}
    assert (LinkType.UPSTREAM_HOMEPAGE, 'https://example.com/foo') in links
    assert (LinkType.UPSTREAM_DOWNLOAD, 'https://example.com/foo-1.3.0.tar.gz') in links
    assert not any(link_type == LinkType.UPSTREAM_REPOSITORY for link_type, _ in links)
    assert package.maintainers == ['maintainer@example.com']
