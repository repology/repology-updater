# Copyright (C) 2024 Gavin John <gavinnjohn@gmail.com>
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

from typing import Iterable

from repology.package import LinkType
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser


class VSCMarketplaceParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        with open(path, 'r') as extdatafile:
            extension_data = json.load(extdatafile)
            raw_extensions = extension_data['extensions']

        for extension in raw_extensions:
            with factory.begin() as pkg:
                version_idx = 0
                while True:
                    for package_property in extension['versions'][version_idx]['properties']:
                        if package_property['key'] == 'Microsoft.VisualStudio.Code.PreRelease' and package_property['value'] == 'true':
                            version_idx += 1
                            continue
                    break

                pkg.add_name('vscode-extension:{publisherName}-{extensionName}'.format(publisherName=extension['publisher']['publisherName'], extensionName=extension['extensionName']), NameType.GENERIC_SRC_NAME)
                pkg.set_version(extension['versions'][version_idx]['version'])
                pkg.set_summary(extension['shortDescription'])
                pkg.add_maintainers('{publisherName}@vscmarketplace'.format(**extension['publisher']))
                pkg.add_links(LinkType.UPSTREAM_HOMEPAGE, 'https://marketplace.visualstudio.com/items?itemName={publisherName}.{extensionName}'.format(publisherName=extension['publisher']['publisherName'], extensionName=extension['extensionName']))

                for file_meta in extension['versions'][version_idx]['files']:
                    match file_meta['assetType']:
                        case 'Microsoft.VisualStudio.Services.Content.Changelog':
                            pkg.add_links(LinkType.UPSTREAM_CHANGELOG, file_meta['source'])
                        case 'Microsoft.VisualStudio.Services.Content.Details':
                            pkg.add_links(LinkType.UPSTREAM_DOCUMENTATION, file_meta['source'])
                        case 'Microsoft.VisualStudio.Services.Content.License':
                            pkg.add_licenses(file_meta['source'])

                for package_property in extension['versions'][version_idx]['properties']:
                    match package_property['key']:
                        case 'Microsoft.VisualStudio.Services.Links.Support':
                            pkg.add_links(LinkType.PACKAGE_ISSUE_TRACKER, package_property['value'])
                        case 'Microsoft.VisualStudio.Services.Links.Learn':
                            pkg.add_links(LinkType.PACKAGE_HOMEPAGE, package_property['value'])
                        case 'Microsoft.VisualStudio.Services.Links.Source':
                            pkg.add_links(LinkType.PACKAGE_SOURCES, package_property['value'])
                        case 'Microsoft.VisualStudio.Services.CustomerQnALink':
                            pkg.add_links(LinkType.UPSTREAM_DISCUSSION, package_property['value'])

                yield pkg
