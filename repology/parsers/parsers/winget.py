# Copyright (C) 2020-2021, 2023 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import os
from typing import Any, Iterable

import yaml

from repology.logger import Logger
from repology.package import LinkType
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.walk import walk_tree


_DOCUMENT_LABEL_TO_LINK_TYPE = {
    '': LinkType.UPSTREAM_DOCUMENTATION,
    'docs': LinkType.UPSTREAM_DOCUMENTATION,
    'documentation': LinkType.UPSTREAM_DOCUMENTATION,
    'guide': LinkType.UPSTREAM_DOCUMENTATION,
    'manual': LinkType.UPSTREAM_DOCUMENTATION,
    'user guide': LinkType.UPSTREAM_DOCUMENTATION,
    'wiki': LinkType.UPSTREAM_WIKI,
    # a lot of 'FAQ' as well, is it worth adding?
}


def _iter_directories(path: str) -> Iterable[str]:
    prev_dir: str | None = None

    for yamlpath in walk_tree(os.path.join(path, 'manifests'), suffix='.yaml'):
        cur_dir = os.path.dirname(yamlpath)

        if cur_dir != prev_dir:
            yield cur_dir
            prev_dir = cur_dir


def _parse_manifest(manifest_data: dict[str, Any], pkg: PackageMaker) -> None:
    if manifest_data['ManifestType'] not in ['singleton', 'installer', 'version', 'locale', 'defaultLocale']:
        pkg.log(f'Unknown ManifestType {manifest_data["ManifestType"]}', Logger.ERROR)

    if manifest_data['ManifestType'] in ['singleton', 'installer']:
        for installer in manifest_data['Installers']:
            pkg.add_links(LinkType.UPSTREAM_DOWNLOAD, installer['InstallerUrl'])

    if manifest_data['ManifestType'] in ['singleton', 'defaultLocale']:
        pkg.add_name(manifest_data['PackageIdentifier'], NameType.WINGET_ID)
        pkg.add_name(manifest_data['PackageIdentifier'].split('.', 1)[-1], NameType.WINGET_ID_NAME)
        pkg.add_name(manifest_data['PackageName'], NameType.WINGET_NAME)
        # Moniker field is optional and mostly useless

        version = manifest_data['PackageVersion']
        if isinstance(version, float):
            pkg.log(f'PackageVersion "{version}" is a floating point, should be quoted in YAML', Logger.WARNING)

        pkg.set_version(str(version))
        pkg.add_links(LinkType.UPSTREAM_HOMEPAGE, manifest_data.get('PackageUrl'))
        pkg.add_links(LinkType.UPSTREAM_CHANGELOG, manifest_data.get('ReleaseNotesUrl'))

        for documentation in manifest_data.get('Documentations', []):
            if link_type := _DOCUMENT_LABEL_TO_LINK_TYPE.get(documentation.get('DocumentLabel', '').lower()):
                pkg.add_links(link_type, documentation['DocumentUrl'])

        # pkg.set_summary(manifest_data.get('Description'))  # may be long
        # pkg.add_licenses(manifest_data['License'])  # long garbage

        pkg.add_categories(map(str, manifest_data.get('Tags', [])))


class WingetGitParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        for pkgpath_abs in _iter_directories(path):
            pkgpath_rel = os.path.relpath(pkgpath_abs, path)

            with factory.begin(pkgpath_rel) as pkg:
                manifests = [filename for filename in os.listdir(pkgpath_abs) if filename.endswith('.yaml')]

                for manifest in manifests:
                    try:
                        with open(os.path.join(pkgpath_abs, manifest), 'r') as fd:
                            manifest_data = yaml.safe_load(fd)
                    except UnicodeDecodeError:
                        pkg.log(f'failed to decode {manifest}, probably UTF-16 garbage', Logger.ERROR)
                        continue
                    except yaml.MarkedYAMLError as e:
                        if e.problem_mark:
                            pkg.log(f'YAML error in {manifest} at line {e.problem_mark.line}: {e.problem}', Logger.ERROR)
                        else:
                            pkg.log(f'YAML error in {manifest}: {e.problem}', Logger.ERROR)
                        continue

                    _parse_manifest(manifest_data, pkg)

                # skip manifests/ at the left and version directory at the right
                relevant_path = '/'.join(pkgpath_rel.split('/')[1:-1])
                pkg.add_name(relevant_path, NameType.WINGET_PATH)

                pkg.set_extra_field('path', pkgpath_rel)

                if not pkg.version:
                    raise RuntimeError('could not parse required information from all manifests')
                else:
                    yield pkg
