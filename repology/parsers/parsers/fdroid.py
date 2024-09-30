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

import xml.etree.ElementTree
from typing import Iterable

from repology.package import LinkType, PackageFlags
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser
from repology.parsers.xml import safe_findtext


class FDroidParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        root = xml.etree.ElementTree.parse(path)

        for application in root.findall('application'):
            with factory.begin() as app:
                app.add_name(safe_findtext(application, 'id'), NameType.FDROID_ID)
                # org.primftpd: name="primiti\nve ftpd"
                app.add_name(safe_findtext(application, 'name').replace('\n', ''), NameType.FDROID_NAME)
                app.add_licenses(application.findtext('license'))
                app.add_categories(safe_findtext(application, 'categories').split(','))
                app.add_links(LinkType.UPSTREAM_HOMEPAGE, application.findtext('web'))
                app.add_links(LinkType.UPSTREAM_HOMEPAGE, application.findtext('source'))
                app.add_links(LinkType.UPSTREAM_ISSUE_TRACKER, application.findtext('issues'))
                app.add_links(LinkType.UPSTREAM_CHANGELOG, application.findtext('changelog'))
                app.add_links(LinkType.UPSTREAM_DONATION, application.findtext('donate'))
                app.set_summary(application.findtext('summary'))

                upstream_version_code = int(safe_findtext(application, 'marketvercode'))
                for package in application.findall('package'):
                    version_code = int(safe_findtext(package, 'versioncode'))
                    version = package.findtext('version')

                    if version:
                        pkg = app.clone()

                        pkg.set_version(version)
                        pkg.set_flags(PackageFlags.DEVEL if version_code > upstream_version_code else 0)
                        pkg.set_extra_field('versioncode', version_code)

                        yield pkg
