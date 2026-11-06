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
import os
import re
from dataclasses import dataclass
from typing import Any, Iterable, cast

from repology.package import LinkType, PackageFlags
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers


_CVE_RE = re.compile(r'CVE-[0-9]{4}-[0-9]+')

# A source pinned to an upstream commit, by a full commit hash in the
# archive url or strip_prefix or by the commit of a git_repository,
# builds the module version from that commit instead of a release. Such
# a snapshot keeps its module version unchanged.
_BCR_SNAPSHOT_RE = re.compile(r'(?<![0-9A-Za-z])[0-9a-f]{40}(?![0-9A-Za-z])')


# A .bcr.N suffix marks a revision of a module version, published when
# the entry needs a different source archive, patches or MODULE.bazel
# (https://github.com/bazelbuild/bazel-central-registry/blob/main/docs/README.md#add-only).
# The part before it is the upstream version number the revision is
# published under. Not every module follows the convention; some spell
# the revision -bcr.N, .bcrN, .bcr.N.N, .bcr.alpha.N or .bcr.beta.N.
_BCR_REVISION_RE = re.compile(r'[.-]bcr(?:\.(?:alpha|beta))?\.?[0-9]+(?:\.[0-9]+)?$')


def _strip_bcr_revision(version: str) -> str:
    return _BCR_REVISION_RE.sub('', version)


def _normalize_release_version(version: str) -> str:
    version = _strip_bcr_revision(version)
    # modules versioned from the upstream tag verbatim
    version = re.sub(r'^v([0-9])', r'\1', version)
    return version


def _read_json(path: str) -> dict[str, Any]:
    with open(path) as fd:
        return cast(dict[str, Any], json.load(fd))


@dataclass
class _ModuleVersion:
    version: str
    source: dict[str, Any] | None
    yank_reason: str | None

    @staticmethod
    def load(moduledir: str, version: str, yanked: dict[str, str]) -> '_ModuleVersion':
        sourcepath = os.path.join(moduledir, version, 'source.json')
        return _ModuleVersion(
            version=version,
            source=_read_json(sourcepath) if os.path.exists(sourcepath) else None,
            yank_reason=(yanked[version] or '') if version in yanked else None,
        )

    def is_snapshot(self) -> bool:
        if self.source is None:
            return False
        if self.source.get('commit'):
            return True
        return any(_BCR_SNAPSHOT_RE.search(self.source.get(key) or '') for key in ('url', 'strip_prefix'))

    # For a release, the module version without its .bcr.N revision or
    # leading v, which is the upstream release version as the module
    # spells it. A snapshot keeps its whole module version, .bcr. parts
    # included. It sorts above the release it is based on, where its
    # IGNORE flag keeps it from counting as the newest version.
    def normalized_version(self) -> str:
        if self.is_snapshot():
            return self.version
        return _normalize_release_version(self.version)


class BazelCentralRegistryParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        modulesdir = os.path.join(path, 'modules')

        for modulename in os.listdir(modulesdir):
            moduledir = os.path.join(modulesdir, modulename)
            metadatapath = os.path.join(moduledir, 'metadata.json')
            if not os.path.exists(metadatapath):
                continue

            with factory.begin(modulename) as pkg:
                metadata = _read_json(metadatapath)

                pkg.add_name(modulename, NameType.BCR_MODULE_NAME)
                pkg.add_links(LinkType.UPSTREAM_HOMEPAGE, metadata.get('homepage'))

                for maintainer in metadata.get('maintainers', []):
                    if email := maintainer.get('email'):
                        pkg.add_maintainers(extract_maintainers(email))

                yanked = metadata.get('yanked_versions') or {}
                module_versions = [
                    _ModuleVersion.load(moduledir, version, yanked)
                    for version in dict.fromkeys(metadata.get('versions', []))
                ]

                # Every module version is emitted, .bcr.N revisions included.
                # Revisions of a release share its normalized version and
                # compare equal, but each pins its own archive and patches, so
                # their sources can differ. A normalized version all of whose
                # module versions are yanked is recalled; a version yanked for
                # a CVE is vulnerable.
                live_versions = {mv.normalized_version() for mv in module_versions if mv.yank_reason is None}

                for mv in module_versions:
                    verpkg = pkg.clone(append_ident=':' + mv.version)
                    verpkg.set_version(mv.normalized_version())
                    verpkg.set_rawversion(mv.version)

                    if mv.yank_reason is not None:
                        if _CVE_RE.search(mv.yank_reason):
                            verpkg.set_flags(PackageFlags.VULNERABLE)
                        elif mv.normalized_version() not in live_versions:
                            verpkg.set_flags(PackageFlags.RECALLED)

                    if mv.source is not None:
                        verpkg.add_links(LinkType.UPSTREAM_DOWNLOAD, mv.source.get('url'))
                        if mv.is_snapshot():
                            verpkg.set_flags(PackageFlags.IGNORE)  # not an upstream release
                        if patches := mv.source.get('patches'):
                            verpkg.set_extra_field('patch', sorted(patches))

                    yield verpkg
