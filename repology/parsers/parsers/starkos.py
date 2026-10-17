# Copyright (C) 2026 starkOS GNU/Linux
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

import re
from typing import Iterable

from repology.logger import Logger
from repology.package import LinkType, PackageFlags
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.json import iter_json_list
from repology.parsers.maintainers import extract_maintainers

_URL_RE = re.compile('https?://[^\\s]+')
_ROLLING_VERSIONS = {'git', 'svn', 'hg', 'next', 'master', 'main', 'head', 'trunk'}
_COMMIT_HASH_RE = re.compile('[0-9a-f]{7,40}')
# prebuilt kernels (linux-bin, linux-lts-bin, linux-libre-bin, ...) are built
# for and specific to starkOS, they must not be matched with the Linux kernel
_DISTRO_KERNEL_RE = re.compile('linux(-[a-z0-9]+)*-bin')


def _is_rolling(version: str) -> bool:
    # no upstream release behind these: bare VCS markers or commit hashes
    if version.lower() in _ROLLING_VERSIONS:
        return True
    return bool(_COMMIT_HASH_RE.fullmatch(version)) and bool(re.search('[a-f]', version))


class StarkosJsonParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        for pkgdata in iter_json_list(path, (None,)):
            name = pkgdata['name'].strip()
            repo = pkgdata['repo'].strip()
            version = pkgdata['version'].strip()

            # init scripts for the s6 service manager, these are starkOS
            # specific glue (name-s6 -> service files for name), not
            # packages of an upstream project
            if repo == 's6' and name.endswith('-s6'):
                continue

            if _DISTRO_KERNEL_RE.fullmatch(name):
                continue

            with factory.begin(f'{repo}/{name}') as pkg:
                pkg.add_name(name, NameType.GENERIC_SRC_NAME)
                pkg.set_subrepo(repo)
                pkg.set_version(version)

                # keep the distro revision visible as a raw version
                if release := str(pkgdata.get('release', '')).strip():
                    pkg.set_rawversion(f'{version}-{release}')

                if _is_rolling(version):
                    pkg.set_flags(PackageFlags.ROLLING)

                if summary := pkgdata.get('description', '').strip():
                    pkg.set_summary(summary)

                # homepage is the only upstream link, so it must be a real URL;
                # do not try to repair broken values, report them instead
                homepage = (pkgdata.get('homepage') or '').strip()
                if _URL_RE.fullmatch(homepage):
                    pkg.add_homepages(homepage)
                elif homepage:
                    pkg.log(f'ignoring invalid homepage "{homepage}"', severity=Logger.WARNING)

                if recipe_url := pkgdata.get('recipe_url'):
                    pkg.add_links(LinkType.PACKAGE_RECIPE, recipe_url)

                # "Team name, address@domain" -> address@domain; packages with an
                # empty maintainer fall back to default_maintainer from repos.d
                pkg.add_maintainers(extract_maintainers(pkgdata.get('maintainer')))

                yield pkg
