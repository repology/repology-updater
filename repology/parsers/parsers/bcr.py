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
from typing import Any, Iterable, cast

from repology.package import LinkType, PackageFlags
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.maintainers import extract_maintainers
from repology.parsers.versions import VersionStripper


_CVE_RE = re.compile(r'CVE-[0-9]{4}-[0-9]+')

# A .bcr.N suffix marks a revision of a module version, published when
# the entry needs a different source archive, patches or MODULE.bazel
# (https://github.com/bazelbuild/bazel-central-registry/blob/main/docs/README.md#add-only).
_normalize_version = VersionStripper().strip_right('.bcr.')


def _read_json(path: str) -> dict[str, Any]:
    with open(path) as fd:
        return cast(dict[str, Any], json.load(fd))


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
                versions = list(dict.fromkeys(metadata.get('versions', [])))

                # Every module version is emitted, .bcr.N revisions included.
                # Revisions of a release share its normalized version and
                # compare equal, but each pins its own archive and patches, so
                # their sources can differ. A normalized version all of whose
                # module versions are yanked is recalled; a version yanked for
                # a CVE is vulnerable.
                live_versions = {_normalize_version(version) for version in versions if version not in yanked}

                for version in versions:
                    verpkg = pkg.clone(append_ident=':' + version)
                    verpkg.set_version(version, _normalize_version)

                    if version in yanked:
                        if _CVE_RE.search(yanked[version] or ''):
                            verpkg.set_flags(PackageFlags.VULNERABLE)
                        elif _normalize_version(version) not in live_versions:
                            verpkg.set_flags(PackageFlags.RECALLED)

                    sourcepath = os.path.join(moduledir, version, 'source.json')
                    if os.path.exists(sourcepath):
                        source = _read_json(sourcepath)
                        verpkg.add_links(LinkType.UPSTREAM_DOWNLOAD, source.get('url'))
                        if patches := source.get('patches'):
                            verpkg.set_extra_field('patch', sorted(patches))

                    yield verpkg
