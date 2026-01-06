# Copyright (C) 2020-2021 Dmitry Marakasov <amdmi3@amdmi3.ru>
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


# see `jq '.[].info.project_urls' < pypicache.json` for all of them
_url_types = {
    'bug reports': LinkType.UPSTREAM_ISSUE_TRACKER,
    'bug tracker': LinkType.UPSTREAM_ISSUE_TRACKER,
    'change log': LinkType.UPSTREAM_CHANGELOG,
    'changelog': LinkType.UPSTREAM_CHANGELOG,
    'ci': LinkType.UPSTREAM_CI,
    'chat': LinkType.UPSTREAM_DISCUSSION,
    'code': LinkType.UPSTREAM_REPOSITORY,
    'coverage': LinkType.UPSTREAM_COVERAGE,
    'discord': LinkType.UPSTREAM_DISCUSSION,
    'discussions': LinkType.UPSTREAM_DISCUSSION,
    'documentation': LinkType.UPSTREAM_DOCUMENTATION,
    'docs': LinkType.UPSTREAM_DOCUMENTATION,
    'donation': LinkType.UPSTREAM_DONATION,
    'download': LinkType.UPSTREAM_DOWNLOAD,
    'forum': LinkType.UPSTREAM_DISCUSSION,
    'funding': LinkType.UPSTREAM_DONATION,
    'history': LinkType.UPSTREAM_CHANGELOG,
    'homepage': LinkType.UPSTREAM_HOMEPAGE,
    'issue tracker': LinkType.UPSTREAM_ISSUE_TRACKER,
    'issues': LinkType.UPSTREAM_ISSUE_TRACKER,
    'release notes': LinkType.UPSTREAM_CHANGELOG,
    'repository': LinkType.UPSTREAM_REPOSITORY,
    'source code': LinkType.UPSTREAM_REPOSITORY,
    'source': LinkType.UPSTREAM_REPOSITORY,
    'sources': LinkType.UPSTREAM_REPOSITORY,
    'tracker': LinkType.UPSTREAM_ISSUE_TRACKER,
    'website': LinkType.UPSTREAM_HOMEPAGE,
    'wiki': LinkType.UPSTREAM_WIKI,
}


# https://www.python.org/dev/peps/pep-0440/#pre-releases
# https://www.python.org/dev/peps/pep-0440/#pre-release-spelling
_PEP440_PRERELEASE_RE = re.compile('(a|b|rc|dev|alpha|beta|c|pre|preview)')


def _pep440_is_prerelease(version: str) -> bool:
    return _PEP440_PRERELEASE_RE.search(version.lower()) is not None


class PyPiCacheJsonParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        for pkgdata in iter_json_list(path, (None,)):
            with factory.begin() as pkg:
                info = pkgdata['info']

                pkg.add_name(info['name'], NameType.PYPI_NAME)

                pkg.add_links(LinkType.PROJECT_HOMEPAGE, info['project_url'])
                if (url := info.get('home_page')) and url != 'UNKNOWN':
                    pkg.add_links(LinkType.UPSTREAM_HOMEPAGE, url)

                if info['author_email']:
                    for maintainer in map(str.strip, info['author_email'].split(',')):
                        if ' ' in maintainer or '"' in maintainer or '<' in maintainer or "'" in maintainer or '@' not in maintainer:
                            pkg.log('Skipping garbage maintainer email "{maintainer}"', severity=Logger.WARNING)
                        else:
                            pkg.add_maintainers(maintainer)

                if info['summary']:
                    pkg.set_summary(info['summary'])

                if info['project_urls']:
                    for key, url in info['project_urls'].items():
                        if (link_type := _url_types.get(key.lower())) is not None and url != 'UNKNOWN':
                            pkg.add_links(link_type, url)

                for version, releasedatas in pkgdata['releases'].items():
                    verpkg = pkg.clone()

                    verpkg.set_version(version)

                    if _pep440_is_prerelease(version):
                        verpkg.set_flags(PackageFlags.DEVEL)

                    good_items = 0
                    yanked_items = 0
                    for releasedata in releasedatas:
                        if releasedata['yanked']:
                            yanked_items += 1
                        else:
                            good_items += 1
                            verpkg.add_links(LinkType.PROJECT_DOWNLOAD, releasedata['url'])

                    if yanked_items > 0 and good_items == 0:
                        verpkg.set_flags(PackageFlags.RECALLED)

                    yield verpkg
