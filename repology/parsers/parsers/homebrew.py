# Copyright (C) 2017-2021, 2023 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from dataclasses import dataclass
from typing import Iterable

from repology.logger import Logger
from repology.package import LinkType, PackageFlags
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.json import iter_json_list


_FILE_USINGS = {
    'homebrew_curl',
    'nounzip',
}

_VCS_USINGS = {
    'bzr',
    'cvs',
    'fossil',
    'git',
    'hg',
    'svn',
}


@dataclass
class _UrlData:
    url: str
    tag: str | None = None
    revision: str | None = None
    checksum: str | None = None
    branch: str | None = None
    using: str | None = None

    # checksum presence is sufficient ATOW, howerver be stricter,
    # as there seem to be ongoing migration onto `using` field in homebrew
    # and things may break unexpectedly
    def is_file(self) -> bool:
        if self.using is not None:
            return self.using in _FILE_USINGS and self.checksum is not None
        else:
            return self.checksum is not None

    def is_vcs(self) -> bool:
        if self.using is not None:
            return self.using in _VCS_USINGS and self.checksum is None
        else:
            return self.checksum is None


class HomebrewJsonParser(Parser):
    _require_ruby_source_path: bool

    def __init__(self, require_ruby_source_path: bool = True) -> None:
        self._require_ruby_source_path = require_ruby_source_path

    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        for packagedata in iter_json_list(path, (None,)):
            with factory.begin() as pkg:
                pkg.add_name(packagedata['name'], NameType.HOMEBREW_NAME)
                pkg.add_name(packagedata['name'].split('@', 1)[0], NameType.HOMEBREW_NAME_PRE_AT)
                pkg.add_name(packagedata['full_name'], NameType.HOMEBREW_FULL_NAME)

                pkg.set_summary(packagedata['desc'])

                pkg.add_links(LinkType.UPSTREAM_HOMEPAGE, packagedata['homepage'])

                if ruby_source_path := packagedata.get('ruby_source_path'):
                    pkg.set_extra_field('ruby_source_path', ruby_source_path)
                elif self._require_ruby_source_path:
                    raise RuntimeError('required "ruby_source_path" property missing')

                for version_type, flags in [('stable', 0), ('head', PackageFlags.ROLLING)]:
                    if not packagedata['versions'].get(version_type):
                        continue
                    if not packagedata['urls'].get(version_type):
                        pkg.log(f'{version_type} version defined, but there is no corresponding urls entry', Logger.ERROR)
                        continue

                    verpkg = pkg.clone()

                    verpkg.set_version(packagedata['versions'][version_type])

                    url_data = _UrlData(**packagedata['urls'][version_type])

                    if url_data.is_file():
                        verpkg.add_links(LinkType.UPSTREAM_DOWNLOAD, url_data.url)
                    elif url_data.is_vcs():
                        verpkg.add_links(LinkType.UPSTREAM_REPOSITORY, url_data.url)
                    else:
                        raise RuntimeError(f'unexpected homebrew {version_type} url data: {url_data}')

                    verpkg.set_flags(flags)

                    yield verpkg


class HomebrewCaskJsonParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        for packagedata in iter_json_list(path, (None,)):
            with factory.begin(packagedata['token']) as pkg:
                pkg.add_name(packagedata['token'], NameType.HOMEBREW_CASK_TOKEN)
                pkg.add_name(packagedata['name'][0], NameType.HOMEBREW_CASK_FIRST_NAME)
                pkg.set_version(packagedata['version'].split(',')[0])

                pkg.set_summary(packagedata['desc'])

                pkg.add_links(LinkType.UPSTREAM_HOMEPAGE, packagedata['homepage'])
                pkg.add_links(LinkType.UPSTREAM_DOWNLOAD, packagedata['url'])

                pkg.set_extra_field('ruby_source_path', packagedata['ruby_source_path'])

                yield pkg
