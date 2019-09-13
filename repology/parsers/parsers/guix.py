# Copyright (C) 2016-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
from repology.package import PackageFlags
from repology.packagemaker import PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.json import iter_json_list
from repology.transformer import PackageTransformer


class GuixJsonParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory, transformer: PackageTransformer) -> Iterable[PackageMaker]:
        for pkgdata in iter_json_list(path, (None,)):
            with factory.begin() as pkg:
                pkg.set_name(pkgdata['name'])
                pkg.set_version(pkgdata['version'])
                pkg.set_summary(pkgdata['synopsis'])
                pkg.add_homepages(pkgdata.get('homepage'))

                path, lineno = pkgdata['location'].split(':')
                pkg.set_extra_field('loc_path', path)
                pkg.set_extra_field('loc_line', lineno)

                if 'source' in pkgdata:
                    source = pkgdata['source']

                    if source['type'] == 'url':
                        pkg.add_downloads(source['url'])
                        if re.fullmatch('.*-[0-9]+\\.[0-9a-f]{4,}', pkgdata['version']):
                            # snapshot pattern with plain url
                            pkg.set_flags(PackageFlags.IGNORE)  # e.g. snapshot
                    elif source['type'] == 'svn':
                        pkg.add_downloads(source['svn_url'])

                        if str(source['svn_revision']) in re.split('[._-]', pkgdata['version']):
                            # svn revision in version
                            pkg.set_flags(PackageFlags.IGNORE)  # e.g. snapshot
                    elif source['type'] == 'git':
                        pkg.add_downloads(source['git_url'])

                        if re.fullmatch('[0-9a-f]{7,}', source['git_ref']) and not re.fullmatch('[0-9]{8}', source['git_ref']):
                            # ref is a commit hash, not a tag
                            if len(source['git_ref']) != 40:
                                pkg.log('treating git_ref as trimmed commit hash: {}'.format(source['git_ref']), Logger.WARNING)

                            match = re.fullmatch('(.*)-[0-9]+\\.([0-9a-f]{7,})', pkgdata['version'])
                            if match is not None and source['git_ref'].startswith(match.group(2)):
                                # commit hash in version, allowed pattern documented in
                                # https://guix.gnu.org/manual/en/html_node/Version-Numbers.html
                                pkg.set_flags(PackageFlags.IGNORE)  # e.g. snapshot
                            elif source['git_ref'][:7] in pkgdata['version']:
                                # git commit in version and not a known pattern
                                pkg.set_flags(PackageFlags.INCORRECT)
                    else:  # type == 'none'
                        if re.fullmatch('.*-[0-9]+\\.[0-9a-f]{4,}', pkgdata['version']):
                            # snapshot pattern anyway
                            pkg.set_flags(PackageFlags.IGNORE)  # e.g. snapshot

                yield pkg
