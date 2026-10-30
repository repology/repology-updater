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
from repology.parsers.parsers.bcr import BazelCentralRegistryParser, _normalize_release_version


@pytest.mark.parametrize('version,expected', [
    ('1.3.1', '1.3.1'),
    ('v2.0.0', '2.0.0'),
    ('1.3.1.bcr.5', '1.3.1'),
    ('3.4.0.bcr.1.1', '3.4.0'),
    ('5.3.0-bcr.3', '5.3.0'),
    ('2.10.1.bcr1', '2.10.1'),
    ('1.16.0.bcr.beta.3', '1.16.0'),
    ('5.3.0-bcr.alpha.5', '5.3.0'),
    ('0.0.0-20250408-yosyshq.bcr.1', '0.0.0-20250408-yosyshq'),
    ('0.10.0-bcr.20240313-1142dc4.bcr.2', '0.10.0-bcr.20240313-1142dc4'),
    ('3.8.2.bcr.11', '3.8.2'),
    # pseudo-versions are left for the snapshot rules
    ('1.1.1-0.20211014115138-25647e692c79', '1.1.1-0.20211014115138-25647e692c79'),
    ('0.12.1-20260505-108f93c', '0.12.1-20260505-108f93c'),
])
def test_normalize_release_version(version: str, expected: str) -> None:
    assert _normalize_release_version(version) == expected


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
    snapshot = tmp_path / 'modules' / 'bar'
    _write_json(snapshot / 'metadata.json', {
        'versions': [
            '1.0.0', '1.0.0.bcr.20241007', '1.1.1-0.20211014115138-25647e692c79', 'v2.0.0.bcr.1',
        ],
    })
    _write_json(snapshot / '1.0.0' / 'source.json', {
        'url': 'https://github.com/example/bar/archive/refs/tags/v1.0.0.tar.gz',
        'strip_prefix': 'bar-1.0.0',
    })
    _write_json(snapshot / '1.0.0.bcr.20241007' / 'source.json', {
        'url': 'https://github.com/example/bar/archive/858451e5b7d1c56cf8f6d58f88cf958351837e53.tar.gz',
        'strip_prefix': 'bar-858451e5b7d1c56cf8f6d58f88cf958351837e53',
    })
    _write_json(snapshot / '1.1.1-0.20211014115138-25647e692c79' / 'source.json', {
        'url': 'https://github.com/example/bar/archive/25647e6.tar.gz',
        'strip_prefix': 'bar-25647e692c7906b96ffd2b05ca54c097948e879c',
    })
    _write_json(snapshot / 'v2.0.0.bcr.1' / 'source.json', {
        'type': 'git_repository',
        'remote': 'https://github.com/example/bar.git',
        'commit': '1cc19a21a0c06b4e3e7a1bd8a3f4f59f69cbd9b1',
    })
    # a directory without metadata.json is not a module
    (tmp_path / 'modules' / 'stray').mkdir()
    return tmp_path


def test_every_version_is_emitted(registry: Path) -> None:
    packages = _parse(registry)
    assert sorted(packages) == ['1.0.0', '1.1.0', '1.1.0.bcr.1', '1.2.0', '1.3.0']
    assert {package.projectname_seed for package in packages.values()} == {'foo'}


def test_bcr_snapshot(registry: Path) -> None:
    packages = _parse(registry, 'bar')
    # release archive
    assert not packages['1.0.0'].flags & PackageFlags.IGNORE
    # full commit hash in the archive url
    assert packages['1.0.0.bcr.20241007'].flags & PackageFlags.IGNORE
    # short hash in the url, full hash in strip_prefix
    assert packages['1.1.1-0.20211014115138-25647e692c79'].flags & PackageFlags.IGNORE
    # git_repository pinned to a commit
    assert packages['v2.0.0.bcr.1'].flags & PackageFlags.IGNORE
    # a snapshot keeps its module version, a release is normalized
    assert packages['1.0.0.bcr.20241007'].version == '1.0.0.bcr.20241007'
    assert packages['v2.0.0.bcr.1'].version == 'v2.0.0.bcr.1'
    assert packages['1.0.0'].version == '1.0.0'
    # release archives of other modules
    assert not any(package.flags & PackageFlags.IGNORE for package in _parse(registry).values())


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
