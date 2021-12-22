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

import os
import xml.etree.ElementTree
from typing import Iterable

from repology.package import LinkType
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.xml import safe_findtext, safe_findtext_empty


class ChocolateyParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        atom = '{http://www.w3.org/2005/Atom}'
        ds = '{http://schemas.microsoft.com/ado/2007/08/dataservices}'
        md = '{http://schemas.microsoft.com/ado/2007/08/dataservices/metadata}'

        for pagepath in os.listdir(path):
            if not pagepath.endswith('.xml'):
                continue

            root = xml.etree.ElementTree.parse(os.path.join(path, pagepath))

            for entry in root.findall(f'{atom}entry'):
                with factory.begin() as pkg:
                    pkg.add_name(safe_findtext(entry, f'{atom}title'), NameType.CHOCOLATEY_TITLE)
                    pkg.set_version(safe_findtext(entry, f'{md}properties/{ds}Version'))
                    pkg.add_links(LinkType.UPSTREAM_HOMEPAGE, safe_findtext_empty(entry, f'{md}properties/{ds}ProjectUrl'))
                    pkg.add_links(LinkType.UPSTREAM_REPOSITORY, safe_findtext_empty(entry, f'{md}properties/{ds}ProjectSourceUrl'))
                    pkg.add_links(LinkType.PACKAGE_SOURCES, safe_findtext_empty(entry, f'{md}properties/{ds}PackageSourceUrl'))
                    pkg.add_links(LinkType.UPSTREAM_DOCUMENTATION, safe_findtext_empty(entry, f'{md}properties/{ds}DocsUrl'))
                    pkg.add_links(LinkType.UPSTREAM_ISSUE_TRACKER, safe_findtext_empty(entry, f'{md}properties/{ds}BugTrackerUrl'))
                    pkg.add_links(LinkType.UPSTREAM_DISCUSSION, safe_findtext_empty(entry, f'{md}properties/{ds}MailingListUrl'))
                    pkg.add_name(safe_findtext_empty(entry, f'{md}properties/{ds}Title'), NameType.CHOCOLATEY_METADATA_TITLE)

                    if safe_findtext(entry, f'{md}properties/{ds}IsPrerelease') == 'true':
                        pass
                        # XXX: need testing
                        #pkg.set_flags(PackageFlags.WEAK_DEVEL)

                    commentnode = entry.find(f'{atom}summary')
                    if commentnode is not None:
                        pkg.set_summary(commentnode.text)

                    yield pkg
