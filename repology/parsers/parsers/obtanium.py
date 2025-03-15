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

import os
import json

from typing import Iterable

from repology.package import LinkType
from repology.packagemaker import NameType, PackageFactory, PackageMaker
from repology.parsers import Parser


def rewrite_id(old_id: str) -> str:
    # Android App IDs are often of the form 'com.example.appname'
    # However, most package repositories use the form example-appname
    # This function converts the former to the latter
    return old_id.replace(r'^[^.]+\.', '').replace('.', '-')


class ObtaniumJsonParser(Parser):
    def iter_parse(self, path: str, factory: PackageFactory) -> Iterable[PackageMaker]:
        appsdir = os.path.join(path, 'data', 'apps')
        for filename in os.listdir(appsdir):
            # Try to parse JSON files
            pkgdata = None
            try:
                with open(os.path.join(path, filename), 'r') as fd:
                    pkgdata = json.load(fd)
            except UnicodeDecodeError:
                continue
            except json.JSONDecodeError:
                continue

            with factory.begin() as app:
                app.add_categories(pkgdata['categories'])
                for config in pkgdata['configs']:
                    app.add_name(rewrite_id(config['id']), NameType.ANDROID_ID)
                    app.add_name(config['name'], NameType.OBTANIUM_DISPLAYNAME)
                    app.add_links(LinkType.PACKAGE_DOWNLOAD, config['url'])
                if 'description' in pkgdata:
                    if 'en' in pkgdata['description'] and pkgdata['description']['en']:
                        app.set_summary(pkgdata['description']['en'])
                    else:
                        for lang, desc in pkgdata['description'].items():
                            if desc:
                                app.set_summary(desc)
                                break
                yield app
